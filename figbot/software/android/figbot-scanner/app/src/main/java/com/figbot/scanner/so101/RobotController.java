package com.figbot.scanner.so101;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.function.LongSupplier;

/** Single-worker feedback controller. No camera interpretation or object-success claims.
 * The caller continues tick() while STOPPING, including after a reported fault.
 * requestStop() is the only method intended for a different/UI thread.
 */
public final class RobotController {
    public enum State { DISARMED, HOLDING, MOVING, STOPPING, FAULT_HOLD, FAULT_UNKNOWN }
    public record Result(double wallElapsedSeconds, double trajectorySeconds,
                         int maxTrackingError, double maxGapSeconds,
                         long releaseStartNanos, long releaseCompleteNanos,
                         int[] finalPositions) {
        public Result { finalPositions = finalPositions.clone(); }
        @Override public int[] finalPositions() { return finalPositions.clone(); }
    }

    private final ServoBus bus;
    private final LongSupplier clock;
    private ArmProfile profile, connectedProfile;
    private volatile Map<Integer, St3215Protocol.FeedbackState> rows = Collections.emptyMap();
    private volatile State state = State.DISARMED;
    private volatile boolean stopRequested;
    private volatile String message = "Disconnected; no torque state assumed";
    private int[] targets, stopTargets;
    private long lastReadNs, startedNs, lastTickNs, deadlineNs, stopDeadlineNs, stopStableSince;
    private long pickupWaitNs, approachWaitNs, releaseWaitNs, releaseStartNs, releaseCompleteNs;
    private double phase, maxGap;
    private int maxTracking;
    private boolean connected, pickupConfirmed, releaseConfirmed, faultStop, validatingHold;
    private GoalTrajectory trajectory;
    private volatile Result lastResult;
    private String telemetryNote="";
    private String faultReason="";
    private GraspContact graspContact;
    private static final int GRASP_START_BODY_TOLERANCE_COUNTS=3;
    private int[] graspBodyHold;
    /** Neither completion nor a current/stall candidate proves an object was picked up. */
    public enum GraspOutcome { NONE, CONTACT_POSSIBLE, CLOSED_UNVERIFIED }
    private GraspOutcome graspOutcome=GraspOutcome.NONE;
    public GraspOutcome graspOutcome(){return graspOutcome;}
    public int heldJawTarget(){return targets[5];}
    public String faultReason(){return faultReason;}
    public String telemetryNote(){return telemetryNote;}

    public RobotController(ServoBus bus, ArmProfile profile, LongSupplier nanoClock) {
        this.bus = Objects.requireNonNull(bus);
        this.profile = Objects.requireNonNull(profile);
        this.clock = Objects.requireNonNull(nanoClock);
    }
    public State state() { return state; }
    public String message() { return message; }
    public Result lastResult() { return lastResult; }
    public double trajectoryTimeSeconds() { return trajectory == null ? 0 : phase; }
    public int[] positions() {
        Map<Integer,St3215Protocol.FeedbackState> snapshot=rows;
        if (snapshot.size() != 6) throw new IllegalStateException("No complete feedback yet");
        int[] result = new int[6];
        for (int i=1;i<=6;i++) result[i-1] = snapshot.get(i).position();
        return result;
    }
    public Map<Integer, St3215Protocol.FeedbackState> feedback() {
        return Collections.unmodifiableMap(new LinkedHashMap<>(rows));
    }

    public void setProfile(ArmProfile replacement) {
        Objects.requireNonNull(replacement);
        if (state != State.DISARMED && state != State.HOLDING) throw new IllegalStateException("Profile can change only while idle");
        if (connectedProfile != null && (!Arrays.equals(connectedProfile.offsets(), replacement.offsets()) ||
                !Arrays.equals(connectedProfile.referenceRaw(), replacement.referenceRaw()) ||
                !Arrays.equals(connectedProfile.referenceRadians(), replacement.referenceRadians()) ||
                !Arrays.equals(connectedProfile.directionSigns(), replacement.directionSigns())))
            throw new IllegalArgumentException("Connected encoder identity/reference cannot change");
        profile = replacement;
    }

