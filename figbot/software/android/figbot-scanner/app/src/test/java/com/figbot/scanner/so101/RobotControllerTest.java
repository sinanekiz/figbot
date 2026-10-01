package com.figbot.scanner.so101;

import org.junit.Test;
import static org.junit.Assert.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicLong;

public final class RobotControllerTest {
    static final class FakeBus implements ServoBus {
        final byte[][] registers=new byte[7][256];
        final List<String> writes=new ArrayList<>();
        final List<Map<Integer,Integer>> streams=new ArrayList<>();
        boolean failFeedback, failWrite, wrongReadback;
        int temperatureSpikes,temperatureOnlySpikes,spikeTemperature=62,temperatureOnlySpikeValue=62;
        final java.util.ArrayDeque<Integer> directTemperatures=new java.util.ArrayDeque<>();
        FakeBus(ArmProfile p) {
            for(int id=1;id<=6;id++) {
                put(id,3,777);put(id,31,p.offsets()[id-1]);registers[id][33]=0;
                registers[id][40]=1;registers[id][41]=50;registers[id][85]=50;
                put(id,42,p.home()[id-1]);put(id,46,3400);position(id,p.home()[id-1]);
                registers[id][62]=122;registers[id][63]=35;
            }
        }
        void put(int id,int address,int value) {registers[id][address]=(byte)value;registers[id][address+1]=(byte)(value>>8);}
        void position(int id,int value) {put(id,56,value);}
        int position(int id){return St3215Protocol.word(registers[id],56);}
        int goal(int id){return St3215Protocol.word(registers[id],42);}
        void speed(int id,int value){put(id,58,value<0?(-value)|0x8000:value);}
        void follow(){for(int id=1;id<=6;id++){position(id,goal(id));speed(id,0);registers[id][66]=0;}}
        @Override public byte[] read(int id,int address,int length)throws IOException {
            if(failFeedback && address==40 && length==31)throw new IOException("feedback missing");
            byte[] result=Arrays.copyOfRange(registers[id],address,address+length);
            if(id==4&&address==40&&length==31&&temperatureSpikes>0){temperatureSpikes--;result[23]=(byte)spikeTemperature;}
            if(id==4&&address==63&&length==1&&temperatureOnlySpikes>0){temperatureOnlySpikes--;result[0]=(byte)temperatureOnlySpikeValue;}
            if(id==4&&address==63&&length==1&&!directTemperatures.isEmpty())result[0]=directTemperatures.removeFirst().byteValue();
            if(wrongReadback && address==42)result[0]++;
            return result;
        }
        @Override public void write(int id,int address,byte[] data)throws IOException {
            writes.add("write:"+id+":"+address+":"+(data[0]&255));
            if(failWrite)throw new IOException("ambiguous write");
            System.arraycopy(data,0,registers[id],address,data.length);
        }
        @Override public void syncProfiles(Map<Integer,int[]> profiles)throws IOException {
            writes.add("profiles:"+profiles.keySet());
            if(failWrite)throw new IOException("ambiguous profile");
            for(var e:profiles.entrySet()){int id=e.getKey();int[]p=e.getValue();registers[id][41]=(byte)p[2];put(id,42,p[0]);put(id,44,0);put(id,46,p[1]);}
        }
        @Override public void syncPositions(Map<Integer,Integer> positions)throws IOException {
            writes.add("positions:"+positions.keySet());streams.add(Map.copyOf(positions));
            if(failWrite)throw new IOException("ambiguous stream");
            for(var e:positions.entrySet())put(e.getKey(),42,e.getValue());
        }
        @Override public void close(){}
    }
    static final class Rig {
        final ArmProfile profile=ArmProfile.unverifiedDefaults().withPhysicalCalibrationVerified(true);
        final FakeBus bus=new FakeBus(profile);
        final AtomicLong now=new AtomicLong(1_000_000_000L);
        final RobotController c=new RobotController(bus,profile,now::get);
        Rig()throws IOException {this(-1);}
        Rig(int jaw)throws IOException {if(jaw>=0){bus.position(6,jaw);bus.put(6,42,jaw);}c.connectReadOnly();c.attachExistingHold();}
        void step(double seconds)throws IOException {now.addAndGet((long)(seconds*1e9));c.tick(true);}
        GoalTrajectory cycle(boolean home){return new GoalTrajectory(profile,c.positions(),new int[]{2308,2871,2337,1864,3127,894},profile.basket(),home);}
    }

