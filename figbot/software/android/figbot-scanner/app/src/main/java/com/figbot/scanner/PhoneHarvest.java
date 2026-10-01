package com.figbot.scanner;

import android.app.*;
import android.content.*;
import android.hardware.usb.*;
import android.os.Build;
import android.text.InputType;
import android.widget.*;
import androidx.core.content.ContextCompat;
import com.figbot.scanner.so101.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

/** Foreground phone brain. The single motor worker owns USB; inference and IK never own it. */
final class PhoneHarvest implements AutoCloseable {
    record Seen(double[] world,float confidence,String source){}
    record Frame(long captured,long received,String epoch,List<Seen> seen,float[] translation,float[] rotation){}
    record PendingPoint(String type,double[] measured){}
    record Prepared(long targetId,String epoch,int[] pickup,double[] targetMm,long observed){}
    record PoseSample(long nanos,int[] raw,double phase,Job job){}
    static final class Job {
        final long id; final GoalTrajectory route; final PickEvidence evidence;
        Job(long id,GoalTrajectory route,PickEvidence evidence){this.id=id;this.route=route;this.evidence=evidence;}
    }
    private static final String USB_PERMISSION="com.figbot.scanner.SO101_USB";
    private final Activity activity;
    private final TextView status;
    private final Runnable requestTap;
    final PhoneSetup setup;
    private final UsbManager usb;
    private final boolean pcMode;
    private final ScheduledExecutorService motor=Executors.newSingleThreadScheduledExecutor(r->new Thread(r,"figbot-motor"));
    private final ExecutorService planner=Executors.newSingleThreadExecutor(r->new Thread(r,"figbot-planner"));
    private final AtomicReference<Frame> frame=new AtomicReference<>();
    private final AtomicReference<Prepared> prepared=new AtomicReference<>();
    private final AtomicBoolean planning=new AtomicBoolean(),stop=new AtomicBoolean();
    private final TargetTracker tracker=new TargetTracker(new TargetTracker.Config(30,.55,3,750_000_000L,8_000_000_000L,25));
    private final List<Job> pendingEvidence=new ArrayList<>();
    private final ArrayDeque<PoseSample> poseHistory=new ArrayDeque<>();
    private final ArrayDeque<PickEvidence.BaselineFrame> baselineHistory=new ArrayDeque<>();
    private volatile RobotController controller;
    private ServoBus bus;
    private volatile boolean autonomous,closed;
    private volatile int testSpeed=PhoneSetup.SPEED_SLOW;
    private volatile double[] testTargetMm;
    private volatile boolean testActive;
    private boolean returning;
    private int attempted,confirmed,unknown;
    private long lastFrame=-1,idleSince,lastUi;
    private String epoch="none",message="USB bağlı değil · Önce kol ayarlarını tamamla.";
    private Frame mount;
    private Job activeJob;
    private List<double[]> latestObjects=List.of();
    private PendingPoint pendingPoint;
    private AlertDialog settingsDialog;
    private final BroadcastReceiver receiver=new BroadcastReceiver(){
        @Override public void onReceive(Context c,Intent i){
            if(USB_PERMISSION.equals(i.getAction())){
                UsbDevice device=i.getParcelableExtra(UsbManager.EXTRA_DEVICE);
                if(device!=null&&i.getBooleanExtra(UsbManager.EXTRA_PERMISSION_GRANTED,false))open(device);
                else say("USB izni verilmedi; motor komutu gönderilmedi.");
            }else if(UsbManager.ACTION_USB_DEVICE_DETACHED.equals(i.getAction())){
                stop();say("USB ayrıldı. Motorun durduğunu bağlantı üzerinden doğrulayamıyorum.");
            }
        }
    };
    PhoneHarvest(Activity a,TextView s,Runnable tap){
        activity=a;status=s;requestTap=tap;setup=new PhoneSetup(a);usb=(UsbManager)a.getSystemService(Context.USB_SERVICE);
        pcMode=a.getIntent().getBooleanExtra("pc_bridge",false);
        if(pcMode)message="PC modu · PC_Uzerinden_Toplama.cmd açıkken PC’ye bağlan.";
        IntentFilter filter=new IntentFilter(USB_PERMISSION);filter.addAction(UsbManager.ACTION_USB_DEVICE_DETACHED);
        ContextCompat.registerReceiver(a,receiver,filter,ContextCompat.RECEIVER_NOT_EXPORTED);
        motor.scheduleWithFixedDelay(this::tick,0,20,TimeUnit.MILLISECONDS);
    }
    void frame(long captured,String revision,List<Seen> observations,float[]translation,float[]rotation){
        frame.set(new Frame(captured,System.nanoTime(),revision,List.copyOf(observations),translation.clone(),rotation.clone()));
    }
    void lost(){frame.set(null);pendingPoint=null;stop();}
    void stop(){autonomous=false;stop.set(true);RobotController c=controller;if(c!=null)c.requestStop();}
    void connect(){
        if(pcMode){submit(()->{
            if(controller!=null)throw new IllegalStateException("PC zaten bağlı.");
            ServoBus candidate=PcServoBus.open();
            try{RobotController c=new RobotController(candidate,setup.effectiveProfile(),System::nanoTime);c.connectReadOnly();bus=candidate;controller=c;say("PC üzerinden altı motor okundu. Kol ayarlarıyla devam et.");}
            catch(Exception e){candidate.close();throw e;}
        });return;}
        if(controller!=null){say("USB zaten bağlı. Önce aynı duruşta tutmayı aç veya devral.");return;}
        List<UsbDevice> devices=new ArrayList<>(usb.getDeviceList().values());
        if(devices.isEmpty()){say("Telefonu USB veri kablosuyla motor kartına bağla. Telefon USB host olmalı.");return;}
        String[] names=devices.stream().map(d->String.format(Locale.US,"%s · %04X:%04X",d.getProductName(),d.getVendorId(),d.getProductId())).toArray(String[]::new);
        new AlertDialog.Builder(activity).setTitle("Motor kartını seç").setItems(names,(d,n)->{
            UsbDevice device=devices.get(n);
            if(usb.hasPermission(device))open(device);else{
                Intent intent=new Intent(USB_PERMISSION).setPackage(activity.getPackageName());
                PendingIntent pi=PendingIntent.getBroadcast(activity,0,intent,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
                usb.requestPermission(device,pi);
            }
        }).show();
    }
    private void open(UsbDevice device){submit(()->{
        if(controller!=null)throw new IllegalStateException("USB zaten bağlı.");
        ServoBus candidate=UsbServoBus.open(usb,device);
        try{RobotController c=new RobotController(candidate,setup.effectiveProfile(),System::nanoTime);c.connectReadOnly();bus=candidate;controller=c;
            say("Altı ST3215 okundu. Bağlanma hareket veya tork açmadı.");}
        catch(Exception e){candidate.close();throw e;}
    });}
    /** Test mode: single supervised move from the current held pose to the newest
     * camera-confirmed fig position, at the selected speed. No autonomous cycle,
     * no grip: the jaw stays open so the physical offset stays measurable. */
    void start(){submit(()->{
        requireController();
        if(controller.state()==RobotController.State.DISARMED)controller.attachExistingHold();
        if(controller.state()!=RobotController.State.HOLDING)throw new IllegalStateException("Önce mevcut duruşta motor tutmasını doğrula.");
        Frame f=frame.get();if(!fresh(f,System.nanoTime()))throw new IllegalStateException("Güncel sabit kamera gerekli.");
        TargetTracker.Target target=tracker.snapshot(System.nanoTime()).stream()
                .filter(t->t.fresh&&t.state==TargetTracker.State.CONFIRMED).findFirst()
                .orElseThrow(()->new IllegalStateException("Doğrulanmış incir yok; kamerayı incire tut ve bekle."));
        ArmProfile p=setup.testProfile();
        int[]seed=controller.positions();
        double pitch=Double.isFinite(setup.pitch)?setup.pitch:0;
        int[]pickup=new So101Kinematics(p).inverse(target.positionMm(),pitch,seed);
        pickup[5]=p.gripperOpen();  // hover open: grip stays measurable, nothing squashed
        GoalTrajectory route=GoalTrajectory.moveTo(p,seed,pickup,testSpeed);
        controller.setProfile(p);
        controller.start(route);
        testTargetMm=target.positionMm().clone();testActive=true;
        say(String.format(Locale.US,"Hedefe git · XYZ %.0f / %.0f / %.0f mm · %s · Tahmini %.2f sn · Sapmayı gözle.",
                target.positionMm()[0],target.positionMm()[1],target.positionMm()[2],
                PhoneSetup.speedLabel(testSpeed),route.duration()));
    });}
    /** Return to the recorded home pose at the gentle home-speed limits. */
    void goHome(){submit(()->{
        requireController();
        if(controller.state()==RobotController.State.DISARMED)controller.attachExistingHold();
        if(controller.state()!=RobotController.State.HOLDING)throw new IllegalStateException("Önce mevcut duruşta motor tutmasını doğrula.");
        ArmProfile p=setup.testProfile();
        GoalTrajectory route=GoalTrajectory.moveToHome(p,controller.positions());
        controller.setProfile(p);testTargetMm=null;testActive=false;
        controller.start(route);
        say("Kayıtlı başlangıca dönülüyor.");
    });}
    /** Cycles Yavaş(300) -> Orta(700) -> Hızlı(1200) counts/s; returns the UI label. */
    String cycleSpeed(){
        testSpeed=testSpeed<=PhoneSetup.SPEED_SLOW+50?PhoneSetup.SPEED_MEDIUM
                :testSpeed<=PhoneSetup.SPEED_MEDIUM+50?PhoneSetup.SPEED_FAST:PhoneSetup.SPEED_SLOW;
        String label=PhoneSetup.speedLabel(testSpeed);
        say(label+" seçildi ("+testSpeed+" sayım/s).");
        return label;
    }
    void preview(){submit(()->{
        FixedCameraCalibration fixed=setup.fixedCamera;
        boolean ready=fixed!=null?fixed.isComplete()&&fixed.isReady():
                setup.workspace!=null&&setup.workspace.isValidated()&&setup.workspace.groundPlane()!=null;
        if(!ready)throw new IllegalStateException("Önce kamera eşlemesi ve zemin ölçümü gerekli.");
        TargetTracker.Target target=tracker.snapshot(System.nanoTime()).stream().filter(t->t.fresh&&t.state==TargetTracker.State.CONFIRMED).findFirst().orElseThrow(()->new IllegalStateException("Üç ayrı görüntüde doğrulanmış incir bekleniyor."));
        ArmProfile p=setup.effectiveProfile();int[]start=controller==null?p.home():controller.positions();
        planner.execute(()->{try{
        int[]q=new So101Kinematics(p).inverse(target.positionMm(),setup.pitch,start);q[5]=p.gripperClosed();
        GoalTrajectory route=new GoalTrajectory(p,start,q,p.basket(),false);checkGround(route,p,setup);
        say(String.format(Locale.US,"Önizleme #%d · XYZ %.0f / %.0f / %.0f mm · %.2f sn · Motor sürülmedi.",target.id,target.positionMm()[0],target.positionMm()[1],target.positionMm()[2],route.duration()));
    }catch(Exception e){say(e.getMessage());}});});}
    private void tick(){
        if(closed)return;
        try{
            long now=System.nanoTime();Frame f=frame.get();
            if(stop.getAndSet(false)){autonomous=false;cancelReservations(now);if(controller!=null)controller.requestStop();}
            if(f!=null&&!f.epoch.equals(epoch)){boolean previous=!epoch.equals("none");epoch=f.epoch;tracker.reset(epoch);prepared.set(null);lastFrame=-1;
                activeJob=null;pendingEvidence.clear();poseHistory.clear();baselineHistory.clear();if(previous){setup.clearWorkspace();pendingPoint=null;say("Kamera oturumu değişti; kamera eşleme ölçümleri yenilenmeli.");}
                if(autonomous){stop();say("Kamera oturumu değişti; yeniden Başlat gerekli.");}}
            if(fresh(f,now)&&f.captured!=lastFrame){lastFrame=f.captured;consume(f,now);}
            if(autonomous&&(!fresh(f,now)||mount==null||!ObservationTiming.stationary(mount.translation,f.translation,mount.rotation,f.rotation))){
                stop();say("Kamera eskidi veya telefon yerinden oynadı; toplama durduruldu.");}
            RobotController c=controller;
            if(c!=null){try{c.tick(fresh(f,now));}catch(Exception e){autonomous=false;cancelReservations(System.nanoTime());say(e.getMessage());}}
            if(c!=null){long readNs=System.nanoTime();poseHistory.addLast(new PoseSample(readNs,c.positions(),c.trajectoryTimeSeconds(),activeJob));while(!poseHistory.isEmpty()&&readNs-poseHistory.getFirst().nanos>1_500_000_000L)poseHistory.removeFirst();}
            if(c!=null&&activeJob!=null&&c.state()==RobotController.State.HOLDING){
                RobotController.Result result=c.lastResult();
                if(result!=null){activeJob.evidence.released(result.releaseCompleteNanos());pendingEvidence.add(activeJob);attempted++;
                    say(String.format(Locale.US,"Deneme %d · %.2f sn · Sepete bırakma görüntüsü kontrol ediliyor.",attempted,result.wallElapsedSeconds()));}
                activeJob=null;idleSince=now;
            }
            if(c!=null&&testActive&&c.state()==RobotController.State.HOLDING){
                testActive=false;
                double[]goal=testTargetMm;testTargetMm=null;
                if(goal!=null){
                    double[]reached=new So101Kinematics(setup.testProfile()).forward(c.positions());
                    double drift=Math.sqrt(Math.pow(reached[0]-goal[0],2)+Math.pow(reached[1]-goal[1],2)+Math.pow(reached[2]-goal[2],2));
                    say(String.format(Locale.US,"Varıldı · Model XYZ %.0f / %.0f / %.0f mm · Hedef %.0f / %.0f / %.0f mm · Model sapması %.1f mm · Fiziksel sapmayı incire göre ölç ve bildir.",
                            reached[0],reached[1],reached[2],goal[0],goal[1],goal[2],drift));
                }
            }
            verifyEvidence(f,now);
            if(autonomous&&c!=null&&c.state()==RobotController.State.HOLDING){
                if(returning){autonomous=false;returning=false;say("Başlangıca dönüldü. Görüntüyle doğrulanan "+confirmed+", belirsiz "+unknown+".");}
                else if(attempted>=3||now-idleSince>5_000_000_000L){
                    GoalTrajectory home=GoalTrajectory.moveToHome(setup.effectiveProfile(),c.positions());checkGround(home,setup.effectiveProfile(),setup);
                    c.start(home);returning=true;
                }else{
                    Prepared next=prepared.getAndSet(null);
                    if(next!=null){TargetTracker.Target t=tracker.get(next.targetId,now);
                        if(t==null||!t.fresh||!epoch.equals(next.epoch)||ArmValidation.distance(t.positionMm(),next.targetMm)>8){tracker.markUnknown(next.targetId,now);}
                        else{ArmProfile p=setup.effectiveProfile();GoalTrajectory route=new GoalTrajectory(p,c.positions(),next.pickup,p.basket(),false);checkGround(route,p,setup);
                            PickEvidence evidence;
                            try{evidence=PickEvidence.withBaseline(setup.basketVolume,setup.jawRadius,setup.novelty,new ArrayList<>(baselineHistory));}
                            catch(Exception noBaseline){tracker.markUnknown(next.targetId,System.nanoTime());say("Kavrama öncesi üç kararlı görüntü yok; hedef atlandı.");evidence=null;}
                            if(evidence!=null){activeJob=new Job(next.targetId,route,evidence);c.start(route);idleSince=now;}}
                    }
                }
            }
            if(autonomous&&!returning&&attempted<3&&prepared.get()==null&&planning.compareAndSet(false,true))prepareNext();
            if(now-lastUi>250_000_000L){lastUi=now;long uiNow=System.nanoTime();String line=message+"\n"+(c==null?"USB kapalı":c.state().toString())+" · Hedef "+tracker.snapshot(uiNow).size()+" · Doğrulanan "+confirmed+" · Belirsiz "+unknown;activity.runOnUiThread(()->status.setText(line));}
        }catch(Exception e){autonomous=false;cancelReservations(System.nanoTime());if(controller!=null)controller.requestStop();say(e.getMessage());}
    }
    private void consume(Frame f,long now){
        FixedCameraCalibration fixed=setup.fixedCamera;
        WorkspaceCalibration w=setup.workspace;
        if(fixed!=null)fixed.updatePose(f.translation,f.rotation);
        if(fixed==null&&w==null)return;
        List<TargetTracker.Detection>targets=new ArrayList<>();List<double[]>objects=new ArrayList<>();
        for(Seen seen:f.seen){
            if(seen.world==null||seen.confidence<.55||seen.source.equals("ARCORE_FEATURE_POINT_HIT"))continue;
            double[]robot=fixed!=null?fixed.toRobotMm(seen.world):w.toRobotMm(seen.world);
            if(seen.source.equals("ARCORE_DEPTH_HIT"))objects.add(robot);
            try{
                double[]pick;
                if(fixed!=null){
                    // Test build: XY from the detection, Z from measured ground + grip height.
                    // The fig-height-range filter is skipped so a wrong mount angle stays
                    // measurable instead of silently dropping every target.
                    FixedCameraCalibration.FlatGround g=fixed.ground();
                    double z=g!=null?g.heightAt(robot[0],robot[1])+g.pickOffsetMm:robot[2];
                    pick=new double[]{robot[0],robot[1],z};
                }else pick=w.toPickTargetMm(seen.world);
                targets.add(new TargetTracker.Detection(pick,seen.confidence,f.captured));
            }catch(IllegalArgumentException|IllegalStateException ignored){}
        }
        latestObjects=List.copyOf(objects);tracker.update(targets,now,epoch);
        baselineHistory.addLast(new PickEvidence.BaselineFrame(f.captured,latestObjects));
        while(baselineHistory.size()>8||(!baselineHistory.isEmpty()&&f.captured-baselineHistory.getFirst().capturedNs()>2_000_000_000L))baselineHistory.removeFirst();
    }
    private void prepareNext(){
        TargetTracker.Target target=tracker.reserveNext(System.nanoTime());
        if(target==null){planning.set(false);return;}
        String plannedEpoch=epoch;ArmProfile p=setup.effectiveProfile();
        int[]seed=activeJob==null?controller.positions():p.basket();double pitch=setup.pitch;
        planner.execute(()->{try{
            int[]pickup=new So101Kinematics(p).inverse(target.positionMm(),pitch,seed);pickup[5]=p.gripperClosed();
            GoalTrajectory route=new GoalTrajectory(p,seed,pickup,p.basket(),false);checkGround(route,p,setup);
            submit(()->{if(autonomous&&plannedEpoch.equals(epoch))prepared.set(new Prepared(target.id,plannedEpoch,pickup,target.positionMm(),target.lastSeenNs));
                else if(plannedEpoch.equals(epoch))tracker.markUnknown(target.id,System.nanoTime());planning.set(false);});
        }catch(Exception e){submit(()->{if(plannedEpoch.equals(epoch))tracker.markFailed(target.id,System.nanoTime());planning.set(false);say("Hedef atlandı: "+e.getMessage());});}});
    }
    private void verifyEvidence(Frame f,long now){
        FixedCameraCalibration fixed=setup.fixedCamera;
        boolean groundReady=fixed!=null?fixed.ground()!=null:
                setup.workspace!=null&&setup.workspace.groundPlane()!=null;
        if(controller==null||!groundReady)return;
        PoseSample matched=null;if(f!=null)for(PoseSample item:poseHistory)
            if(Math.abs(item.nanos-f.captured)<=40_000_000L&&(matched==null||Math.abs(item.nanos-f.captured)<Math.abs(matched.nanos-f.captured)))matched=item;
        double[]tip=new So101Kinematics(setup.effectiveProfile()).forward(matched==null?controller.positions():matched.raw);
        double ground=fixed!=null?fixed.ground().heightAt(tip[0],tip[1]):setup.workspace.groundPlane().heightAt(tip[0],tip[1]);
        if(activeJob!=null&&f!=null&&matched!=null&&matched.job==activeJob){double phase=matched.phase;
            activeJob.evidence.observe(f.captured,now,latestObjects,tip,phase>activeJob.route.pickupTime()&&phase<activeJob.route.releaseStart(),ground);}
        for(Iterator<Job>it=pendingEvidence.iterator();it.hasNext();){Job job=it.next();
            PickEvidence.Outcome outcome=job.evidence.observe(f==null?0:f.captured,now,latestObjects,tip,false,ground);
            if(outcome==PickEvidence.Outcome.CONFIRMED){tracker.markCollected(job.id,now);confirmed++;it.remove();}
            else if(outcome==PickEvidence.Outcome.UNKNOWN){tracker.markUnknown(job.id,now);unknown++;it.remove();}
        }
    }
    static void checkGround(GoalTrajectory path,ArmProfile p,WorkspaceCalibration w){
        if(w==null||w.groundPlane()==null)throw new IllegalStateException("Ölçülmüş zemin gerekli.");
        So101Kinematics model=new So101Kinematics(p);
        for(double t=0;t<=path.duration()+.02;t+=.02){double[]tip=model.forward(path.sample(Math.min(t,path.duration())));
            if(tip[2]<w.groundPlane().heightAt(tip[0],tip[1]))throw new IllegalArgumentException("Hesaplanan kıskaç yolu zeminin altına giriyor.");}
    }
    /** Fixed camera mount variant: ground comes from the measured flat configuration. */
    static void checkGround(GoalTrajectory path,ArmProfile p,PhoneSetup setup){
        FixedCameraCalibration fixed=setup.fixedCamera;
        if(fixed!=null){
            if(fixed.ground()==null)throw new IllegalStateException("Zemin ve kavrama yüksekliği ölçüleri gerekli.");
            So101Kinematics model=new So101Kinematics(p);
            for(double t=0;t<=path.duration()+.02;t+=.02){double[]tip=model.forward(path.sample(Math.min(t,path.duration())));
                if(tip[2]<fixed.ground().heightAt(tip[0],tip[1]))throw new IllegalArgumentException("Hesaplanan kıskaç yolu zeminin altına giriyor.");}
            return;
        }
        checkGround(path,p,setup.workspace);
    }
    private static boolean fresh(Frame f,long now){return f!=null&&ObservationTiming.fresh(f.captured,now)&&now-f.received<750_000_000L;}
    private interface Work{void run()throws Exception;}
    private void submit(Work work){if(!closed)motor.execute(()->{try{work.run();}catch(Exception e){say(e.getMessage());}});}
    private void requireController(){if(controller==null)throw new IllegalStateException("Önce USB motor kartına bağlan.");}
    private void say(String text){message=text==null?"İşlem tamamlanamadı.":text;activity.runOnUiThread(()->status.setText(message));}
    private void cancelReservations(long now){
        Prepared next=prepared.getAndSet(null);if(next!=null&&next.epoch.equals(epoch))tracker.markUnknown(next.targetId,now);
        if(activeJob!=null){tracker.markUnknown(activeJob.id,now);activeJob=null;unknown++;}
    }
    private void geometryChanged(){submit(()->{cancelReservations(System.nanoTime());tracker.reset(epoch);lastFrame=-1;});}

    void settings(){
        stop();LinearLayout p=ControlUi.column(activity);ScrollView scroll=new ScrollView(activity);scroll.addView(p);
        ControlUi.text(activity,p,"Hedef testi · basit akış",23);
        ControlUi.text(activity,p,"1 · Bağlan  2 · Mevcut tutmayı devral  3 · Kamerayı incire tut  4 · Hedefe git",15);
        ControlUi.text(activity,p,"Başlangıç/sepet duruşları ve ölçüler kayıtlı oturum değerleridir; yeniden öğretmek isteğe bağlıdır.",13);
        ControlUi.button(activity,p,pcMode?"PC’ye bağlan · yalnız oku":"USB kartını bağla · yalnız oku",v->connect());
        if(pcMode)ControlUi.text(activity,p,"PC_Uzerinden_Toplama.cmd açık kalmalı. Telefon ve motor kartı PC’ye ayrı kablolarla bağlıdır. Kalibrasyon ve toplama düğmeleri bu ekranda aynı şekilde çalışır.",14);
        ControlUi.button(activity,p,"Mevcut motor tutmasını devral",v->submit(()->{requireController();controller.attachExistingHold();say("Mevcut tutma doğrulandı.");}));
        ControlUi.button(activity,p,"Kolu destekliyorum · aynı yerde tutmayı aç",v->submit(()->{requireController();controller.holdSupportedPose();say("Aynı duruşta tutma kontrol ediliyor; destekli tut.");}));
        ControlUi.button(activity,p,"Kolu destekliyorum · motorları serbest bırak",v->submit(()->{requireController();controller.releaseSupported();say("Motorlar serbest; elle ölçüm duruşuna getirebilirsin.");}));
        for(String[]entry:new String[][]{{"home","Kapalı başlangıcı kaydet"},{"basket","Sepet bırakma duruşunu kaydet"},{"closed","İnciri tutan kıskaç açıklığını kaydet"},{"open","Açık kıskaç konumunu kaydet"}})
            ControlUi.button(activity,p,entry[1],v->submit(()->{capturePose(entry[0]);geometryChanged();say(entry[1]+": tamam.");}));
        ControlUi.text(activity,p,"Kamera ve kol ölçümü",20);
        if(setup.fixedCameraAvailable()){
            ControlUi.text(activity,p,"Sabit kamera montajı etkin: kamera–taban dönüşümü uygulama içinden gelir. 4 eşleme + 3 kontrol noktası ve zemin dokunuşu gerekmez; telefon sabit kaldığı sürece her karede pozu otomatik güncellenir.",14);
            ControlUi.text(activity,p,"Kamera durumu: "+(setup.fixedCamera.isReady()?"kamera pozu alındı":"kamera görüntüsü bekleniyor")+" · "+setup.fixedCamera.description(),13);
        }else{
        ControlUi.text(activity,p,"Robotun mekanik tabanını orijin al. Bilinen noktaların XYZ değerlerini cetvelle ölç. İlk 4 nokta eşleme, sonraki 3 farklı nokta doğrulama içindir; tüm toplama alanına yay.",14);
        for(String[]entry:new String[][]{{"fit","Kamera eşleme noktası"},{"held","Bağımsız kamera kontrol noktası"},{"ground","Zemin noktası"}})
            ControlUi.button(activity,p,entry[1],v->pointDialog(entry[0]));
        }
        ControlUi.button(activity,p,"Bağımsız kıskaç ucu ölçümü",v->pointDialog("arm"));
        ControlUi.button(activity,p,"Zemin, kavrama ve sepet ölçüleri",v->dimensionsDialog());
        if(!setup.fixedCameraAvailable())
            ControlUi.button(activity,p,"Bu oturumun kamera ölçümlerini temizle",v->{setup.clearWorkspace();geometryChanged();say("Kamera ölçümleri temizlendi.");});
        ControlUi.text(activity,p,"İlk deneme: sabit telefon ve kol, düz zemin, boş hareket alanı. Bu sürüm engellerin tam hacmini modellemez. Ekrandan ayrılma yeni hareketleri durdurur; USB koparsa motor duruşu doğrulanamayabilir.",13);
        settingsDialog=new AlertDialog.Builder(activity).setView(scroll).setPositiveButton("Kameraya dön",null).show();
    }
    private void pointDialog(String type){
        LinearLayout p=ControlUi.column(activity);EditText[]fields=new EditText[3];String[]names={"X (mm)","Y (mm)","Z (mm)"};
        for(int i=0;i<3;i++){fields[i]=number(p,names[i],Double.NaN);}
        new AlertDialog.Builder(activity).setTitle(type.equals("arm")?"Kıskaç ucunun ölçülen konumu":"Ölçülü referans noktası").setView(p)
            .setPositiveButton(type.equals("arm")?"Enkoderle karşılaştır":"Noktayı görüntüden seç",(d,n)->{try{
                double[]xyz=values(fields);
                if(type.equals("arm"))submit(()->{requireStationaryPose();double error=setup.arm.add(controller.positions(),xyz);setup.save();say(String.format(Locale.US,"Uç ölçüm farkı %.1f mm · %d kayıt",error,setup.arm.measurements().size()));});
                else{pendingPoint=new PendingPoint(type,xyz);if(settingsDialog!=null)settingsDialog.dismiss();requestTap.run();say("Ölçtüğün referans noktasına kamera görüntüsünde dokun.");}
            }catch(Exception e){say(e.getMessage());}}).setNegativeButton("Vazgeç",null).show();
    }
    void worldTap(double[]world){PendingPoint p=pendingPoint;pendingPoint=null;if(p==null)return;
        try{setup.addPoint(p.type,world,p.measured);geometryChanged();
            say("Eşleme "+setup.fit.size()+" / kontrol "+setup.held.size()+" / zemin "+setup.groundPoints.size()+" ölçümü.");}
        catch(Exception e){say("Ölçüm alınmadı: "+e.getMessage());}}
    private void dimensionsDialog(){
        String[]labels={"İncirin görülen en düşük yüksekliği (mm)","İncirin görülen en yüksek yüksekliği (mm)","Kavrama merkezi: zeminden yükseklik (mm)","Kavrama eğimi (derece)","İncir merkezinin kıskaca yakınlık payı (mm)","Sepette ayrı meyve merkezleri arası mesafe (mm)","İncir zemininin kol taban düzlemine göre yüksekliği (mm)","Sepet merkez X (mm)","Sepet merkez Y (mm)","Sepet iç yarıçapı (mm)","Sepet iç taban Z (mm)","Sepet üst kenar Z (mm)"};
        // Fixed-installation defaults from the user's measured layout; editable before saving.
        double[]defaults={20,40,10,0,15,30,0,-100,100,100,100,150};
        LinearLayout p=ControlUi.column(activity);ScrollView scroll=new ScrollView(activity);scroll.addView(p);EditText[]fields=new EditText[labels.length];double[]current=setup.dimensions();
        for(int i=0;i<labels.length;i++)fields[i]=number(p,labels[i],Double.isFinite(current[i])?current[i]:defaults[i]);
        new AlertDialog.Builder(activity).setTitle("Ölçülen toplama düzeni").setView(scroll).setPositiveButton("Ölçüleri kaydet",(d,n)->{try{setup.configure(values(fields));geometryChanged();say("Toplama düzeni ölçüleri kaydedildi.");}catch(Exception e){say(e.getMessage());}}).setNegativeButton("Vazgeç",null).show();
    }
    private EditText number(LinearLayout parent,String label,double value){ControlUi.text(activity,parent,label,14);EditText e=new EditText(activity);e.setSingleLine(true);e.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL|InputType.TYPE_NUMBER_FLAG_SIGNED);e.setHint("Ölçülmedi");if(Double.isFinite(value))e.setText(String.format(Locale.US,"%.2f",value));parent.addView(e);return e;}
    private void capturePose(String name)throws Exception{requireStationaryPose();setup.capture(name,controller.positions());}
    private void requireStationaryPose()throws Exception{requireController();if(controller.state()==RobotController.State.MOVING||controller.state()==RobotController.State.STOPPING)throw new IllegalStateException("Hareket sürerken pozisyon ölçülemez.");controller.tick(false);for(St3215Protocol.FeedbackState f:controller.feedback().values())if(f.moving()||Math.abs(f.speed())>0)throw new IllegalStateException("Kol tam durmadı; ölçüm alınmadı.");}
    private static double[] values(EditText[]fields){double[]v=new double[fields.length];for(int i=0;i<v.length;i++){String s=fields[i].getText().toString().trim().replace(',','.');if(s.isEmpty())throw new IllegalArgumentException("Ölçülmemiş değerleri doldur.");v[i]=Double.parseDouble(s);if(!Double.isFinite(v[i]))throw new IllegalArgumentException("Sonlu ölçüm gerekli.");}return v;}
    @Override public void close(){stop();planner.shutdownNow();activity.unregisterReceiver(receiver);
        motor.schedule(()->{closed=true;try{if(bus!=null)bus.close();}catch(Exception ignored){}motor.shutdown();},1200,TimeUnit.MILLISECONDS);}
}