    /** Inspects identity, offsets, factory acceleration and feedback; never writes. */
    public void connectReadOnly() throws IOException {
        requireState(State.DISARMED);
        connected = false;
        inspectConfiguration();
        readAll();
        connectedProfile = profile;
        connected = true;
        message = "Six ST3215 devices inspected without changing torque";
    }

    public void attachExistingHold() throws IOException {
        requireState(State.DISARMED);
        requireConnected();
        inspectConfiguration();
        readAll();
        requireStationary(true);
        for (int id=1;id<=6;id++) {
            int goal = St3215Protocol.word(bus.read(id,42,2),0);
            if (Math.abs(goal-rows.get(id).position()) > 20) throw new IOException("ID"+id+" existing goal is not the held position");
        }
        targets = positions();
        state = State.HOLDING;
        stopRequested = false;
        message = "Existing stationary hold adopted without writes";
    }

    /** Explicit acknowledgement only; no writes and no recovery from unknown torque/stop state. */
    public void acknowledgeHeldFault() throws IOException {
        requireState(State.FAULT_HOLD);requireConnected();inspectConfiguration();readAll();requireStationary(true);
        int[] first=positions();readAll();requireStationary(true);
        for(int id=1;id<=6;id++)if(Math.abs(first[id-1]-positions()[id-1])>3
                ||Math.abs(St3215Protocol.word(bus.read(id,42,2),0)-positions()[id-1])>12)
            throw new IOException("Fault recovery requires unchanged measured hold");
        targets=positions();stopRequested=false;faultStop=false;graspContact=null;graspOutcome=GraspOutcome.NONE;
        state=State.HOLDING;message="Fault acknowledged; current hold checked, no motion started";
    }

    public void startGrasp(GoalTrajectory closing) throws IOException {
        Objects.requireNonNull(closing);
        int[] first=closing.sample(0),end=closing.end();
        for(int i=0;i<5;i++)if(first[i]!=end[i])throw new IOException("Grasp may move only the jaw");
        if(end[5]>=first[5])throw new IOException("Grasp requires closing direction");
        start(closing,true);graspContact=new GraspContact(rows.get(6).currentRaw());graspOutcome=GraspOutcome.NONE;
    }

    /** Explicit supported-pose operation. Enables only currently disabled joints. */
    public void holdSupportedPose() throws IOException {
        requireState(State.DISARMED);
        requireConnected();
        inspectConfiguration();
        readAll(); requireStationary(false);
        requireSupportedStationary();
        int[] first = positions();
        int[] oldTorque = new int[6];
        for (int id=1;id<=6;id++) {
            oldTorque[id-1] = rows.get(id).torque();
            if (oldTorque[id-1] == 1 && Math.abs(St3215Protocol.word(bus.read(id,42,2),0)-first[id-1]) > 20)
                throw new IOException("Enabled ID"+id+" has a distant goal");
        }
        readAll(); requireStationary(false);
        requireSupportedStationary();
        for (int id=1;id<=6;id++)
            if (Math.abs(rows.get(id).position()-first[id-1]) > 8 || rows.get(id).torque() != oldTorque[id-1])
                throw new IOException("Supported pose changed before activation");
        targets = positions();
        try {
            for (int id=1;id<=6;id++) if (oldTorque[id-1] == 0) {
                St3215Protocol.FeedbackState fresh = St3215Protocol.readFeedback(bus,id);
                validateHealth(id,fresh);
                if (Math.abs(fresh.position()-targets[id-1]) > 8 || fresh.speed()!=0 || fresh.moving() || fresh.torque()!=0)
                    throw new IOException("Disabled joint moved before activation");
                byte[] goal = profileBytes(targets[id-1],57,1);
                bus.write(id,41,goal);
                verifyBytes(id,41,goal);
                int torque = bus.read(id,40,1)[0]&255;
                if (torque == 0) bus.write(id,40,new byte[]{1});
                verifyBytes(id,40,new byte[]{1});
            }
            readAll(); requireStationary(true);
            stopTargets = targets.clone();
            validatingHold = true; faultStop = false; stopStableSince=0;
            stopDeadlineNs = clock.getAsLong()+800_000_000L;
            state = State.STOPPING;
            message = "Same-pose hold enabled; checking stability for 0.8 seconds";
        } catch (IOException | RuntimeException error) {
            state = State.FAULT_UNKNOWN;
            message = "Hold activation unconfirmed; maintain physical support: "+error.getMessage();
            throw error;
        }
    }