    @Test public void readOnlyConnectAndAttachDoNotEnableOrRewriteMotors()throws Exception {
        Rig r=new Rig();assertEquals(RobotController.State.HOLDING,r.c.state());assertTrue(r.bus.writes.isEmpty());
        assertArrayEquals(r.profile.home(),r.c.positions());
    }
    @Test public void modelOffsetModeAndFactoryAccelerationMismatchesPreventWrites()throws Exception {
        for(int address:new int[]{3,31,33,85}) {
            ArmProfile p=ArmProfile.unverifiedDefaults();FakeBus bus=new FakeBus(p);bus.registers[2][address]++;
            RobotController c=new RobotController(bus,p,System::nanoTime);
            assertThrows(IOException.class,c::connectReadOnly);assertTrue(bus.writes.isEmpty());
        }
    }
    @Test public void disabledMotorsCannotBeAttachedAsExistingHold()throws Exception {
        ArmProfile p=ArmProfile.unverifiedDefaults();FakeBus bus=new FakeBus(p);bus.registers[2][40]=0;
        RobotController c=new RobotController(bus,p,System::nanoTime);c.connectReadOnly();
        assertThrows(IOException.class,c::attachExistingHold);assertTrue(bus.writes.isEmpty());
    }
    @Test public void supportedReleaseThenHoldAgainUsesMeasuredPose()throws Exception {
        Rig r=new Rig();r.c.releaseSupported();r.c.tick(true);
        assertEquals(HoldControl.Action.HOLD,HoldControl.action(r.c));
        r.bus.position(1,2200);r.c.holdSupportedPose();
        assertEquals(2200,r.bus.goal(1));
        assertEquals(RobotController.State.STOPPING,r.c.state());
        r.step(.02);r.step(.79);assertEquals(RobotController.State.HOLDING,r.c.state());
        assertEquals(HoldControl.Action.RELEASE,HoldControl.action(r.c));
    }
    @Test public void supportedReleaseCannotInterruptActiveTravel()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));int before=r.bus.writes.size();
        assertThrows(IOException.class,r.c::releaseSupported);
        assertEquals(before,r.bus.writes.size());
        assertEquals(RobotController.State.MOVING,r.c.state());
    }
    @Test public void releaseWriteFailureNeverClaimsAllMotorsFree()throws Exception {
        Rig r=new Rig();r.bus.failWrite=true;
        assertThrows(IOException.class,r.c::releaseSupported);
        assertEquals(RobotController.State.FAULT_UNKNOWN,r.c.state());
        for(int id=1;id<=6;id++)assertEquals(1,r.bus.registers[id][40]);
    }
    @Test public void manualCalibrationOutsideTravelEnvelopeDoesNotAuthorizeMotion()throws Exception {
        Rig r=new Rig();r.c.releaseSupported();
        int[] pose=r.profile.home();pose[0]=1800; // below the recorded 1905 travel bound
        r.bus.position(1,pose[0]);r.c.tick(true);
        new So101Kinematics(r.profile).forwardTransform(r.c.positions());
        int writes=r.bus.writes.size();
        assertThrows(IllegalArgumentException.class,()->com.figbot.scanner.vision.CalibrationScan.poses(r.profile,r.c.positions()));
        assertEquals(writes,r.bus.writes.size());
        r.c.holdSupportedPose();r.step(.02);r.step(.79);
        assertEquals(1800,r.c.positions()[0]); // hold stays here, never jumps into envelope
    }
    @Test public void supportedActivationTouchesOnlyDisabledJointsAndValidatesHold()throws Exception {
        ArmProfile p=ArmProfile.unverifiedDefaults();FakeBus bus=new FakeBus(p);bus.registers[2][40]=0;bus.registers[3][40]=0;
        AtomicLong now=new AtomicLong(1_000_000_000L);RobotController c=new RobotController(bus,p,now::get);
        c.connectReadOnly();c.holdSupportedPose();assertEquals(RobotController.State.STOPPING,c.state());
        assertEquals(List.of("write:2:41:1","write:2:40:1","write:3:41:1","write:3:40:1"),bus.writes);
        assertEquals(57,St3215Protocol.word(bus.registers[2],46));
        now.addAndGet(20_000_000L);c.tick(true);now.addAndGet(790_000_000L);c.tick(true);assertEquals(RobotController.State.HOLDING,c.state());
    }
    @Test public void supportedActivationFailureDoesNotReleaseOtherExistingHolds()throws Exception {
        ArmProfile p=ArmProfile.unverifiedDefaults();FakeBus bus=new FakeBus(p);bus.registers[2][40]=0;bus.failWrite=true;
        RobotController c=new RobotController(bus,p,System::nanoTime);c.connectReadOnly();
        assertThrows(IOException.class,c::holdSupportedPose);assertEquals(RobotController.State.FAULT_UNKNOWN,c.state());
        assertEquals(List.of("write:2:41:1"),bus.writes);assertEquals(1,bus.registers[1][40]);
    }
    @Test public void unverifiedCalibrationCannotStartPhysicalTravel()throws Exception {
        Rig r=new Rig();r.c.setProfile(ArmProfile.unverifiedDefaults());
        assertThrows(IOException.class,()->r.c.start(r.cycle(false)));assertTrue(r.bus.writes.isEmpty());
    }
    @Test public void updatingProfileCannotReplaceConnectedEncoderIdentity()throws Exception {
        Rig r=new Rig();int[] offsets=r.profile.offsets();offsets[0]++;
        ArmProfile other=new ArmProfile(offsets,r.profile.referenceRaw(),r.profile.referenceRadians(),r.profile.directionSigns(),
                r.profile.envelopes(),r.profile.home(),r.profile.basket(),894,1153,true,"test");
        assertThrows(IllegalArgumentException.class,()->r.c.setProfile(other));assertTrue(r.bus.writes.isEmpty());
    }
    @Test public void goalTrajectoryRunsWithPassiveRollAndMeasuredRelease()throws Exception {
        Rig r=new Rig();GoalTrajectory t=r.cycle(true);r.c.start(t);
        for(int k=0;k<1500 && r.c.state()==RobotController.State.MOVING;k++){r.bus.follow();r.step(.02);}
        assertEquals(RobotController.State.HOLDING,r.c.state());assertNotNull(r.c.lastResult());
        assertTrue(r.c.lastResult().releaseCompleteNanos()>r.c.lastResult().releaseStartNanos());
        assertTrue(r.c.lastResult().wallElapsedSeconds()>=t.duration()-.02);
        assertTrue(r.bus.streams.size()>20);assertTrue(r.bus.streams.stream().noneMatch(m->m.containsKey(5)));
        assertArrayEquals(t.end(),r.c.positions());
        assertTrue(r.bus.writes.stream().noneMatch(w->w.matches("write:.*:40:.*")));
    }
    @Test public void hostGapFaultStopsWithoutAutomaticTorqueReleaseOrResume()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));
        assertThrows(IOException.class,()->r.step(.3));assertEquals(RobotController.State.STOPPING,r.c.state());
        r.bus.follow();r.step(.02);r.step(.1);assertEquals(RobotController.State.FAULT_HOLD,r.c.state());
        assertThrows(IOException.class,()->r.c.start(r.cycle(false)));
        for(int id=1;id<=6;id++)assertEquals(1,r.bus.registers[id][40]);
    }
    @Test public void moderateSchedulingGapRetimesPhaseWithoutRelaxingDeadline()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.step(.1);assertEquals(.04,r.c.trajectoryTimeSeconds(),1e-9);
    }
    @Test public void heldFaultAcknowledgementChecksHealthAndDoesNotWrite()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));assertThrows(IOException.class,()->r.step(.3));
        r.bus.follow();r.step(.02);r.step(.1);int writes=r.bus.writes.size();
        r.bus.registers[6][63]=60;assertThrows(IOException.class,()->r.c.acknowledgeHeldFault());
        assertEquals(RobotController.State.FAULT_HOLD,r.c.state());r.bus.registers[6][63]=35;
        r.c.acknowledgeHeldFault();assertEquals(RobotController.State.HOLDING,r.c.state());assertEquals(writes,r.bus.writes.size());
    }
    @Test public void sustainedJawContactStopsWithSingleSmallPreload()throws Exception {
        Rig r=new Rig(1153);
        int[] goal=r.c.positions();goal[5]=870;
        r.c.startGrasp(GoalTrajectory.moveTo(r.profile,r.c.positions(),goal,180));
        int contactAt=1020;
        for(int i=0;i<300&&r.c.state()==RobotController.State.MOVING;i++){
            r.bus.follow();if(r.bus.position(6)<=contactAt){r.bus.position(6,contactAt);r.bus.put(6,69,12);}
            r.step(.02);
        }
        assertEquals(RobotController.State.STOPPING,r.c.state());assertEquals(RobotController.GraspOutcome.CONTACT_POSSIBLE,r.c.graspOutcome());
        assertEquals(contactAt-6,r.bus.goal(6));r.step(.02);r.step(.1);
        assertEquals(RobotController.State.HOLDING,r.c.state());assertEquals(contactAt-6,r.c.heldJawTarget());
    }
    @Test public void graspRejectsBodyDriftBeforeWritingAnyMotor()throws Exception {
        Rig r=new Rig(1153);int[] first=r.c.positions(),goal=first.clone();goal[5]=870;
        GoalTrajectory closing=GoalTrajectory.moveTo(r.profile,first,goal,180);
        r.bus.position(1,first[0]+4); // changes after the caller's pose snapshot
        assertThrows(IOException.class,()->r.c.startGrasp(closing));
        assertTrue(r.bus.writes.isEmpty());assertEquals(RobotController.State.HOLDING,r.c.state());
    }
    @Test public void graspKeepsFreshMeasuredBodyInsteadOfCorrectingSmallDrift()throws Exception {
        Rig r=new Rig(1153);int[] first=r.c.positions(),goal=first.clone();goal[5]=870;
        GoalTrajectory closing=GoalTrajectory.moveTo(r.profile,first,goal,180);
        r.bus.position(1,first[0]+3);
        r.c.startGrasp(closing);
        assertEquals(first[0]+3,r.bus.goal(1));
        for(int i=0;i<300&&r.c.state()==RobotController.State.MOVING;i++){r.bus.follow();r.step(.02);}
        assertEquals(RobotController.State.HOLDING,r.c.state());
        assertEquals(first[0]+3,r.c.positions()[0]);
        assertTrue(r.bus.streams.stream().allMatch(m->m.keySet().stream().allMatch(id->id==6)));
        assertEquals(RobotController.GraspOutcome.CLOSED_UNVERIFIED,r.c.graspOutcome());
        assertNotNull(r.c.lastResult());
    }
    @Test public void closeCompletionWithLightCurrentDoesNotClaimEmptyOrConfirmedContact()throws Exception {
        Rig r=new Rig(1153);int[] goal=r.c.positions();goal[5]=870;
        r.c.startGrasp(GoalTrajectory.moveTo(r.profile,r.c.positions(),goal,180));
        for(int i=0;i<300&&r.c.state()==RobotController.State.MOVING;i++){
            r.bus.follow();r.bus.position(6,Math.min(1153,r.bus.goal(6)+7));r.bus.put(6,69,3);r.step(.02);
        }
        assertEquals(RobotController.State.HOLDING,r.c.state());
        assertEquals(RobotController.GraspOutcome.CLOSED_UNVERIFIED,r.c.graspOutcome());
        assertEquals(877,r.c.positions()[5]);assertNotNull(r.c.lastResult());
    }
    @Test public void graspWithBodyMotionIsRejectedBeforeWrites()throws Exception {
        Rig r=new Rig(1153);int[] goal=r.c.positions();goal[0]+=10;goal[5]=870;
        assertThrows(IOException.class,()->r.c.startGrasp(GoalTrajectory.moveTo(r.profile,r.c.positions(),goal,180)));
        assertTrue(r.bus.writes.isEmpty());
    }
    @Test public void graspRejectsInteriorBodyTravelEvenWhenEndpointsMatch()throws Exception {
        Rig r=new Rig(1200);GoalTrajectory excursion=r.cycle(true);
        assertArrayEquals(Arrays.copyOf(excursion.start(),5),Arrays.copyOf(excursion.end(),5));
        assertTrue(excursion.end()[5]<excursion.start()[5]);
        IOException error=assertThrows(IOException.class,()->r.c.startGrasp(excursion));
        assertEquals("Grasp may move only the jaw",error.getMessage());
        assertTrue(r.bus.writes.isEmpty());
    }
    @Test public void staleClosingPlanCannotOpenJawThatHasAlreadyClosedFurther()throws Exception {
        Rig r=new Rig(880);int[] first=r.c.positions(),goal=first.clone();goal[5]=870;
        GoalTrajectory closing=GoalTrajectory.moveTo(r.profile,first,goal,180);
        r.bus.position(6,865);
        assertThrows(IOException.class,()->r.c.startGrasp(closing));
        assertTrue(r.bus.writes.isEmpty());
    }
    @Test public void requestStopIsIntentOnlyUntilWorkerTick()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));int count=r.bus.writes.size();r.c.requestStop();assertEquals(count,r.bus.writes.size());
        r.step(.02);assertEquals(RobotController.State.STOPPING,r.c.state());r.step(.1);assertEquals(RobotController.State.HOLDING,r.c.state());
        assertTrue(r.bus.writes.stream().noneMatch(w->w.endsWith(":40:0")));
    }
    @Test public void feedbackLossNeverReportsConfirmedHold()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.failFeedback=true;
        assertThrows(IOException.class,()->r.step(.02));assertEquals(RobotController.State.FAULT_UNKNOWN,r.c.state());
        assertNull(r.c.lastResult());assertTrue(r.bus.writes.stream().noneMatch(w->w.endsWith(":40:0")));
    }
    @Test public void trackingBoundFaultStillUsesFiniteFiftyAccelerationStop()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.position(1,r.bus.position(1)+193);
        assertThrows(IOException.class,()->r.step(.02));assertEquals(RobotController.State.STOPPING,r.c.state());
        assertEquals(50,r.bus.registers[1][41]);r.bus.follow();r.step(.02);r.step(.1);assertEquals(RobotController.State.FAULT_HOLD,r.c.state());
    }
    @Test public void staleCameraCausesHoldStopNotRelease()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.now.addAndGet(20_000_000L);
        assertThrows(IOException.class,()->r.c.tick(false));r.bus.follow();r.step(.02);r.step(.1);
        assertEquals(RobotController.State.FAULT_HOLD,r.c.state());for(int id=1;id<=6;id++)assertEquals(1,r.bus.registers[id][40]);
    }
    @Test public void transientVisionWaitCanStopBeforeStaleFaultAndReplanSameGoal()throws Exception {
        Rig r=new Rig();int[] target=r.c.positions();target[0]+=150;
        r.c.start(GoalTrajectory.moveTo(r.profile,r.c.positions(),target,300));
        for(int k=0;k<8;k++){r.bus.follow();r.step(.02);}
        r.bus.follow();r.c.requestStop();r.now.addAndGet(20_000_000L);r.c.tick(false);
        r.bus.follow();r.now.addAndGet(20_000_000L);r.c.tick(false);
        assertEquals(RobotController.State.STOPPING,r.c.state());r.now.addAndGet(100_000_000L);r.c.tick(false);
        assertEquals(RobotController.State.HOLDING,r.c.state());
        assertTrue(r.c.positions()[0]<target[0]);
        r.c.start(GoalTrajectory.moveTo(r.profile,r.c.positions(),target,300));
        for(int k=0;k<200&&r.c.state()==RobotController.State.MOVING;k++){r.bus.follow();r.step(.02);}
        assertEquals(RobotController.State.HOLDING,r.c.state());
        assertEquals(target[0],r.c.positions()[0]);
        for(int id=1;id<=6;id++)assertEquals(1,r.bus.registers[id][40]);
    }
    @Test public void isolatedThermalJumpNeedsThreeFreshConsistentCoolConfirmations()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.temperatureSpikes=1;r.step(.02);
        assertEquals(RobotController.State.MOVING,r.c.state());
        assertEquals(35,r.c.feedback().get(4).temperature());
        assertTrue(r.c.telemetryNote().contains("confirmed=35,35,35"));
    }
    @Test public void initialTemperatureGlitchIsAlsoIndependentlyConfirmed()throws Exception {
        ArmProfile p=ArmProfile.unverifiedDefaults();FakeBus bus=new FakeBus(p);
        bus.temperatureSpikes=1;bus.spikeTemperature=97;
        RobotController c=new RobotController(bus,p,System::nanoTime);c.connectReadOnly();
        assertEquals(35,c.feedback().get(4).temperature());assertTrue(bus.writes.isEmpty());
    }
    @Test public void delayedStationaryPollDoesNotSkipTemperatureConfirmation()throws Exception {
        Rig r=new Rig();r.bus.temperatureSpikes=1;r.step(.4);
        assertEquals(RobotController.State.HOLDING,r.c.state());assertEquals(35,r.c.feedback().get(4).temperature());
    }
    @Test public void stopReachedBeforeDeadlineCanFinishItsStabilityWindow()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.c.requestStop();r.step(.02);
        r.bus.speed(1,100);r.step(.20);
        r.bus.speed(1,0);r.step(.10);
        r.step(.06);assertEquals(RobotController.State.STOPPING,r.c.state());
        r.step(.05);assertEquals(RobotController.State.HOLDING,r.c.state());
    }
    @Test public void ninetySevenDegreeGlitchStillRequiresThreeIndependentCoolReadbacks()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.spikeTemperature=97;r.bus.temperatureSpikes=1;r.step(.02);
        assertEquals(RobotController.State.MOVING,r.c.state());assertEquals(35,r.c.feedback().get(4).temperature());
        r.bus.registers[4][63]=97;assertThrows(IOException.class,()->r.step(.02));
    }
    @Test public void sustainedHighTemperatureStillFaultsAtUnchangedThreshold()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.registers[4][63]=55;
        assertThrows(IOException.class,()->r.step(.02));
        assertNotEquals(RobotController.State.MOVING,r.c.state());
    }
    @Test public void inconsistentThermalConfirmationCannotClearTheFault()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.temperatureSpikes=1;r.bus.temperatureOnlySpikes=1;
        assertThrows(IOException.class,()->r.step(.02));
        assertNotEquals(RobotController.State.MOVING,r.c.state());
    }
    @Test public void coldInconsistentFirstReadRequiresThreeSubsequentConsistentReads()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.temperatureSpikes=1;
        r.bus.temperatureOnlySpikes=1;r.bus.temperatureOnlySpikeValue=38;r.step(.02);
        assertEquals(RobotController.State.MOVING,r.c.state());
        assertEquals(35,r.c.feedback().get(4).temperature());
        assertTrue(r.c.telemetryNote().contains("confirmed=38,35,35,35"));
    }
    @Test public void repeatedBlockGlitchRequiresThreeSeparateRegisterConfirmations()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.temperatureSpikes=2;r.bus.spikeTemperature=97;
        r.step(.02);assertEquals(RobotController.State.MOVING,r.c.state());
        assertEquals(35,r.c.feedback().get(4).temperature());
        assertTrue(r.c.telemetryNote().contains("block temperatures=97,97 confirmed=35,35,35"));
    }
    @Test public void liveThirdSlotOutlierNeedsThreeLaterColdReadings()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.temperatureSpikes=1;r.bus.spikeTemperature=91;
        r.bus.directTemperatures.addAll(List.of(34,34,38,34,34,34));r.step(.02);
        assertEquals(RobotController.State.MOVING,r.c.state());
        assertEquals(34,r.c.feedback().get(4).temperature());
        assertTrue(r.c.telemetryNote().contains("confirmed=34,34,38,34,34,34"));
    }
    @Test public void boundedColdReadbacksCannotWaitForeverForAgreement()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.temperatureSpikes=1;
        r.bus.directTemperatures.addAll(List.of(34,38,34,38,34,38));
        assertThrows(IOException.class,()->r.step(.02));
        assertNotEquals(RobotController.State.MOVING,r.c.state());
    }
    @Test public void hotThirdReadIsNotDiscardedAsAnOutlier()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.bus.temperatureSpikes=1;
        r.bus.directTemperatures.addAll(List.of(34,34,55,34,34,34));
        assertThrows(IOException.class,()->r.step(.02));
        assertNotEquals(RobotController.State.MOVING,r.c.state());
    }
    @Test public void onlyExplicitSupportedReleaseDisablesTorque()throws Exception {
        Rig r=new Rig();r.c.releaseSupported();assertEquals(RobotController.State.DISARMED,r.c.state());
        for(int id=1;id<=6;id++)assertEquals(0,r.bus.registers[id][40]);
    }
    @Test public void jawOpeningCannotStartOutsideMeasuredBasketRegion()throws Exception {
        Rig r=new Rig();GoalTrajectory t=r.cycle(false);r.c.start(t);
        while(r.c.trajectoryTimeSeconds()<t.releaseStart()-.03){r.bus.follow();r.step(.02);}
        int closed=r.profile.gripperClosed();boolean sawClosedBeyondNominalStart=false;
        for(int k=0;k<6;k++) {
            r.bus.follow();r.bus.position(1,r.profile.basket()[0]-100);r.bus.speed(1,400);
            r.step(.02);
            if(r.c.trajectoryTimeSeconds()>=t.releaseStart()) {
                assertEquals(closed,r.bus.goal(6));sawClosedBeyondNominalStart=true;
            }
        }
        assertTrue(sawClosedBeyondNominalStart);
        for(int id=1;id<=5;id++){r.bus.position(id,id==5?r.profile.home()[4]:r.profile.basket()[id-1]);r.bus.speed(id,0);}
        r.step(.02);assertTrue(r.bus.goal(6)>closed);
    }
    @Test public void pickupWaitsForMeasuredClosureThenFaultsInsteadOfCarrying()throws Exception {
        Rig r=new Rig();GoalTrajectory t=r.cycle(false);r.c.start(t);
        while(r.c.trajectoryTimeSeconds()<t.pickupTime()-.04){r.bus.follow();r.step(.02);}
        IOException fault=null;
        for(int k=0;k<20;k++) {
            r.bus.follow();r.bus.position(6,r.profile.gripperClosed()+30);
            try{r.step(.02);}catch(IOException e){fault=e;break;}
            assertTrue(r.c.trajectoryTimeSeconds()<=t.pickupTime()+1e-9);
        }
        assertNotNull(fault);assertTrue(fault.getMessage().contains("Pickup jaw"));
        assertEquals(RobotController.State.STOPPING,r.c.state());
    }
    @Test public void singleSettledPacketDuringBrakingCannotAuthorizeAnotherLeg()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.c.requestStop();r.step(.02);
        assertEquals(RobotController.State.STOPPING,r.c.state());
        r.bus.speed(3,150);r.step(.02);assertEquals(RobotController.State.STOPPING,r.c.state());
        r.bus.speed(3,0);r.step(.02);r.step(.08);assertEquals(RobotController.State.STOPPING,r.c.state());
        r.step(.02);assertEquals(RobotController.State.HOLDING,r.c.state());
    }
    @Test public void failedStopDoesNotDisableTorqueOrClaimSafety()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.c.requestStop();r.bus.speed(1,1000);r.step(.02);
        assertEquals(RobotController.State.STOPPING,r.c.state());r.now.addAndGet(910_000_000L);
        assertThrows(IOException.class,()->r.c.tick(true));assertEquals(RobotController.State.FAULT_UNKNOWN,r.c.state());
        for(int id=1;id<=6;id++)assertEquals(1,r.bus.registers[id][40]);
    }
    @Test public void updatedProfileIsForbiddenDuringMotion()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));assertThrows(IllegalStateException.class,()->r.c.setProfile(r.profile));
    }
    @Test public void singleLegCannotBypassConnectedTravelSpeedLimit()throws Exception {
        Rig r=new Rig();int[] target=r.c.positions();target[0]=3200;
        GoalTrajectory tooFast=GoalTrajectory.moveTo(r.profile,r.c.positions(),target,3400);
        assertTrue(tooFast.maxSpeed()>r.profile.speedLimit());
        assertThrows(IOException.class,()->r.c.start(tooFast));assertTrue(r.bus.writes.isEmpty());
    }
    @Test public void stopAllowsBrakeOvershootAndReturnBeforeReportingFailure()throws Exception {
        Rig r=new Rig();r.c.start(r.cycle(false));r.c.requestStop();r.bus.speed(1,1050);r.step(.02);
        r.now.addAndGet(600_000_000L);r.bus.speed(1,-200);r.c.tick(true);
        assertEquals(RobotController.State.STOPPING,r.c.state());
        r.bus.follow();r.now.addAndGet(80_000_000L);r.c.tick(true);assertEquals(RobotController.State.STOPPING,r.c.state());r.now.addAndGet(100_000_000L);r.c.tick(true);assertEquals(RobotController.State.HOLDING,r.c.state());
    }
}