    /** Explicit user-supported release; never called from pause or camera loss. */
    public void releaseSupported() throws IOException {
        if (state == State.MOVING || state == State.STOPPING) throw new IOException("Stop movement before supported release");
        requireConnected(); inspectConfiguration(); readAll(); requireStationary(false);
        IOException failure = null;
        for (int id=1;id<=6;id++) {
            try {
                if (rows.get(id).torque() != 0) bus.write(id,40,new byte[]{0});
                verifyBytes(id,40,new byte[]{0});
            } catch (IOException error) { if (failure == null) failure=error; else failure.addSuppressed(error); }
        }
        trajectory = null; validatingHold = false; stopRequested = false;
        if (failure != null) {state=State.FAULT_UNKNOWN;message="Supported release not fully confirmed";throw failure;}
        state = State.DISARMED;message="Torque disabled by explicit supported release";
    }

    public void start(GoalTrajectory next) throws IOException {
        start(next,false);
    }

    private void start(GoalTrajectory next,boolean jawOnly) throws IOException {
        requireState(State.HOLDING);requireConnected();Objects.requireNonNull(next);
        if (!profile.physicalCalibrationVerified()) throw new IOException("Measured physical calibration is required before travel");
        if (stopRequested) throw new IOException("Stop is pending");
        inspectConfiguration(); readAll(); requireStationary(true);
        int[] actual = positions(), first = next.sample(0), end = next.sample(next.duration());
        profile.validatePose(first);profile.validatePose(end);
        if(jawOnly)profile.validatePose(actual);
        if(jawOnly && end[5]>=actual[5])throw new IOException("Measured jaw is already at or beyond the closing target");
        for (int i=0;i<6;i++) {
            if (Math.abs(first[i]-actual[i])>20 || Math.abs(targets[i]-actual[i])>32)
                throw new IOException("Trajectory does not start at current held pose");
            if (i==4 && (first[i]!=end[i] || Math.abs(first[i]-actual[i])>8))
                throw new IOException("Wrist roll must remain passive");
            if(jawOnly && i<5 && Math.abs(first[i]-actual[i])>GRASP_START_BODY_TOLERANCE_COUNTS)
                throw new IOException("Grasp body changed before closure; fresh alignment is required");
        }
        // A trajectory may have been created with another profile. Validate its
        // entire bounded duration against this connection before the first write.
        if (!Double.isFinite(next.duration()) || next.duration()<=0 || next.duration()>50)
            throw new IOException("Invalid trajectory duration");
        if (!Double.isFinite(next.maxSpeed()) || !Double.isFinite(next.maxAcceleration()) ||
                next.maxSpeed()>profile.speedLimit()+1e-6 || next.maxAcceleration()>profile.accelerationLimit()*100.0+1e-5)
            throw new IOException("Trajectory exceeds the connected profile speed/acceleration limits");
        for (double t=0;t<=next.duration()+.01;t+=.01) {
            int[] q=next.sample(Math.min(t,next.duration()));profile.validatePose(q);
            if (q[4]!=first[4]) throw new IOException("Trajectory changes passive wrist roll");
            if(jawOnly)for(int i=0;i<5;i++)if(q[i]!=first[i])throw new IOException("Grasp may move only the jaw");
        }
        // Even accepted encoder quantization must not become a body correction
        // while the fingers close. Freeze all body targets at this fresh reading.
        graspBodyHold=jawOnly?actual.clone():null;
        graspContact=null;targets=actual.clone();trajectory=next;phase=0;maxGap=0;maxTracking=0;
        pickupConfirmed=!Double.isFinite(next.pickupTime());releaseConfirmed=!Double.isFinite(next.releaseStart());
        pickupWaitNs=approachWaitNs=releaseWaitNs=releaseStartNs=releaseCompleteNs=0;
        validatingHold=false;lastResult=null;
        try {
            Map<Integer,int[]> profiles=new LinkedHashMap<>();
            for(int id=1;id<=6;id++) if(id!=5) profiles.put(id,new int[]{actual[id-1],3400,profile.accelerationLimit()});
            bus.syncProfiles(profiles);
            for(int id:profiles.keySet()) verifyBytes(id,41,profileBytes(actual[id-1],3400,profile.accelerationLimit()));
            startedNs=lastTickNs=clock.getAsLong();deadlineNs=startedNs+(long)((next.duration()+1.5)*1e9);
            state=State.MOVING;message="Concurrent goal trajectory running";
        } catch(IOException | RuntimeException error) {
            latchFault(error);throw error;
        }
    }

    /** Thread-safe intent only. The single worker performs a bounded hold stop. */
    public void requestStop() { stopRequested=true; }

    public void tick(boolean cameraFresh) throws IOException {
        if (!connected) return;
        try {
            readAll();
            if (stopRequested) {
                stopRequested=false;
                if(state==State.MOVING) beginStop(false,"Stop requested");
            }
            if(state==State.STOPPING) {checkStop();return;}
            if(state==State.HOLDING || state==State.FAULT_HOLD) {
                for(int id=1;id<=6;id++) if(rows.get(id).torque()!=1 ||
                        Math.abs(rows.get(id).position()-targets[id-1])>32 || Math.abs(rows.get(id).speed())>100)
                    throw new IOException("ID"+id+" held pose drifted: target="+targets[id-1]+" actual="+rows.get(id));
                return;
            }
            if(state!=State.MOVING) return;
            if(!cameraFresh) throw new IOException("Camera observations are stale");
            long now=clock.getAsLong();double gap=(now-lastTickNs)/1e9;
            if(gap<0 || gap>.25) throw new IOException("Servo worker missed its bounded update interval");
            if(now>deadlineNs) throw new IOException("Trajectory finite deadline exceeded");
            if(graspContact!=null){
                St3215Protocol.FeedbackState jaw=rows.get(6);
                if(graspContact.observe(now,jaw.position(),targets[5],jaw.speed(),jaw.currentRaw())){
                    graspOutcome=GraspOutcome.CONTACT_POSSIBLE;
                    beginStop(false,"Sustained jaw contact candidate",6);return;
                }
            }
            maxGap=Math.max(maxGap,gap);
            phase+=gap>.08?Math.min(gap,.04):gap;
            lastTickNs=now;
            double cap=trajectory.duration();
            if(!pickupConfirmed) {
                cap=Math.min(cap,trajectory.pickupTime());
                if(phase>=trajectory.pickupTime()) {
                    int closed=trajectory.sample(trajectory.pickupTime())[5];
                    if(Math.abs(rows.get(6).position()-closed)<=20) pickupConfirmed=true;
                    else {if(pickupWaitNs==0)pickupWaitNs=now;phase=Math.min(phase,trajectory.pickupTime());
                        if(now-pickupWaitNs>200_000_000L)throw new IOException("Pickup jaw closure was not confirmed");}
                }
                if(pickupConfirmed)cap=trajectory.duration();
            }
            if(!releaseConfirmed) {
                int[] basket=trajectory.sample(trajectory.basketArrival());
                if(phase>=trajectory.releaseStart() && releaseStartNs==0) {
                    if(nearBasket(basket,64,true)) releaseStartNs=now;
                    else {
                        if(approachWaitNs==0)approachWaitNs=now;
                        phase=Math.min(phase,trajectory.basketArrival());
                        if(now-approachWaitNs>750_000_000L)throw new IOException("Measured release approach not confirmed");
                    }
                }
                cap=Math.min(cap,releaseStartNs==0?trajectory.basketArrival():trajectory.releaseEnd());
                if(phase>=trajectory.releaseEnd()) {
                    int open=trajectory.sample(trajectory.releaseEnd())[5];
                    if(releaseStartNs!=0 && nearBasket(basket,22,false) && Math.abs(rows.get(6).position()-open)<=20) {
                        releaseConfirmed=true;releaseCompleteNs=now;cap=trajectory.duration();
                    } else {
                        if(releaseWaitNs==0)releaseWaitNs=now;phase=Math.min(phase,trajectory.releaseEnd());
                        if(now-releaseWaitNs>750_000_000L)throw new IOException("Basket/open-jaw motor pose not confirmed");
                    }
                }
            }
            phase=Math.min(phase,trajectory.duration());
            int[] expected=runtimeSample(phase,now,0,cap);
            for(int id=1;id<=6;id++) {
                St3215Protocol.FeedbackState f=rows.get(id);int[] bounds=profile.envelopes()[id-1];
                if(f.torque()!=1 || f.position()<bounds[0]-32 || f.position()>bounds[1]+32)
                    throw new IOException("ID"+id+" torque/range lost");
                int error=Math.abs(f.position()-expected[id-1]);maxTracking=Math.max(maxTracking,error);
                if(error>(id==5?32:192))throw new IOException("ID"+id+" trajectory following error "+error);
            }
            int[] goal=null;
            for(double lead:new double[]{.1,.075,.05,.025,0}) {
                int[] candidate=runtimeSample(phase,now,lead,cap);boolean nearby=true;
                for(int id=1;id<=6;id++) if(id!=5 && Math.abs(candidate[id-1]-rows.get(id).position())>192)nearby=false;
                if(nearby){goal=candidate;break;}
            }
            if(goal==null)throw new IOException("No finite nearby servo target");
            Map<Integer,Integer> changes=new LinkedHashMap<>();
            for(int id=1;id<=6;id++)if(id!=5 && goal[id-1]!=targets[id-1])changes.put(id,goal[id-1]);
            if(!changes.isEmpty()) {
                bus.syncPositions(changes);
                for(Map.Entry<Integer,Integer> e:changes.entrySet())verifyBytes(e.getKey(),42,St3215Protocol.leWord(e.getValue()));
                targets=goal.clone();
            }
            int[] finalHold=runtimeSample(trajectory.duration(),now,0,trajectory.duration());
            if(phase>=trajectory.duration() && settled(finalHold,20,50)) {
                if(graspContact!=null){graspOutcome=GraspOutcome.CLOSED_UNVERIFIED;graspContact=null;}
                lastResult=new Result((now-startedNs)/1e9,phase,maxTracking,maxGap,releaseStartNs,releaseCompleteNs,positions());
                targets=finalHold;trajectory=null;graspBodyHold=null;state=State.HOLDING;message="Motor trajectory completed and final hold verified";
            }
        } catch(IOException | RuntimeException error) {
            latchFault(error);throw error;
        }
    }

    private int[] runtimeSample(double seconds,long now,double lead,double cap) {
        int[] result=trajectory.sample(Math.min(seconds+lead,cap));
        if(graspBodyHold!=null)System.arraycopy(graspBodyHold,0,result,0,5);
        if(Double.isFinite(trajectory.releaseStart()) && !releaseConfirmed && seconds<=trajectory.releaseEnd()) {
            if(seconds+lead>=trajectory.releaseStart()) {
                int closed=trajectory.sample(trajectory.releaseStart())[5];
                int open=trajectory.sample(trajectory.releaseEnd())[5];
                double u=releaseStartNs==0?0:Math.max(0,Math.min(1,((now-releaseStartNs)/1e9+lead)/(trajectory.releaseEnd()-trajectory.releaseStart())));
                double s=10*u*u*u-15*u*u*u*u+6*u*u*u*u*u;
                result[5]=(int)Math.round(closed+(open-closed)*s);
            }
        }
        return result;
    }

    private boolean nearBasket(int[] basket,int tolerance,boolean checkDirection) {
        for(int id=1;id<=5;id++) {
            St3215Protocol.FeedbackState f=rows.get(id);int delta=basket[id-1]-f.position();
            if(Math.abs(delta)>(id==5?22:tolerance))return false;
            if(checkDirection && Math.abs(delta)>22 && f.speed()*Integer.signum(delta)<-50)return false;
        }
        return true;
    }

    private void beginStop(boolean fault,String reason) throws IOException {
        beginStop(fault,reason,0);
    }
    private void beginStop(boolean fault,String reason,int jawPreload) throws IOException {
        graspContact=null;
        graspBodyHold=null;
        trajectory=null;validatingHold=false;faultStop=fault;stopStableSince=0;
        if(rows.size()!=6 || clock.getAsLong()-lastReadNs>100_000_000L) {
            state=State.FAULT_UNKNOWN;message="No fresh feedback for a confirmed stop: "+reason;return;
        }
        stopTargets=positions();
        stopTargets[5]=Math.max(profile.envelopes()[5][0],stopTargets[5]-jawPreload);
        targets=stopTargets.clone();
        Map<Integer,int[]> profiles=new LinkedHashMap<>();int maxSpeed=0;
        for(int id=1;id<=6;id++) {
            maxSpeed=Math.max(maxSpeed,Math.abs(rows.get(id).speed()));
            if(id!=5 && rows.get(id).torque()==1) profiles.put(id,new int[]{stopTargets[id-1],3400,profile.accelerationLimit()});
        }
        state=State.STOPPING;
        // Capturing the present position while moving requires braking past it
        // and returning. A braking-only deadline falsely rejects that return.
        double allowance=maxSpeed<=50?.35:Math.max(.35,Math.min(.9,
                .30+(1+Math.sqrt(2))*maxSpeed/(profile.accelerationLimit()*100.0)));
        stopDeadlineNs=clock.getAsLong()+(long)(allowance*1e9);
        if(!profiles.isEmpty()) {
            bus.syncProfiles(profiles);
            for(int id:profiles.keySet())verifyBytes(id,41,profileBytes(stopTargets[id-1],3400,profile.accelerationLimit()));
        }
        message="Stop requested; actual hold still being verified: "+reason;
    }

    private void checkStop() throws IOException {
        for(int id=1;id<=6;id++) {
            St3215Protocol.FeedbackState f=rows.get(id);
            if(f.torque()!=1 || Math.abs(f.position()-stopTargets[id-1])>(validatingHold?12:192)) {
                state=State.FAULT_UNKNOWN;message="Stop/hold not confirmed; torque has not been automatically released";
                throw new IOException(message);
            }
        }
        long now=clock.getAsLong();
        boolean stationary=settled(stopTargets,12,50);
        if(stationary){if(stopStableSince==0)stopStableSince=now;}else stopStableSince=0;
        // One in-range packet during braking is not a settled hold. Require a
        // continuous encoder/speed interval before allowing another leg.
        if((!validatingHold || now>=stopDeadlineNs) && stationary && now-stopStableSince>=100_000_000L) {
            state=faultStop?State.FAULT_HOLD:State.HOLDING;validatingHold=false;
            message=faultStop?"Fault latched; stationary hold verified: "+faultReason:"Stationary hold verified";
        } else if(now>stopDeadlineNs && !(stationary&&stopStableSince>0
                &&stopStableSince<=stopDeadlineNs&&now<=stopDeadlineNs+100_000_000L)) {
            state=State.FAULT_UNKNOWN;message="Stop deadline exceeded; physical stopping is unconfirmed";
            throw new IOException(message);
        }
    }

    private void latchFault(Exception error) {
        if(faultReason.isEmpty()||state!=State.FAULT_HOLD&&state!=State.FAULT_UNKNOWN&&state!=State.STOPPING)faultReason=error.getMessage();
        if(state==State.FAULT_UNKNOWN)return;
        try {
            if(state==State.MOVING || state==State.HOLDING || state==State.FAULT_HOLD)beginStop(true,error.getMessage());
            else if(state==State.STOPPING) {state=State.FAULT_UNKNOWN;message="Stop feedback failed: "+error.getMessage();}
            else message=error.getMessage();
        } catch(IOException | RuntimeException stopError) {
            state=State.FAULT_UNKNOWN;message="Stop command/feedback unconfirmed: "+stopError.getMessage();error.addSuppressed(stopError);
        }
    }

    private boolean settled(int[] pose,int positionTolerance,int speedTolerance) {
        for(int id=1;id<=6;id++) {
            St3215Protocol.FeedbackState f=rows.get(id);
            if(f.torque()!=1 || Math.abs(f.position()-pose[id-1])>positionTolerance || Math.abs(f.speed())>speedTolerance || f.moving())return false;
        }
        return true;
    }
    private void requireConnected() throws IOException {if(!connected)throw new IOException("Read-only connection inspection required");}
    private void requireState(State expected) throws IOException {if(state!=expected)throw new IOException("Expected "+expected+", found "+state);}
    private void requireStationary(boolean torqueEnabled) throws IOException {
        for(Map.Entry<Integer,St3215Protocol.FeedbackState> e:rows.entrySet()) {
            St3215Protocol.FeedbackState f=e.getValue();
            if(Math.abs(f.speed())>50 || f.moving() || (torqueEnabled && f.torque()!=1))
                throw new IOException("ID"+e.getKey()+" is not stationary");
        }
    }
    private void requireSupportedStationary() throws IOException {
        for(St3215Protocol.FeedbackState f:rows.values())
            if(f.speed()!=0 || f.moving())throw new IOException("Supported activation requires two stationary snapshots");
    }
    private void inspectConfiguration() throws IOException {
        int[] offsets=profile.offsets();
        for(int id=1;id<=6;id++) {
            if(St3215Protocol.word(bus.read(id,3,2),0)!=777 || (bus.read(id,33,1)[0]&255)!=0)
                throw new IOException("ID"+id+" model or position mode mismatch");
            if(St3215Protocol.word(bus.read(id,31,2),0)!=offsets[id-1])throw new IOException("ID"+id+" offset mismatch");
            int acceleration=bus.read(id,85,1)[0]&255;
            if(acceleration!=profile.accelerationLimit() || acceleration>50 || acceleration<1)
                throw new IOException("ID"+id+" factory acceleration mismatch");
        }
    }
    private void readAll() throws IOException {
        LinkedHashMap<Integer,St3215Protocol.FeedbackState> fresh=new LinkedHashMap<>();
        // Incomplete reads must never be mistaken for a fresh whole-arm snapshot.
        lastReadNs=Long.MIN_VALUE/2;
        for(int id=1;id<=6;id++){
            St3215Protocol.FeedbackState value=St3215Protocol.readFeedback(bus,id);
            // Confirm every high block reading independently, including a first read
            // or a delayed poll. Old cached temperatures are never used as evidence.
            if(value.temperature()>=55){
                int first=bus.read(id,63,1)[0]&255;
                int second=bus.read(id,63,1)[0]&255;
                St3215Protocol.FeedbackState confirmed=St3215Protocol.readFeedback(bus,id);
                int third=bus.read(id,63,1)[0]&255;
                telemetryNote="ID"+id+" block temperatures="+value.temperature()+","+confirmed.temperature()
                        +" confirmed="+first+","+second+","+third;
                // A cold but inconsistent first register sample needs more evidence,
                // not a wider threshold. At most three additional reads; an outlier
                // in the third initial slot also needs three subsequent readings.
                // Any hot direct
                // reading preserves the fault, and the last three must still agree.
                for(int extra=0;extra<3&&first<55&&second<55&&third<55
                        &&Math.max(first,Math.max(second,third))-Math.min(first,Math.min(second,third))>2;extra++){
                    first=second;second=third;third=bus.read(id,63,1)[0]&255;
                    telemetryNote+=","+third;
                }
                if(first<55&&second<55&&third<55
                        &&Math.max(first,Math.max(second,third))-Math.min(first,Math.min(second,third))<=2){
                    // The last temperature-only read is newer than the complete block.
                    // Keep all other freshly read fields and their existing health checks.
                    value=new St3215Protocol.FeedbackState(confirmed.torque(),confirmed.position(),confirmed.speed(),
                            confirmed.voltage(),third,confirmed.currentRaw(),confirmed.moving());
                }
            }
            fresh.put(id,value);
        }
        rows=Collections.unmodifiableMap(fresh);lastReadNs=clock.getAsLong();
        for(Map.Entry<Integer,St3215Protocol.FeedbackState> e:rows.entrySet())validateHealth(e.getKey(),e.getValue());
    }
    private static void validateHealth(int id,St3215Protocol.FeedbackState f) throws IOException {
        if(f.position()<0 || f.position()>4095 || !Double.isFinite(f.voltage()) || f.voltage()<10 || f.voltage()>12.6 ||
                f.temperature()>=55 || Math.abs(f.currentRaw())>150 || (f.torque()!=0 && f.torque()!=1))
            throw new IOException("ID"+id+" health feedback outside verified bounds: "+f);
    }
    private void verifyBytes(int id,int address,byte[] expected) throws IOException {
        if(!Arrays.equals(expected,bus.read(id,address,expected.length)))throw new IOException("ID"+id+" register readback mismatch at "+address);
    }
    private static byte[] profileBytes(int position,int speed,int acceleration) {
        return new byte[]{(byte)acceleration,(byte)position,(byte)(position>>8),0,0,(byte)speed,(byte)(speed>>8)};
    }
}
