package com.figbot.scanner;

import android.Manifest;
import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbManager;
import android.media.Image;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.MotionEvent;
import android.view.Surface;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.core.content.ContextCompat;

import com.figbot.scanner.so101.ArmProfile;
import com.figbot.scanner.so101.FixedCameraCalibration;
import com.figbot.scanner.so101.FollowBrain;
import com.figbot.scanner.so101.GoalTrajectory;
import com.figbot.scanner.so101.GraspAlignment;
import com.figbot.scanner.so101.GripperSettings;
import com.figbot.scanner.so101.HoldControl;
import com.figbot.scanner.so101.PcServoBus;
import com.figbot.scanner.so101.PickupPlan;
import com.figbot.scanner.so101.PickupCycle;
import com.figbot.scanner.so101.AttemptedTargets;
import com.figbot.scanner.so101.RobotController;
import com.figbot.scanner.so101.ServoBus;
import com.figbot.scanner.so101.So101Kinematics;
import com.figbot.scanner.so101.UsbServoBus;
import com.figbot.scanner.so101.WorkspaceCalibration;
import com.figbot.scanner.so101.WorkSurface;
import com.google.ar.core.ArCoreApk;
import com.google.ar.core.Camera;
import com.google.ar.core.Config;
import com.google.ar.core.Coordinates2d;
import com.google.ar.core.DepthPoint;
import com.google.ar.core.Frame;
import com.google.ar.core.HitResult;
import com.google.ar.core.Plane;
import com.google.ar.core.Pose;
import com.google.ar.core.Session;
import com.google.ar.core.TrackingState;
import com.google.ar.core.exceptions.CameraNotAvailableException;
import com.google.ar.core.exceptions.NotYetAvailableException;
import com.google.ar.core.exceptions.ResourceExhaustedException;
import com.google.ar.core.exceptions.UnavailableException;

import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.json.JSONArray;
import org.json.JSONObject;
import com.figbot.scanner.vision.*;

/**
 * FIGBOT Kol Kontrol — the whole app rewritten around one flow:
 * the camera reports fig positions in robot coordinates (arm to the left of the
 * scene), orange while the camera/vehicle is moving and green once it settles.
 * "Hedefe Git" follows adaptively: orange re-aims at most once per second,
 * green performs one smooth precise leg; arrival is decided from feedback.
 */
public final class KolActivity extends Activity implements GLSurfaceView.Renderer {
    private static final int CAMERA_PERMISSION_REQUEST = 41;
    private static final long INFERENCE_INTERVAL_NS = 250_000_000L;
    private static final long STABILITY_WINDOW_NS = 700_000_000L;
    /** Provisional grip centre height above the confirmed bench plane. */
    // Provisional model value; physical finger centre still needs independent measurement.
    private static final double GRIP_CLEARANCE_MM = 25;
    private static final int[] SPEEDS = {300, 700, 1200};

    /** Raw YOLO detections with the capture time; world points resolve per frame. */
    private record Detections(List<FigDetection> boxes, long capturedNs, Pose pose, int generation) {}
    private record PoseSample(long t, float[] translation, float[] quaternion) {}

    private GLSurfaceView surfaceView;
    private TargetOverlayView overlayView;
    private TextView chip;
    private TextView statusLine;
    private TextView targetLine;
    private TextView markerLine;
    private TextView errorLine;
    private Button holdButton;
    private volatile String lastError = "";
    private boolean awaitingHold;
    private volatile ArucoTracker markerDetector;
    private volatile String markerError = "Etiket algılayıcı hazırlanıyor";
    private final AtomicReference<ArucoTracker.Observation> markerObservation = new AtomicReference<>();
    private volatile int visionGeneration;
    private volatile boolean visionActive;
    private volatile Pose currentCameraPose;
    private SensorManager mountSensors;
    private final FixedMountReference mountReference=new FixedMountReference();
    private final SensorEventListener mountListener=new SensorEventListener(){
        @Override public void onAccuracyChanged(Sensor sensor,int accuracy){}
        @Override public void onSensorChanged(SensorEvent event){
            long now=System.nanoTime();
            if(event.sensor.getType()==Sensor.TYPE_GAME_ROTATION_VECTOR){
                float[] q=new float[4];SensorManager.getQuaternionFromVector(q,event.values);
                mountReference.rotation(q,now);
            }else if(event.sensor.getType()==Sensor.TYPE_LINEAR_ACCELERATION)
                mountReference.acceleration(event.values[0],event.values[1],event.values[2],now);
        }
    };
    private volatile long cameraFrameNs;
    private long lastCameraFrameTimestamp;
    private final CameraReferenceGuard cameraReferenceGuard = new CameraReferenceGuard();
    private volatile boolean cameraReferenceReady;
    private boolean resumeScanLeg;
    private enum PickupPhase { NONE, APPROACHING, SEATING, CLOSING, LIFTING, CARRYING, RELEASING }
    private volatile PickupPhase pickupPhase=PickupPhase.NONE;
    private int[] pickupGoal;
    private PickupCycle pickupCycle;
    private int pickupLeg;
    private int retainedJaw;
    private int pickupSpeed;
    private boolean alignmentCorrectionUsed;
    private boolean graspInPlace;
    private volatile GripperSettings gripperSettings;
    private volatile boolean gripperSettingsReady;
    private final AttemptedTargets attemptedTargets=new AttemptedTargets();
    private boolean attemptedTargetsLoaded;
    private CameraReferenceGuard.State lastReferenceState = CameraReferenceGuard.State.READY;
    private volatile MarkerCalibration.Result markerCalibration;
    private volatile MarkerCalibration.Result savedMarkerCalibration;
    private volatile String calibrationMismatch = "";
    private final CalibrationReuse calibrationReuse=new CalibrationReuse();
    private boolean reuseRejected;
    private RigidPose calibrationToolPrior;
    private volatile Pose calibrationCameraPose;
    private final List<MarkerCalibration.Sample> markerSamples = new ArrayList<>();
    private List<int[]> scanPoses = List.of();
    private ArmProfile scanMotionProfile;
    private boolean autoScan;
    private int[] stableRaw;
    private long stableSince, lastMarkerCapture, scanStarted, scanLegStarted;
    private int stableMarkerFrames;
    private RigidPose lastStableMarker;
    private final StablePoseWindow calibrationWindow = new StablePoseWindow();
    private final StablePoseWindow previewWindow = new StablePoseWindow();
    private final DisplayMemory<ArucoTracker.Observation> markerDisplay = new DisplayMemory<>();
    private final DisplayMemory<Detections> figDisplay = new DisplayMemory<>();
    private volatile boolean markerSteady;
    private volatile boolean trackingActive;
    private volatile boolean worldTrackingActive;
    private volatile long figInferenceMs;
    private long lastVisionLog, markerAttempts, markerSeen, markerClear;
    private boolean markerDiagnostics;
    private TeachingCameraServer teachingCamera;
    private int markerDiagnosticSlot;
    private long lastMarkerRequestNs, lastMarkerImageTimestamp, lastFigImageTimestamp, lastOverlayNs;
    private long heldSince;
    private Button connectButton;
    private Button followButton;
    private Button[] speedButtons = new Button[3];

    private final BackgroundRenderer backgroundRenderer = new BackgroundRenderer();
    private final Handler ui = new Handler(Looper.getMainLooper());
    private Session session;
    private boolean installRequested;
    private boolean cameraTextureBound;
    private CameraControls cameraControls;
    private volatile int surfaceWidth, surfaceHeight;
    private volatile OnnxFigDetector detector;
    private volatile boolean detectorReady;
    private final ExecutorService inferenceExecutor = Executors.newSingleThreadExecutor();
    private final ExecutorService markerExecutor = Executors.newSingleThreadExecutor();
    private final AtomicBoolean markerRunning = new AtomicBoolean();
    private final AtomicBoolean inferenceRunning = new AtomicBoolean();
    private final AtomicReference<Detections> latestDetections = new AtomicReference<>();
    private long lastInferenceRequestNs;
    private final ArrayDeque<PoseSample> poseHistory = new ArrayDeque<>();
    private volatile boolean cameraStable;

    private FixedCameraCalibration fixedCamera;
    private volatile ArmProfile profile;
    private volatile boolean workSurfaceReady;
    private final FollowBrain brain = FollowBrain.standard();

    /** Measured world→robot transform from the 4-tap arm-as-rig calibration. */
    private static final WorkspaceCalibration.Limits CALIBRATION_LIMITS =
            new WorkspaceCalibration.Limits(12, 20, .05, 70, 20, .65);
    private volatile WorkspaceCalibration calibration;
    private final List<WorkspaceCalibration.Sample> calibrationSamples = new ArrayList<>();
    private volatile boolean calibrating;
    private volatile int calibStep;
    private final AtomicReference<float[]> pendingCalibTap = new AtomicReference<>();
    private final ScheduledExecutorService motor =
            Executors.newSingleThreadScheduledExecutor(r -> new Thread(r, "figbot-motor"));
    private final java.util.concurrent.ExecutorService planner=Executors.newSingleThreadExecutor(r->new Thread(r,"figbot-planner"));
    private final AtomicBoolean planning=new AtomicBoolean();
    private final java.util.concurrent.atomic.AtomicLong motionEpoch=new java.util.concurrent.atomic.AtomicLong();
    private volatile MarkerVisibility markerView;
    private long lastRenderDiagnostic;
    private volatile RobotController controller;
    private ServoBus bus;
    private volatile int speedIndex;
    private volatile double[] pendingTarget;
    private volatile String message = "Bağlan → kamerayı incire tut → Hedefe Git.";
    private volatile boolean following;
    private UsbManager usb;
    private static final String USB_PERMISSION = "com.figbot.scanner.KOL_USB";
    private final BroadcastReceiver usbReceiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            if (!USB_PERMISSION.equals(intent.getAction())) return;
            UsbDevice device = intent.getParcelableExtra(UsbManager.EXTRA_DEVICE);
            if (device != null && intent.getBooleanExtra(UsbManager.EXTRA_PERMISSION_GRANTED, false))
                connectUsb(device);
            else say("USB izni verilmedi.");
        }
    };

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        markerDiagnostics=getIntent().getBooleanExtra("marker_diagnostics",false);
        if(getIntent().getBooleanExtra("teaching_camera",false))try{
            teachingCamera=new TeachingCameraServer();
        }catch(java.io.IOException failure){android.util.Log.e("FigbotTeaching","Camera export unavailable",failure);}
        setContentView(R.layout.activity_kol);
        cameraControls=new CameraControls(this);
        usb = (UsbManager) getSystemService(Context.USB_SERVICE);
        mountSensors=(SensorManager)getSystemService(Context.SENSOR_SERVICE);
        surfaceView = findViewById(R.id.surfaceView);
        overlayView = findViewById(R.id.overlay);
        chip = findViewById(R.id.chip);
        statusLine = findViewById(R.id.statusLine);
        targetLine = findViewById(R.id.targetLine);
        markerLine = findViewById(R.id.markerLine);
        errorLine = findViewById(R.id.errorLine);
        holdButton = findViewById(R.id.holdButton);
        lastError = getSharedPreferences("kol_diagnostics", MODE_PRIVATE).getString("last_error", "");
        showLastError();
        errorLine.setOnClickListener(v -> new android.app.AlertDialog.Builder(this)
                .setTitle("Son hata").setMessage(lastError).setPositiveButton("Tamam", null).show());
        statusLine.setOnClickListener(v -> new android.app.AlertDialog.Builder(this)
                .setTitle("Durum").setMessage(message).setPositiveButton("Tamam", null).show());
        connectButton = findViewById(R.id.connectButton);
        followButton = findViewById(R.id.followButton);
        loadAttemptedTargets();
        followButton.setOnLongClickListener(v->{
            new android.app.AlertDialog.Builder(this).setTitle("Toplama seçenekleri")
                    .setItems(new String[]{"Burada kavra ve 5 cm kaldır", "Kıskaç açıklığını ayarla", "Taban yüksekliği", "Denenmiş hedef kaydını temizle", "Kamera mesafesini kontrol et"},(d,w)->{
                        if(w==0)runMotor(this::startGraspInPlace);
                        else if(w==1)showGripperSettings();
                        else if(w==2)showWorkSurface();
                        else if(w==4)showCameraDistanceCheck();
                        else runMotor(()->{
                        requireIdleSetup();
                        attemptedTargets.clear();saveAttemptedTargets();attemptedTargetsLoaded=true;say("Denenmiş konumlar temizlendi.");
                        });
                    }).setNegativeButton("Vazgeç",null).show();return true;
        });
        speedButtons[0] = findViewById(R.id.speedSlow);
        speedButtons[1] = findViewById(R.id.speedMedium);
        speedButtons[2] = findViewById(R.id.speedFast);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        profile = ArmProfile.unverifiedDefaults()
                .withRecordedSessionValidation("RECORDED_SESSION_2026_09_20_21; follow build; no fresh tip measurement")
                // The wrist roll is passive in this app (never commanded); the recorded
                // 46-count window must not veto starting from any in-branch resting pose.
                .withPassiveWristRoll();
        loadWorkSurface();
        loadGripperSettings();
        try (InputStream in = getAssets().open("camera_calibration.json")) {
            fixedCamera = FixedCameraCalibration.fromAsset(in);
        } catch (Exception error) {
            fixedCamera = null;
            say("Kamera kalibrasyonu yüklenemedi: " + error.getMessage());
        }

        loadSavedMarkerCalibration();
        connectButton.setOnClickListener(v -> chooseConnection());
        holdButton.setOnClickListener(v -> chooseHoldAction());
        followButton.setOnClickListener(v -> runMotor(() -> {
            if(!attemptedTargetsLoaded)throw new IllegalStateException("Denenmiş konum kaydı okunamadı; Hedefe Git'e uzun basıp açıkça yeni tur başlat.");
            if(pickupPhase!=PickupPhase.NONE||planning.get())throw new IllegalStateException("Çevrim/hesap sürüyor; durdurmak için DUR.");
            requireController();
            requireWorkSurface();
            requireGripperSettings();
            requireMarkerCalibration();
            if (calibrating) cancelCalibration();
            adoptExistingHold();
            clearLastError();
            pickupPhase=PickupPhase.NONE;
            brain.arm(System.nanoTime());
            following = true; motionEpoch.incrementAndGet();
            followButton.setText("Takip: AÇIK");
            say("Yeni hedef bekleniyor · kilitle, al, sepete bırak; aynı konumu tekrarlama.");
        }));
        findViewById(R.id.stopButton).setOnClickListener(v -> {
            brain.disarm();
            following = false; motionEpoch.incrementAndGet(); pickupPhase=PickupPhase.NONE;
            pendingTarget = null;
            ui.post(() -> followButton.setText("Hedefe Git"));
            runMotor(() -> {
                calibrating = false; autoScan = false;
                if (controller != null) {
                    if(controller.state()==RobotController.State.FAULT_HOLD){controller.acknowledgeHeldFault();clearLastError();say("Hata temizlendi; mevcut tutma doğrulandı. Hareket başlamadı.");}
                    else controller.requestStop();
                }
            });
            say("DUR — mevcut konumda tutma istendi.");
        });
        findViewById(R.id.homeButton).setOnClickListener(v -> runMotor(() -> {
            requireController();
            calibrating = false; autoScan = false;
            adoptExistingHold();
            brain.disarm();
            following = false; motionEpoch.incrementAndGet(); pickupPhase=PickupPhase.NONE;
            pendingTarget = null;
            ui.post(() -> followButton.setText("Hedefe Git"));
            controller.start(GoalTrajectory.moveToHome(profile, controller.positions()));
            say("Kayıtlı başlangıca dönülüyor.");
        }));
        for (int i = 0; i < speedButtons.length; i++) {
            final int index = i;
            speedButtons[i].setOnClickListener(v -> {
                speedIndex = index;
                refreshSpeedUi();
                say(SPEEDS[index] + " sayım/s hız seçildi.");
            });
        }
        findViewById(R.id.calibButton).setOnClickListener(v -> chooseCalibration());
        if(getIntent().getBooleanExtra("teaching_camera",false)){
            connectButton.setEnabled(false);holdButton.setEnabled(false);followButton.setEnabled(false);
            findViewById(R.id.calibButton).setEnabled(false);findViewById(R.id.homeButton).setEnabled(false);
            say(teachingCamera==null?"Öğretim kamerası açılamadı; kayıt başlatılmadı.":"Elle öğretim kamerası açık · kayıt bilgisayardan yönetiliyor.");
        }
        // AR-world coordinates belong to this camera session. Never restore old 4-tap fits.
        refreshSpeedUi();
        ContextCompat.registerReceiver(this, usbReceiver,
                new IntentFilter(USB_PERMISSION), ContextCompat.RECEIVER_NOT_EXPORTED);
        motor.scheduleWithFixedDelay(this::motorTick, 0, 20, TimeUnit.MILLISECONDS);
        markerExecutor.execute(() -> {
            try { markerDetector = new ArucoTracker(); markerError = "ID 0 / 36 mm etiket bekleniyor"; }
            catch (Exception | UnsatisfiedLinkError error) { markerError = "Etiket algılayıcı açılamadı: " + error.getClass().getSimpleName(); }
        });
        inferenceExecutor.execute(() -> {
            try {
                detector = new OnnxFigDetector(getApplicationContext());
                detectorReady = true;
            } catch (Exception error) {
                detectorReady = false;
                say("İncir modeli yüklenemedi: " + error.getClass().getSimpleName());
            }
        });

        surfaceView.setPreserveEGLContextOnPause(true);
        surfaceView.setEGLContextClientVersion(2);
        surfaceView.setRenderer(this);
        surfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
        surfaceView.setOnTouchListener((view, event) -> {
            if (!calibrating || markerDetector != null) {
                if(event.getAction()==MotionEvent.ACTION_UP){cameraControls.show(!cameraControls.visible());view.performClick();}
                return true;
            }
            // Consume DOWN so the gesture stays on this view and UP actually arrives.
            if (event.getAction() == MotionEvent.ACTION_UP) {
                pendingCalibTap.set(new float[]{event.getX(), event.getY()});
                view.performClick();
            }
            return true;
        });
    }

    private void chooseHoldAction() {
        RobotController selected = controller;
        HoldControl.Action action = HoldControl.action(selected);
        if (action != HoldControl.Action.HOLD && action != HoldControl.Action.RELEASE) return;
        boolean release = action == HoldControl.Action.RELEASE;
        new android.app.AlertDialog.Builder(this)
                .setTitle(release ? "Kolu bırak" : "Kolu tut")
                .setMessage(release ? "Kolu alttan destekle. Onaylayınca altı motor serbest kalacak; kolu elle taşıyabileceksin."
                        : "Kolu alttan destekleyip sabit tut. Motorlar bulunduğu konumu tutacak. Ekranda Kol tutuyor yazana kadar desteği koru.")
                .setPositiveButton(release ? "Destekliyorum, bırak" : "Destekliyorum, tut", (d, w) -> runMotor(() -> {
                    if (selected != controller || HoldControl.action(controller) != action)
                        throw new IllegalStateException("Kolun durumu değişti; güncel düğmeye tekrar bas.");
                    brain.disarm(); following = false; motionEpoch.incrementAndGet(); pickupPhase=PickupPhase.NONE; pendingTarget = null;
                    calibrating = false; autoScan = false;
                    ui.post(() -> followButton.setText("Hedefe Git"));
                    if (release) {
                        controller.releaseSupported();
                        awaitingHold = false;
                        say("Motorlar serbest. Kolu destekle; Kalibre → Elle ölçüm ile ölçebilirsin.");
                    } else {
                        establishHold();
                        awaitingHold = controller.state() != RobotController.State.HOLDING;
                        say(awaitingHold ? "Tutma doğrulanıyor; kolu desteklemeye devam et." : "Kol tutuyor — desteği çekebilirsin.");
                    }
                    updateTargetLine(controller);
                }))
                .setNegativeButton("Vazgeç", null).show();
    }

    private String calibrationAvailability(boolean automatic) {
        if(!workSurfaceReady)return "Taban yüksekliği okunamadı; Hedefe Git'e uzun bas → Taban yüksekliği.";
        RobotController c = controller;
        if (c == null) return "Önce motor kartına Bağlan.";
        if (calibrating) return "Ölçüm sürüyor. Yeniden başlatmak için önce DUR.";
        if (c.state() == RobotController.State.MOVING || c.state() == RobotController.State.STOPPING)
            return "Önce DUR; kolun durmasını bekle.";
        if (c.state() == RobotController.State.FAULT_HOLD || c.state() == RobotController.State.FAULT_UNKNOWN)
            return "Motor hatası: " + c.message();
        if (automatic) {
            // Availability must not plan twelve paths on the UI thread every500ms.
            // The selected short/full scan is planned once on the planner worker.
            try { profile.calibrationIngress(c.positions());
                if(new So101Kinematics(profile).forward(c.positions())[2]<profile.groundZMm())
                    return "Model uç masa düzleminin altında; başlangıç duruşu doğrulanmalı.";
            }
            catch (IllegalArgumentException | IllegalStateException e) { return brief(e); }
            if (c.state() != RobotController.State.HOLDING) return "Kolu destekle → Kolu tut.";
        } else if (HoldControl.action(c) != HoldControl.Action.HOLD) {
            return "Kolu destekle → Kolu bırak; sonra Elle ölçüm.";
        }
        ArucoTracker.Observation obs = markerObservation.get();
        if (obs == null || !obs.fresh(System.nanoTime(), visionGeneration)) return "ID 0 etiketinin tamamını kameraya göster.";
        if (!obs.usable()) return obs.measurementProblem();
        if (!cameraStable) return "Telefonu sabit bir yere koy; STABİL yazmasını bekle.";
        return null;
    }

    private void chooseCalibration() {
        android.widget.CheckBox keepMount=new android.widget.CheckBox(this);
        keepMount.setText("Etiketin kola bağlantısı değişmedi");
        keepMount.setChecked(savedMarkerCalibration!=null);keepMount.setEnabled(savedMarkerCalibration!=null);
        android.app.AlertDialog dialog = new android.app.AlertDialog.Builder(this)
                .setTitle("Kamera ile kolu eşle")
                .setMessage("Hazırlık kontrol ediliyor…")
                .setView(keepMount)
                .setPositiveButton("Otomatik hareket", (d, w) -> {boolean keep=keepMount.isChecked();runMotor(() -> beginMarkerCalibration(true,keep));})
                .setNeutralButton("Elle ölçüm", (d, w) -> {boolean keep=keepMount.isChecked();runMotor(() -> beginMarkerCalibration(false,keep));})
                .setNegativeButton("Kapat", null).create();
        Runnable refresh = new Runnable() {
            private String lastText="";
            @Override public void run() {
                if (!dialog.isShowing()) return;
                String automatic = calibrationAvailability(true), manual = calibrationAvailability(false);
                String text="Otomatik: " + (automatic == null ? "Hazır" : automatic)
                        + (keepMount.isChecked()?"\n4 kısa duruş: 2 ölçüm + 2 ayrı kontrol.":"\nİlk kurulum: 12 duruş, farklı yön ve eğimler.")
                        + "\nTelefon sabit, etiket görünür ve kıskaç boş kalmalı."
                        + "\nSonuç kaydedilir; sonraki açılışta kullanılır."
                        + (manual==null?"\nElle ölçüm de hazır; kolu destekli tut.":"");
                if(!text.equals(lastText)){dialog.setMessage(text);lastText=text;}
                String action=keepMount.isChecked()?"Kısa eşle (4 duruş)":"İlk kurulum (12 duruş)";
                if(!action.contentEquals(dialog.getButton(android.app.AlertDialog.BUTTON_POSITIVE).getText()))
                    dialog.getButton(android.app.AlertDialog.BUTTON_POSITIVE).setText(action);
                dialog.getButton(android.app.AlertDialog.BUTTON_POSITIVE).setEnabled(automatic == null);
                dialog.getButton(android.app.AlertDialog.BUTTON_NEUTRAL).setEnabled(manual == null);
                ui.postDelayed(this, 500);
            }
        };
        dialog.setOnShowListener(d -> refresh.run());
        dialog.setOnDismissListener(d -> ui.removeCallbacks(refresh));
        dialog.show();
    }

    // ---------------- Marker calibration ----------------

    private void beginMarkerCalibration(boolean automatic,boolean keepMount) throws Exception {
        requireController();
        requireWorkSurface();
        if(planning.get())throw new IllegalStateException("Hareket hesabı sürüyor; önce DUR veya hesabın bitmesini bekle.");
        if (calibrating) throw new IllegalStateException("Ölçüm sürüyor; önce DUR.");
        ArucoTracker.Observation seen = markerObservation.get();
        if(seen==null || !seen.fresh(System.nanoTime(),visionGeneration) || !seen.usable())
            throw new IllegalStateException(seen==null?"Önce etiketi kameraya net göster.":seen.measurementProblem().isEmpty()?"Taze etiket ölçümü bekleniyor.":seen.measurementProblem());
        if(!cameraStable)throw new IllegalStateException("Telefonu sabitle ve görüntünün kararlı olmasını bekle.");
        if(controller.state()==RobotController.State.MOVING || controller.state()==RobotController.State.STOPPING)
            throw new IllegalStateException("Önce DUR; kol durduktan sonra kalibre et.");
        if(automatic){
            adoptExistingHold();
            final RobotController c=controller;final ArmProfile p=profile;final int[] start=c.positions();
            final int generation=visionGeneration;final long epoch=motionEpoch.incrementAndGet();
            final RigidPose mount=keepMount&&savedMarkerCalibration!=null?savedMarkerCalibration.toolMarker():null;
            final MarkerVisibility view=markerView;
            final So101Kinematics kin=new So101Kinematics(p);
            final RigidPose cameraBase=mount==null?null:seen.cameraMarker().compose(mount.inverse())
                    .compose(RigidPose.fromMatrix(kin.forwardTransform(start)).inverse());
            final double visibleEdge=MarkerVisibility.supportedEdge(seen.imageCorners());
            android.util.Log.i("FigbotCalib","SCAN_INPUT raw="+java.util.Arrays.toString(start)+" view="+view+" edge="+visibleEdge+" initiallyVisible="+(view==null||view.contains(seen.cameraMarker(),visibleEdge))
                    +" cameraR="+java.util.Arrays.deepToString(seen.cameraMarker().rotation())+" cameraT="+java.util.Arrays.toString(seen.cameraMarker().translation()));
            mountReference.armNow();planning.set(true);
            say("Etiketi kadrajda tutan tarama hesaplanıyor; kol bulunduğu konumda tutuyor.");
            planner.execute(()->{
                CalibrationScan.Plan computed=null;Exception problem=null;
                try{
                    java.util.function.Predicate<int[]> visible=q->view==null||cameraBase==null||
                            view.measurable(cameraBase.compose(RigidPose.fromMatrix(kin.forwardTransform(q))).compose(mount),visibleEdge);
                    computed=mount==null?CalibrationScan.plan(p,start,visible):CalibrationScan.planKnownMount(p,start,visible);
                }
                catch(Exception error){problem=error;}
                final CalibrationScan.Plan plan=computed;final Exception failure=problem;
                try{motor.execute(()->{
                    planning.set(false);
                    if(epoch!=motionEpoch.get()||controller!=c||generation!=visionGeneration)return;
                    try{
                        if(failure!=null)throw failure;
                        ArucoTracker.Observation fresh=markerObservation.get();long now=System.nanoTime();
                        if(c.state()!=RobotController.State.HOLDING||rawDifference(start,c.positions())>6
                                ||!mountReference.validNow()||fresh==null||!fresh.fresh(now,generation)||!fresh.usable())
                            throw new IllegalStateException("Tarama hesabı sırasında duruş veya kamera değişti; tekrar kalibre et.");
                        scanPoses=plan.poses();scanMotionProfile=plan.motionProfile();c.setProfile(scanMotionProfile);
                        startMarkerSampling(true,keepMount);
                    }catch(Exception error){reportError(error);}
                });}catch(java.util.concurrent.RejectedExecutionException stopped){planning.set(false);}
            });
            return;
        }else{
            if(controller.state()!=RobotController.State.DISARMED || controller.feedback().values().stream().anyMatch(f->f.torque()!=0))
                throw new IllegalStateException("Elle ölçüm için önce kolu destekle → Kolu bırak. Sonra Kalibre → Elle ölçüm.");
            scanPoses=List.of();
        }
        startMarkerSampling(false,keepMount);
    }

    private void startMarkerSampling(boolean automatic,boolean keepMount) {
        brain.disarm();following=false;motionEpoch.incrementAndGet();pickupPhase=PickupPhase.NONE;pendingTarget=null;lastRobotFrames=new double[0][];
        markerCalibration=null;calibrationMismatch="";calibration=null;markerSamples.clear();stableRaw=null;reuseRejected=true;
        calibrationToolPrior=keepMount&&savedMarkerCalibration!=null?savedMarkerCalibration.toolMarker():null;
        calibrationWindow.clear();stableMarkerFrames=0;lastMarkerCapture=0;calibStep=0;
        calibrationCameraPose=currentCameraPose;
        mountReference.armNow();
        cameraReferenceGuard.reset();cameraReferenceReady=true;resumeScanLeg=false;
        lastReferenceState=CameraReferenceGuard.State.READY;
        autoScan=automatic;scanStarted=scanLegStarted=System.nanoTime();calibrating=true;
        clearLastError();
        ui.post(()->followButton.setText("Hedefe Git"));
        say("Etiket ölçümü 0/"+markerSampleCount()+" · telefonu sabit tut; " + (automatic?"kol yavaş taramaya hazır":"kolu destekle, farklı yön/eğimlerde duraklat"));
    }

    private String calibrationProfileKey(){
        return "opencv-camera-mm-v1;tag=DICT_4X4_50:0:36;"+ArmProfile.VENDOR_URDF_SHA256
                +java.util.Arrays.toString(profile.referenceRaw())+java.util.Arrays.toString(profile.referenceRadians())
                +java.util.Arrays.toString(profile.directionSigns())+java.util.Arrays.toString(profile.offsets());
    }
    private void requireIdleSetup(){
        if(following||planning.get()||pickupPhase!=PickupPhase.NONE||calibrating)
            throw new IllegalStateException("Ayar değiştirmeden önce DUR.");
        if(controller!=null&&controller.state()!=RobotController.State.HOLDING
                &&controller.state()!=RobotController.State.DISARMED)
            throw new IllegalStateException("Önce motor durumu doğrulanmalı.");
    }
    private double gripZMm(){return profile.groundZMm()+GRIP_CLEARANCE_MM;}
    private void requireWorkSurface(){
        if(!workSurfaceReady)throw new IllegalStateException("Taban yüksekliği geçersiz; Hedefe Git'e uzun bas → Taban yüksekliği.");
    }
    private void loadWorkSurface(){
        try{
            WorkSurface surface=WorkSurface.fromCentimeters(getSharedPreferences("work_surface",MODE_PRIVATE)
                    .getString("base_height_cm","0"));
            profile=profile.withGroundZMm(surface.groundZMm());workSurfaceReady=true;
        }catch(RuntimeException invalid){workSurfaceReady=false;reportError(invalid);}
    }
    private void showWorkSurface(){
        android.widget.EditText input=new android.widget.EditText(this);
        input.setInputType(android.text.InputType.TYPE_CLASS_NUMBER|android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        input.setSingleLine(true);
        input.setText(String.format(Locale.US,"%.1f",-profile.groundZMm()/10));
        input.selectAll();
        android.app.AlertDialog dialog=new android.app.AlertDialog.Builder(this)
                .setTitle("Taban yüksekliği (cm)")
                .setMessage("İncirin durduğu yüzeyden beyaz tabanın altına kadar dikey mesafe. Aynı seviyedeyse 0. Bir kez kaydedilir; kamera kalibrasyonu korunur.")
                .setView(input).setPositiveButton("Kaydet",null).setNegativeButton("Vazgeç",null).create();
        dialog.setOnShowListener(d->dialog.getButton(android.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
            final WorkSurface measured;
            try{measured=WorkSurface.fromCentimeters(input.getText().toString());requireIdleSetup();}
            catch(RuntimeException invalid){input.setError(invalid.getMessage());return;}
            runMotor(()->{
                requireIdleSetup();ArmProfile next=profile.withGroundZMm(measured.groundZMm());
                if(!getSharedPreferences("work_surface",MODE_PRIVATE).edit()
                        .putString("base_height_cm",Double.toString(measured.baseHeightMm()/10)).commit())
                    throw new IllegalStateException("Taban yüksekliği kaydedilemedi.");
                if(controller!=null)controller.setProfile(next);
                profile=next;workSurfaceReady=true;pendingTarget=null;lastRobotFrames=new double[0][];
                latestDetections.set(null);brain.disarm();motionEpoch.incrementAndGet();
                android.util.Log.i("FigbotPickup","WORK_SURFACE groundZ="+next.groundZMm()+" gripZ="+gripZMm());
                say(String.format(Locale.US,"Taban %.1f cm · masa Z %.0f mm. Kaydedildi; hareket başlamadı.",measured.baseHeightMm()/10,next.groundZMm()));
                ui.post(dialog::dismiss);
            });
        }));
        dialog.show();
    }
    private void requireGripperSettings(){
        if(!gripperSettingsReady)throw new IllegalStateException("Kıskaç ayarı okunamadı; Hedefe Git'e uzun bas → Kıskaç açıklığını ayarla.");
    }
    private android.util.AtomicFile gripperFile(){return new android.util.AtomicFile(new java.io.File(getFilesDir(),"gripper_settings.record"));}
    private void loadGripperSettings(){
        try{
            try{gripperSettings=GripperSettings.decode(profile,new String(gripperFile().readFully(),java.nio.charset.StandardCharsets.UTF_8));}
            catch(java.io.FileNotFoundException absent){gripperSettings=GripperSettings.compatibility(profile);}
            profile=gripperSettings.apply(profile);gripperSettingsReady=true;
        }catch(Exception invalid){gripperSettingsReady=false;reportError(new IllegalStateException("Kıskaç ayarı geçersiz; açıklığı yeniden seç.",invalid));}
    }
    private void saveGripperSettings(GripperSettings settings) throws Exception {
        requireIdleSetup();ArmProfile replacement=settings.apply(profile);
        android.util.AtomicFile file=gripperFile();java.io.FileOutputStream out=null;
        try{out=file.startWrite();out.write(settings.encode().getBytes(java.nio.charset.StandardCharsets.UTF_8));file.finishWrite(out);}
        catch(Exception error){if(out!=null)file.failWrite(out);throw error;}
        if(controller!=null)controller.setProfile(replacement);
        profile=replacement;gripperSettings=settings;gripperSettingsReady=true;
        say("Kıskaç ayarı kaydedildi: kapalı "+settings.closed()+" / açık "+settings.open()+". Hareket başlatılmadı.");
    }
    private void showGripperSettings(){
        String description="Açıklık motor sayımıdır; kuvvet veya milimetre ölçümü değildir. Ayar seçmek kolu hareket ettirmez.\n\n"
                +(gripperSettingsReady?"Kapalı "+gripperSettings.closed()+" · açık "+gripperSettings.open():"Kayıt geçersiz")
                +"\n20 Eylül kaydı: 780 / 1153; o gün incir kaldırıldı, bugünkü kavrama henüz doğrulanmadı.";
        new android.app.AlertDialog.Builder(this).setTitle("Kıskaç açıklığı").setMessage(description)
                .setPositiveButton("Ayar seç",(d,w)->new android.app.AlertDialog.Builder(this).setTitle("Kıskaç ayarını kaydet")
                        .setItems(new String[]{"20 Eylül kavrama kaydı: 780 / 1153", "Şu anki açıklığı kapalı olarak kaydet", "Şu anki açıklığı açık olarak kaydet", "Önceki uygulama ayarı: 870 / 1153"},(dialog,index)->runMotor(()->{
                            requireIdleSetup();
                            if(index==0)saveGripperSettings(GripperSettings.historical(profile));
                            else if(index==3)saveGripperSettings(GripperSettings.from(profile,870,1153,"LEGACY_APP_COMMAND; aperture unmeasured"));
                            else{
                                requireController();controller.tick(true);requireIdleSetup();int jaw=controller.positions()[5];
                                if(controller.feedback().values().stream().anyMatch(f->f.moving()||Math.abs(f.speed())>5))
                                    throw new IllegalStateException("Konumu kaydetmeden önce kol sabit kalmalı.");
                                saveGripperSettings(GripperSettings.from(profile,index==1?jaw:profile.gripperClosed(),
                                        index==2?jaw:profile.gripperOpen(),"OPERATOR_CAPTURED_ENCODER; force/aperture unmeasured"));
                            }
                        })).setNegativeButton("Vazgeç",null).show())
                .setNegativeButton("Kapat",null).show();
    }
    /** Read-only optical scale check, independent of AR depth and the arm model. */
    private void showCameraDistanceCheck(){
        android.app.AlertDialog dialog=new android.app.AlertDialog.Builder(this)
                .setTitle("Kamera mesafesi · etiket kontrolü")
                .setMessage("Etiket ölçümü bekleniyor")
                .setPositiveButton("Kapat",null).create();
        Runnable refresh=new Runnable(){@Override public void run(){
            if(!dialog.isShowing())return;
            ArucoTracker.Observation obs=markerObservation.get();
            String reading="Etiketin tamamını kameraya göster; net ölçüm bekleniyor.";
            if(obs!=null&&obs.fresh(System.nanoTime(),visionGeneration)&&obs.usable()&&markerSteady){
                double range=obs.cameraMarker().distance(RigidPose.identity());
                reading=String.format(Locale.US,"Kamera → etiket merkezi: %.1f cm\nOptik eksen boyunca: %.1f cm\nGörüş açısı: %.0f° · ölçüme uygun\n",
                        range/10,obs.cameraMarker().translation()[2]/10,obs.quality().incidenceDegrees());
            }else if(obs!=null&&obs.fresh(System.nanoTime(),visionGeneration)&&!obs.usable()){
                reading=obs.measurementProblem();
            }
            dialog.setMessage(reading+"\nSiyah dış kare 36 × 36 mm olmalı (kağıt kenarı değil).\n\n"
                    +"Cetvelle kamera merceğinden etiket merkezine olan düz mesafeyi karşılaştır. "
                    +"Bu ölçüm kamera hareketi veya motor bağlantısı gerektirmez.\n\n"
                    +"Etiket mesafesidir; incirin mesafesi veya kavrama doğruluğu değildir.");
            ui.postDelayed(this,250);
        }};
        dialog.setOnDismissListener(d->ui.removeCallbacks(refresh));
        dialog.show();ui.post(refresh);
    }
    private android.util.AtomicFile calibrationFile(){
        return new android.util.AtomicFile(new java.io.File(getFilesDir(),"marker_calibration.record"));
    }
    private android.util.AtomicFile attemptedTargetsFile(){return new android.util.AtomicFile(new java.io.File(getFilesDir(),"attempted_targets.json"));}
    private void loadAttemptedTargets(){
        try{
            JSONArray data=new JSONArray(new String(attemptedTargetsFile().readFully(),java.nio.charset.StandardCharsets.UTF_8));
            for(int i=0;i<data.length();i++){JSONArray p=data.getJSONArray(i);attemptedTargets.add(new double[]{p.getDouble(0),p.getDouble(1)});}
            attemptedTargetsLoaded=true;
        }catch(java.io.FileNotFoundException absent){attemptedTargetsLoaded=true;}
        catch(Exception error){attemptedTargetsLoaded=false;android.util.Log.e("FigbotPickup","Attempt history unreadable",error);}
    }
    private void saveAttemptedTargets() throws Exception {
        JSONArray data=new JSONArray();for(double[] p:attemptedTargets.snapshot())data.put(new JSONArray(p));
        android.util.AtomicFile file=attemptedTargetsFile();java.io.FileOutputStream out=null;
        try{out=file.startWrite();out.write(data.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));file.finishWrite(out);}
        catch(Exception error){if(out!=null)file.failWrite(out);throw error;}
    }
    private void loadSavedMarkerCalibration(){
        try{
            savedMarkerCalibration=CalibrationRecord.decode(new String(calibrationFile().readFully(),java.nio.charset.StandardCharsets.UTF_8),calibrationProfileKey());
            say("Kayıtlı kalibrasyon bulundu; Bağlan ile etiket ve mevcut duruş doğrulanacak.");
        }catch(java.io.FileNotFoundException absent){savedMarkerCalibration=null;}
        catch(Exception invalid){savedMarkerCalibration=null;android.util.Log.w("FigbotCalib","Saved calibration rejected",invalid);}
    }
    private void saveMarkerCalibration(MarkerCalibration.Result result) throws Exception {
        android.util.AtomicFile file=calibrationFile();java.io.FileOutputStream output=null;
        try{
            byte[] bytes=CalibrationRecord.encode(result,calibrationProfileKey()).getBytes(java.nio.charset.StandardCharsets.UTF_8);
            output=file.startWrite();output.write(bytes);file.finishWrite(output);
            savedMarkerCalibration=result;reuseRejected=false;
        }catch(Exception error){if(output!=null)file.failWrite(output);throw error;}
    }
    private void restoreMarkerCalibration(RobotController c,long now){
        if(calibrating||savedMarkerCalibration==null)return;
        if(pickupPhase!=PickupPhase.NONE||c.state()!=RobotController.State.HOLDING&&c.state()!=RobotController.State.DISARMED){calibrationReuse.reset();return;}
        ArucoTracker.Observation obs=markerObservation.get();
        if(!visionActive||!trackingActive||now-cameraFrameNs>CameraReferenceGuard.MAX_FRAME_AGE_NS
                ||!mountReference.settledNow()||obs==null||!obs.fresh(now,visionGeneration)||!obs.usable()
                ||c.state()==RobotController.State.HOLDING&&obs.capturedNs()<=heldSince+150_000_000L
                ||c.feedback().values().stream().anyMatch(f->Math.abs(f.speed())>5||f.moving())){
            calibrationReuse.reset();return;
        }
        RigidPose model=RigidPose.fromMatrix(new So101Kinematics(profile).forwardTransform(c.positions()));
        CalibrationReuse.State status=calibrationReuse.observe(savedMarkerCalibration,model,obs.cameraMarker(),obs.capturedNs(),now);
        if(status==CalibrationReuse.State.MATCH){
            if(markerCalibration!=null&&cameraAtCalibrationPose())return;
            mountReference.armNow();cameraReferenceGuard.reset();cameraReferenceReady=true;lastReferenceState=CameraReferenceGuard.State.READY;
            markerCalibration=savedMarkerCalibration;reuseRejected=false;calibrationMismatch="";clearLastError();
            say(String.format(Locale.US,"Kayıtlı kalibrasyon doğrulandı · kontrol %.1f mm · yeniden tarama gerekmedi.",markerCalibration.heldRmsMm()));
            android.util.Log.i("FigbotCalib","RESTORED_WITH_FRESH_MARKER_AND_ENCODERS");
        }else if(status==CalibrationReuse.State.MISMATCH){
            if(markerCalibration!=null){
                markerCalibration=null;cameraReferenceReady=false;following=false;
                pendingTarget=null;motionEpoch.incrementAndGet();brain.disarm();c.requestStop();
                ui.post(()->followButton.setText("Hedefe Git"));
            }
            if(reuseRejected)return;
            RigidPose observed=savedMarkerCalibration.observedTool(obs.cameraMarker());
            String reason=String.format(Locale.US,"Etiket ile kol modeli uyuşmuyor: %.1f mm / %.1f°. Kayıt korundu. Bu ölçüm tek başına telefonun oynadığını göstermez; uç geometrisi, motor konumu veya görüntü ölçümü incelenmeli.",observed.distance(model),Math.toDegrees(observed.angle(model)));
            calibrationMismatch=reason;
            reuseRejected=true;say(reason);android.util.Log.i("FigbotCalib",reason);
        }
    }

    private void requireMarkerCalibration(){
        ArucoTracker.Observation obs=markerObservation.get();
        if(markerCalibration==null || obs==null || !obs.fresh(System.nanoTime(),visionGeneration) || !obs.usable())
            throw new IllegalStateException(markerCalibration==null&&!calibrationMismatch.isEmpty()?calibrationMismatch:
                    savedMarkerCalibration!=null?"Kayıt var; güncel etiket ve kol duruşu henüz doğrulanmadı.":"Etiketle kalibrasyon ve güncel, net etiket görüntüsü gerekli.");
        if(!cameraReferenceReady||!cameraAtCalibrationPose())throw new IllegalStateException("Kamera referansı henüz doğrulanmadı; takibin toparlanmasını bekle.");
    }
    private boolean cameraAtCalibrationPose(){
        return visionActive&&trackingActive&&System.nanoTime()-cameraFrameNs<=CameraReferenceGuard.MAX_FRAME_AGE_NS
                &&mountReference.validNow();
    }

    private void markerCalibrationTick(RobotController c,long now) throws Exception {
        if(!calibrating)return;
        if(c.state()==RobotController.State.FAULT_HOLD||c.state()==RobotController.State.FAULT_UNKNOWN)throw new IllegalStateException("Motor hatası; kalibrasyon iptal.");
        if(now-scanStarted>180_000_000_000L)throw new IllegalStateException("Kalibrasyon süresi doldu; yeniden başlat.");
        if(autoScan&&now-scanLegStarted>15_000_000_000L)throw new IllegalStateException("Bu duruşta 15 sn boyunca kararlı etiket ölçülemedi. Etiketin tamamını göster; telefonu sabit tut ve tekrar başlat.");
        if(!cameraReferenceReady){
            stableRaw=null;calibrationWindow.clear();stableMarkerFrames=0;return;
        }
        if(c.state()==RobotController.State.MOVING||c.state()==RobotController.State.STOPPING){
            stableRaw=null;calibrationWindow.clear();stableMarkerFrames=0;return;
        }
        int[]raw=c.positions();
        if(resumeScanLeg){
            if(c.state()!=RobotController.State.HOLDING)return;
            // Replan the interrupted leg from measured hold, never sample the halfway pose.
            c.start(GoalTrajectory.moveTo(scanMotionProfile,raw,scanPoses.get(calibStep),300));
            resumeScanLeg=false;stableRaw=null;calibrationWindow.clear();return;
        }
        boolean still=c.feedback().values().stream().allMatch(f->Math.abs(f.speed())<=5&&!f.moving());
        if(stableRaw==null||!still||rawDifference(stableRaw,raw)>3){
            stableRaw=raw.clone();stableSince=now;calibrationWindow.clear();stableMarkerFrames=0;return;
        }
        ArucoTracker.Observation obs=markerObservation.get();
        // Missing/ambiguous frames are skipped, not converted into measurements and not
        // allowed to erase a stationary encoder interval. Old samples expire in the window.
        if(obs==null||!obs.fresh(now,visionGeneration)||!obs.usable()||obs.capturedNs()<cameraReferenceGuard.acceptAfterNs())return;
        if(now-stableSince<700_000_000L||obs.capturedNs()<stableSince+250_000_000L||obs.capturedNs()==lastMarkerCapture)return;
        lastMarkerCapture=obs.capturedNs();
        calibrationWindow.add(obs.capturedNs(),visionGeneration,obs.cameraMarker());
        stableMarkerFrames=calibrationWindow.size();
        RigidPose measured=calibrationWindow.result(now,visionGeneration);
        if(measured==null)return;
        RigidPose fk=RigidPose.fromMatrix(new So101Kinematics(profile).forwardTransform(raw));
        for(MarkerCalibration.Sample old:markerSamples)
            if(old.baseTool().distance(fk)<15&&old.baseTool().angle(fk)<Math.toRadians(5))return;
        markerSamples.add(new MarkerCalibration.Sample(fk,measured));calibStep=markerSamples.size();
        JSONObject trace=new JSONObject().put("sample",calibStep).put("raw",new JSONArray(raw))
                .put("baseR",new JSONArray(fk.rotation())).put("baseT",new JSONArray(fk.translation()))
                .put("cameraR",new JSONArray(measured.rotation())).put("cameraT",new JSONArray(measured.translation()));
        android.util.Log.i("FigbotCalib",trace.toString());
        stableRaw=null;calibrationWindow.clear();stableMarkerFrames=0;
        int fitCount=calibrationToolPrior==null?MarkerCalibration.FIT_COUNT:MarkerCalibration.KNOWN_MOUNT_FIT_COUNT;
        say("Etiket ölçümü "+calibStep+"/"+markerSampleCount()+" · "+(calibStep<fitCount?"öğrenme": "bağımsız kontrol")+(autoScan?"":"; kolun yerini ve eğimini değiştir"));
        if(calibStep==markerSampleCount()){
            MarkerCalibration.Result result=calibrationToolPrior==null
                    ?MarkerCalibration.fit(List.copyOf(markerSamples))
                    :MarkerCalibration.fitKnownMount(List.copyOf(markerSamples),calibrationToolPrior);
            saveMarkerCalibration(result);
            markerCalibration=result;calibrationMismatch="";calibrating=false;autoScan=false; // Keep the original camera reference.
            say(String.format(Locale.US,"Etiket kalibrasyonu hazır · kontrol RMS %.1f mm / en çok %.1f mm. Hedefe Git ile dene.",result.heldRmsMm(),result.heldMaxMm()));
            return;
        }
        if(autoScan){
            c.start(GoalTrajectory.moveTo(scanMotionProfile,raw,scanPoses.get(calibStep),300));scanLegStarted=now;
        }
    }
    private static int rawDifference(int[]a,int[]b){int max=0;for(int i=0;i<5;i++)max=Math.max(max,Math.abs(a[i]-b[i]));return max;}
    private int markerSampleCount(){return calibrationToolPrior==null?MarkerCalibration.TOTAL_COUNT:MarkerCalibration.KNOWN_MOUNT_TOTAL_COUNT;}

    private void startCalibration() {
        brain.disarm();
        following = false; motionEpoch.incrementAndGet(); pickupPhase=PickupPhase.NONE;
        pendingTarget = null;
        ui.post(() -> followButton.setText("Hedefe Git"));
        synchronized (calibrationSamples) {
            calibrationSamples.clear();
        }
        calibStep = 0;
        calibrating = true;
        say("Kalibrasyon 1/4 · kolun kıskaç ucunu ekranda uca dokunarak işaretle.");
    }

    private void cancelCalibration() {
        calibrating = false;
        pendingCalibTap.set(null);
        say("Kalibrasyon iptal; mevcut ölçümler korundu.");
    }

    private void processCalibTap(Frame frame) {
        float[] tap = pendingCalibTap.getAndSet(null);
        if (tap == null || !calibrating) return;
        float[] world = hitWorld(frame, tap[0], tap[1]);
        if (world == null) {
            say("Dokunuşta derinlik bulunamadı — ucu görünür tut ve yeniden dokun.");
            return;
        }
        double[] worldM = {world[0], world[1], world[2]};
        runMotor(() -> recordCalibrationSample(worldM));
    }

    private void recordCalibrationSample(double[] worldM) throws Exception {
        requireController();
        double[] fk = new So101Kinematics(profile).forward(controller.positions());
        double[] robotMm = java.util.Arrays.copyOf(fk, 3);
        synchronized (calibrationSamples) {
            calibrationSamples.add(new WorkspaceCalibration.Sample(
                    UUID.randomUUID().toString(), worldM, robotMm));
            calibStep = calibrationSamples.size();
        }
        if (calibStep < 4) {
            say("Kalibrasyon " + calibStep + "/4 · kolu ≥8 cm uzak, aynı çizgide olmayan bir yere taşı ve uca dokun.");
            return;
        }
        List<WorkspaceCalibration.Sample> samples;
        synchronized (calibrationSamples) {
            samples = List.copyOf(calibrationSamples);
        }
        try {
            WorkspaceCalibration fitted = WorkspaceCalibration.fit(samples, CALIBRATION_LIMITS);
            calibration = fitted;
            calibrating = false;
            saveCalibration(samples);
            WorkspaceCalibration.Residuals r = fitted.fitResiduals();
            say(String.format(Locale.US,
                    "Kalibrasyon tamam · ortalama hata %.1f mm (en çok %.1f mm) · Hedefe Git hazır.",
                    r.rmsMm, r.maxMm));
        } catch (Exception badFit) {
            synchronized (calibrationSamples) {
                calibrationSamples.clear();
            }
            calibStep = 0;
            say("Kalibrasyon tutmadı (" + brief(badFit)
                    + "). Noktalar ≥8 cm ayrık ve kol sabit duruyken uca dokunduğundan emin ol; yeniden dene.");
        }
    }

    private void saveCalibration(List<WorkspaceCalibration.Sample> samples) {
        try {
            JSONArray array = new JSONArray();
            for (WorkspaceCalibration.Sample s : samples)
                array.put(new JSONObject()
                        .put("id", s.id)
                        .put("world_m", new JSONArray(s.worldMetres()))
                        .put("robot_mm", new JSONArray(s.robotMm())));
            getPreferences(MODE_PRIVATE).edit().putString("calibration", array.toString()).apply();
        } catch (Exception ignored) {
            // A failed preference write must not disable the in-memory calibration.
        }
    }

    private void loadCalibration() {
        try {
            String raw = getPreferences(MODE_PRIVATE).getString("calibration", "");
            if (raw.isEmpty()) {
                say("Kamera kalibrasyonu yok — önce KALİBRE (4 dokunuş) yap.");
                return;
            }
            List<WorkspaceCalibration.Sample> samples = new ArrayList<>();
            JSONArray array = new JSONArray(raw);
            for (int i = 0; i < array.length(); i++) {
                JSONObject item = array.getJSONObject(i);
                samples.add(new WorkspaceCalibration.Sample(item.getString("id"),
                        doubles(item.getJSONArray("world_m")), doubles(item.getJSONArray("robot_mm"))));
            }
            calibration = WorkspaceCalibration.fit(samples, CALIBRATION_LIMITS);
            WorkspaceCalibration.Residuals r = calibration.fitResiduals();
            say(String.format(Locale.US, "Kayıtlı kalibrasyon yüklendi · ortalama hata %.1f mm.", r.rmsMm));
        } catch (Exception ignored) {
            say("Kayıtlı kalibrasyon bozuk — KALİBRE ile yeniden ölç.");
        }
    }

    private static double[] doubles(JSONArray array) throws Exception {
        double[] values = new double[array.length()];
        for (int i = 0; i < values.length; i++) values[i] = array.getDouble(i);
        return values;
    }

    /** Measured calibration first; the bundled fixed-mount estimate is only a fallback. */
    private double[] toRobot(double[] worldM,Pose frameCamera) {
        MarkerCalibration.Result marker=markerCalibration;
        if(marker==null||!cameraReferenceReady||!cameraAtCalibrationPose())return null;
        float[] matrix=new float[16];frameCamera.toMatrix(matrix,0);
        double[][] r=new double[3][3];double[] t=new double[3];
        for(int i=0;i<3;i++){t[i]=matrix[12+i]*1000;for(int j=0;j<3;j++)r[i][j]=matrix[j*4+i];}
        double[] cameraMm=CameraCoordinates.fromWorld(new RigidPose(r,t),new double[]{worldM[0]*1000,worldM[1]*1000,worldM[2]*1000});
        return marker.baseWorld().map(cameraMm);
    }

    private interface MotorWork { void run() throws Exception; }

    private void runMotor(MotorWork work) {
        motor.execute(() -> {
            try {
                work.run();
            } catch (Exception error) {
                reportError(error);
            }
        });
    }

    private void requireController() {
        if (controller == null) throw new IllegalStateException("Önce Bağlan.");
    }

    /**
     * Reaches HOLDING from DISARMED, tolerating momentary base drift while the
     * torque is still off: a free ST3215 base spins with the lightest touch, so a
     * single "not stationary" snapshot must not block activation. Pre-write check
     * failures keep the state DISARMED and are simply retried.
     * Torque enable (holdSupportedPose) is allowed here because the caller is the
     * explicit "Kolu tut" button: the user declares physical support.
     */
    private void establishHold() throws Exception {
        RobotController c = controller;
        requireController();
        if (c.state() == RobotController.State.HOLDING) return;
        if (c.state() != RobotController.State.DISARMED)
            throw new IllegalStateException("Kol durumu " + c.state() + "; "+c.faultReason()+". "+(c.state()==RobotController.State.FAULT_HOLD?"DUR ile mevcut tutmayı doğrula.":"Bağlantı ve duruş doğrulanmalı."));
        String last = "";
        for (int attempt = 0; attempt < 10; attempt++) {
            try {
                c.attachExistingHold();
                return;
            } catch (Exception retry) {
                last = brief(retry);
            }
            try {
                c.holdSupportedPose();
                return;
            } catch (Exception retry) {
                if (c.state() != RobotController.State.DISARMED)
                    throw retry;   // activation began; the state machine must run
                last = brief(retry);
            }
            Thread.sleep(250);
        }
        throw new IllegalStateException("Motorlar 2,5 sn içinde durmadı (" + last
                + "). Kolu elinle sabit tut ve tekrar bas; taban serbest dönmesin. Sürerse 12 V beslemeyi kapat-aç.");
    }

    /** Attach-only: adopts an already-powered hold; never enables torque by itself. */
    private void adoptExistingHold() throws Exception {
        RobotController c = controller;
        requireController();
        if (c.state() == RobotController.State.HOLDING) return;
        if (c.state() != RobotController.State.DISARMED)
            throw new IllegalStateException("Kol durumu " + c.state() + "; önce DUR ile sıfırla.");
        String last = "";
        for (int attempt = 0; attempt < 8; attempt++) {
            try {
                c.attachExistingHold();
                return;
            } catch (Exception retry) {
                last = brief(retry);
            }
            Thread.sleep(200);
        }
        throw new IllegalStateException("Mevcut tutma devralınamadı (" + last
                + "). Motor torku kapalıysa kolu destekle → Kolu tut.");
    }

    private static String brief(Exception error) {
        return error.getMessage() == null ? error.getClass().getSimpleName() : error.getMessage();
    }

    private void say(String text) {
        message = text;
        ui.post(() -> statusLine.setText(text));
    }

    private void reportError(Exception error) {
        String text = brief(error);
        RobotController c=controller;
        if(c!=null&&!c.faultReason().isEmpty()&&(c.state()==RobotController.State.FAULT_HOLD||c.state()==RobotController.State.FAULT_UNKNOWN||c.state()==RobotController.State.STOPPING))
            text=c.faultReason()+" · "+text;
        say(text);
        if (text.equals(lastError)) return;
        lastError = text;
        android.util.Log.e("FigbotKol", text, error);
        try(java.io.FileWriter history=new java.io.FileWriter(new java.io.File(getFilesDir(),"motor_errors.log"),true)){
            history.write(System.currentTimeMillis()+" phase="+pickupPhase+" leg="+pickupLeg+" "+text+"\n");
        }catch(java.io.IOException ignored){}
        getSharedPreferences("kol_diagnostics", MODE_PRIVATE).edit().putString("last_error", text).apply();
        ui.post(this::showLastError);
    }

    private void showLastError() {
        errorLine.setText(lastError.isEmpty() ? "" : "SON HATA: " + lastError + " (ayrıntı için dokun)");
        errorLine.setVisibility(lastError.isEmpty() ? android.view.View.GONE : android.view.View.VISIBLE);
    }

    private void clearLastError() {
        lastError = "";
        getSharedPreferences("kol_diagnostics", MODE_PRIVATE).edit().remove("last_error").apply();
        ui.post(this::showLastError);
    }

    private void refreshSpeedUi() {
        for (int i = 0; i < speedButtons.length; i++) {
            boolean on = i == speedIndex;
            speedButtons[i].setBackgroundResource(on ? R.drawable.bg_btn_go : R.drawable.bg_btn_neutral);
        }
    }

    // ---------------- Connection ----------------

    private void chooseConnection() {
        if(getIntent().getBooleanExtra("teaching_camera",false)){
            say("Elle öğretimde motor bağlantısını bilgisayar yönetiyor.");return;
        }
        String[] options = {"PC köprüsü (PC_Uzerinden_Toplama.cmd açık)", "USB direkt (telefon–OTG–motor kartı)"};
        new android.app.AlertDialog.Builder(this)
                .setTitle("Bağlantı türü")
                .setItems(options, (dialog, which) -> {
                    if (which == 0) runMotor(this::connectPc);
                    else pickUsbDevice();
                })
                .show();
    }

    private void connectPc() throws Exception {
        openBus(PcServoBus.open());
    }

    private void pickUsbDevice() {
        List<UsbDevice> devices = new ArrayList<>(usb.getDeviceList().values());
        if (devices.isEmpty()) {
            say("USB kartı görünmüyor; telefonu OTG kabloyla motor kartına bağla.");
            return;
        }
        if (devices.size() == 1) {
            requestUsb(devices.get(0));
            return;
        }
        String[] names = devices.stream()
                .map(d -> String.format(Locale.US, "%s · %04X:%04X", d.getProductName(), d.getVendorId(), d.getProductId()))
                .toArray(String[]::new);
        new android.app.AlertDialog.Builder(this)
                .setTitle("Motor kartını seç")
                .setItems(names, (dialog, which) -> requestUsb(devices.get(which)))
                .show();
    }

    private void requestUsb(UsbDevice device) {
        if (usb.hasPermission(device)) {
            connectUsb(device);
            return;
        }
        android.app.PendingIntent pi = android.app.PendingIntent.getBroadcast(this, 0,
                new Intent(USB_PERMISSION).setPackage(getPackageName()),
                android.app.PendingIntent.FLAG_UPDATE_CURRENT | android.app.PendingIntent.FLAG_IMMUTABLE);
        usb.requestPermission(device, pi);
    }

    private void connectUsb(UsbDevice device) {
        runMotor(() -> openBus(UsbServoBus.open(usb, device)));
    }

    private void openBus(ServoBus candidate) throws Exception {
        if (controller != null) {
            candidate.close();
            throw new IllegalStateException("Zaten bağlı; önce bağlantıyı kes.");
        }
        try {
            RobotController fresh = new RobotController(candidate, profile, System::nanoTime);
            fresh.connectReadOnly();
            bus = candidate;
            controller = fresh;
            say("Altı motor okundu · tutma devralınıyor…");
            try {
                adoptExistingHold();
                clearLastError();
                say("Kol bağlı ve tutuyor · önce Kalibre ile kamera eşlemesini yap.");
            } catch (Exception noHold) {
                say("Bağlı, tutma yok (" + brief(noHold)
                        + "). Kolu destekle → Kolu tut'a bas.");
            }
            ui.post(() -> connectButton.setText("Bağlantıyı kes"));
            connectButton.setOnClickListener(v -> disconnect());
        } catch (Exception error) {
            try {
                candidate.close();
            } catch (Exception ignored) {
            }
            throw error;
        }
    }

    private void disconnect() {
        runMotor(() -> {
            brain.disarm();
            following = false; motionEpoch.incrementAndGet(); pickupPhase=PickupPhase.NONE;
            if (controller != null) controller.requestStop();
            calibrating = false; autoScan = false; awaitingHold = false; pendingTarget = null;
            controller = null;
            if (bus != null) {
                bus.close();
                bus = null;
            }
            say("Bağlantı kesildi.");
            ui.post(() -> {
                connectButton.setText("Bağlan");
                connectButton.setOnClickListener(v -> chooseConnection());
                followButton.setText("Hedefe Git");
            });
        });
    }

    // ---------------- Motor loop ----------------

    private void motorTick() {
        RobotController c = controller;
        long now = System.nanoTime();
        try {
            if (c != null) {
                Detections snapshot = latestDetections.get();
                boolean fresh = snapshot != null && snapshot.generation()==visionGeneration && ObservationTiming.fresh(snapshot.capturedNs(), now);
                ArucoTracker.Observation mo=markerObservation.get();
                boolean markerFresh=mo!=null&&mo.fresh(now,visionGeneration)&&mo.usable();
                if(!calibrating&&markerCalibration!=null&&!mountReference.validNow()){
                    // A moved assembly may keep its extrinsics, but its old fruit
                    // goal must never resume just because the relative fit matches.
                    c.requestStop();following=false;pickupPhase=PickupPhase.NONE;
                    pendingTarget=null;motionEpoch.incrementAndGet();brain.disarm();
                    markerCalibration=null;cameraReferenceReady=false;
                    calibrationReuse.reset();reuseRejected=false;lastRobotFrames=new double[0][];
                    ui.post(()->followButton.setText("Hedefe Git"));
                    say("Düzenek hareketi: toplama durdu, kalibrasyon kaydı korundu. Durunca bağlantı otomatik doğrulanacak.");
                }
                boolean referenceNeeded=calibrating||markerCalibration!=null;
                if(referenceNeeded){
                    CameraReferenceGuard.State gate=cameraReferenceGuard.updateNow(cameraFrameNs,
                            cameraAtCalibrationPose(),pickupPhase!=PickupPhase.NONE||autoScan||(!calibrating&&!following)||(markerFresh&&(!following||fresh)));
                    cameraReferenceReady=gate==CameraReferenceGuard.State.READY;
                    if(gate!=lastReferenceState){
                        android.util.Log.i("FigbotCamera", "reference="+gate+" tracking="+trackingActive
                                +" poseMatch="+cameraAtCalibrationPose()+" markerFresh="+markerFresh
                                +" sample="+calibStep+" motor="+c.state());
                        if(gate==CameraReferenceGuard.State.WAIT)say("Kamera/etiket takibi toparlanıyor; ölçümler korunuyor.");
                        if(gate==CameraReferenceGuard.State.READY)say("Kamera referansı yeniden doğrulandı; devam ediliyor.");
                        lastReferenceState=gate;
                    }
                    if(!cameraReferenceReady){
                        if(autoScan&&(c.state()==RobotController.State.MOVING||c.state()==RobotController.State.STOPPING))resumeScanLeg=true;
                        c.requestStop();pendingTarget=null;
                    }
                    if(gate==CameraReferenceGuard.State.INVALID){
                        markerCalibration=null;calibrationReuse.reset();reuseRejected=false;
                        throw new IllegalStateException(calibrating
                                ?"Tarama sırasında düzenek hareketi veya kamera kesintisi; tarama durdu. Önceki kayıt korundu."
                                :"Düzenek hareketi veya kamera kesintisi: hareket durdu. Kayıt korundu; durunca kamera-kol eşlemesi otomatik doğrulanacak.");
                    }
                }
                // Stop intent is consumed before freshness checking: a transient vision loss
                // uses the ordinary bounded hold stop, never a latched motor fault.
                // A committed finite cycle uses its frozen route and encoder feedback.
                // Fig/tag occlusion is expected near grasp and at the side basket;
                // camera frame freshness, fixed-mount IMU and motor checks still apply.
                // A prevalidated automatic scan leg can blur the tag in transit.
                // Collect calibration data only when stopped with an unambiguous
                // marker; transit still requires fresh camera frames and fixed IMU.
                c.tick(pickupPhase!=PickupPhase.NONE||autoScan?cameraReferenceReady:calibrating?markerFresh:fresh&&(!following||markerFresh));
                if (!autoScan && scanMotionProfile != null &&
                        (c.state()==RobotController.State.HOLDING || c.state()==RobotController.State.DISARMED)) {
                    c.setProfile(profile); scanMotionProfile=null;
                }
                if (awaitingHold && c.state() == RobotController.State.HOLDING) {
                    awaitingHold = false;
                    say("Kol tutuyor — desteği çekebilirsin.");
                }
                if(c.state()==RobotController.State.HOLDING){if(heldSince==0)heldSince=System.nanoTime();}
                else heldSince=0;
                if((following||calibrating)&&!visionActive)throw new IllegalStateException("Kamera kapandı; hareket durduruldu.");
                restoreMarkerCalibration(c,System.nanoTime());
                markerCalibrationTick(c,System.nanoTime());
                if(cameraReferenceReady&&(pickupPhase!=PickupPhase.NONE||markerFresh))pickupTick(c);
                if ((!referenceNeeded||cameraReferenceReady) && c.state() == RobotController.State.HOLDING && pendingTarget != null) {
                    double[] next = pendingTarget;
                    pendingTarget = null;
                    planAndStart(c, next, "Uyum devam");
                }
                if (following && !planning.get() && cameraReferenceReady && markerFresh && (c.state()!=RobotController.State.HOLDING
                        || mo!=null&&mo.capturedNs()>heldSince+150_000_000L)) {
                    List<FollowBrain.Detection> feed = robotDetections(now);
                    FollowBrain.CameraState camera =
                            cameraStable ? FollowBrain.CameraState.STABLE : FollowBrain.CameraState.MOVING;
                    double[] gripper = c.state() == RobotController.State.DISARMED || mo==null
                            ? null : markerCalibration.observedTool(mo.cameraMarker()).translation();
                    FollowBrain.Decision decision =
                            brain.tick(now, camera, feed, c.state() == RobotController.State.HOLDING,
                                    c.state() == RobotController.State.MOVING, gripper);
                    switch (decision.type()) {
                        case RETARGET -> {
                            if (c.state() == RobotController.State.MOVING
                                    || c.state() == RobotController.State.STOPPING) {
                                pendingTarget = decision.targetMm();
                                if (c.state() == RobotController.State.MOVING) c.requestStop();
                            } else {
                                planAndStart(c, decision.targetMm(), "Turuncu uyum");
                            }
                        }
                        case PRECISE_MOVE -> planAndStart(c, decision.targetMm(), "Yeşil yaklaşma");
                        case ARRIVED -> planAndStart(c,decision.targetMm(),"Alma çevrimi");
                        case LOST_TARGET -> {c.requestStop();pendingTarget=null;say("Seçilen incir örtüldü; aynı incir yeniden görünene kadar bekleniyor.");}
                        default -> { }
                    }
                }
            }
            if (now - lastUiUpdate > 250_000_000L) {
                lastUiUpdate = now;
                if(c!=null&&now-lastMotorLog>1_000_000_000L){
                    lastMotorLog=now;
                    android.util.Log.i("FigbotMotor","state="+c.state()+" sample="+calibStep+" note="+c.telemetryNote()+" rows="+c.feedback());
                }
                updateTargetLine(c);
            }
        } catch (Exception error) {
            if(c!=null)c.requestStop();
            reportError(error);
            if(calibrating){calibrating=false;autoScan=false;markerSamples.clear();}
            following = false; motionEpoch.incrementAndGet(); pickupPhase=PickupPhase.NONE;
            brain.disarm();
            pendingTarget = null;
            awaitingHold = false;
            updateTargetLine(c);
            ui.post(() -> followButton.setText("Hedefe Git"));
        }
    }

    private long lastUiUpdate,lastMotorLog;

    private void planAndStart(RobotController c, double[] detectionMm, String why) throws Exception {
        requireWorkSurface();
        requireGripperSettings();
        if(planning.get()||attemptedTargets.contains(detectionMm))return;
        ArucoTracker.Observation observation=markerObservation.get();
        if(markerCalibration==null||observation==null||!observation.fresh(System.nanoTime(),visionGeneration)||!observation.usable()||!cameraReferenceReady)return;
        double[] target = {detectionMm[0], detectionMm[1], gripZMm()};
        int[] seed = c.positions();
        // Bounded correction at the start of each leg; do not mutate camera calibration mid-flight.
        double[] measured=markerCalibration.observedTool(observation.cameraMarker()).translation();
        double[] model=new So101Kinematics(profile).forward(seed);
        double correction=0;for(int i=0;i<3;i++)correction+=Math.pow(model[i]-measured[i],2);
        if(Math.sqrt(correction)>20){
            android.util.Log.w("FigbotCalib","TIP_MODEL_MISMATCH raw="+java.util.Arrays.toString(seed)
                    +" model="+java.util.Arrays.toString(model)+" observed="+java.util.Arrays.toString(measured)
                    +" cameraR="+java.util.Arrays.deepToString(observation.cameraMarker().rotation())
                    +" cameraT="+java.util.Arrays.toString(observation.cameraMarker().translation()));
            throw new IllegalStateException(String.format(Locale.US,"Görülen uç ile model farkı %.1f mm; hareket bekliyor.",Math.sqrt(correction)));
        }
        double weight=Math.min(1,10/Math.max(.001,Math.sqrt(correction)));
        for(int i=0;i<3;i++)target[i]+=(model[i]-measured[i])*weight;
        // Vision correction must never lower the model tip beneath the configured
        // pickup clearance. A slightly high approach is preferable to table contact.
        target[2]=Math.max(gripZMm(),target[2]);
        if(!planning.compareAndSet(false,true))return;
        final long epoch=motionEpoch.get();final int generation=visionGeneration;
        final MarkerCalibration.Result calibrationUsed=markerCalibration;
        final ArmProfile profileUsed=profile;final int speed=SPEEDS[speedIndex];
        final double[] desired=detectionMm.clone();
        say("Yaklaşma açısı hesaplanıyor; kol bulunduğu konumda tutuyor.");
        planner.execute(()->{
            PickupCycle computed=null;Exception problem=null;
            try{computed=PickupCycle.plan(profileUsed,seed,target,speed);}catch(Exception error){problem=error;}
            final PickupCycle cycle=computed;final Exception failure=problem;
            try{motor.execute(()->{
                planning.set(false);
                if(epoch!=motionEpoch.get()||!following||controller!=c||generation!=visionGeneration
                        ||markerCalibration!=calibrationUsed||c.state()!=RobotController.State.HOLDING)return;
                try{
                    if(failure!=null)throw new IllegalStateException(String.format(Locale.US,
                            "Hedef X %.0f · Y %.0f · Z %.0f mm: %s",target[0],target[1],target[2],failure.getMessage()),failure);
                    ArucoTracker.Observation current=markerObservation.get();long now=System.nanoTime();
                    if(!cameraReferenceReady||current==null||!current.fresh(now,visionGeneration)||!current.usable()
                            ||rawDifference(seed,c.positions())>6||Math.abs(seed[5]-c.positions()[5])>6)return;
                    if(FollowBrainDistance(calibrationUsed.observedTool(current.cameraMarker()).translation(),measured)>8)return;
                    if(robotDetections(now).stream().noneMatch(d->FollowBrainDistance(d.robotMm(),desired)<=8))return;
                    if(attemptedTargets.contains(desired))return;
                    // Persist before sending the first motion command: even an interrupted
                    // or unsuccessful attempt must not silently run again after restart.
                    attemptedTargets.add(desired);saveAttemptedTargets();
                    pickupCycle=cycle;pickupLeg=0;pickupGoal=cycle.legs().get(0).end();
                    pickupSpeed=speed;alignmentCorrectionUsed=false;
                    c.start(cycle.legs().get(0));graspInPlace=false;pickupPhase=PickupPhase.APPROACHING;
                    following=false;motionEpoch.incrementAndGet();brain.disarm();pendingTarget=null;
                    say(String.format(Locale.US,"Hedef kilitlendi X %.0f · Y %.0f mm; alma ve sepet çevrimi.",desired[0],desired[1]));
                }catch(Exception error){following=false;motionEpoch.incrementAndGet();brain.disarm();pendingTarget=null;c.requestStop();reportError(error);}
            });}catch(java.util.concurrent.RejectedExecutionException stopped){planning.set(false);}
        });
    }

    private static double FollowBrainDistance(double[] a,double[] b){
        return Math.sqrt(Math.pow(a[0]-b[0],2)+Math.pow(a[1]-b[1],2)+Math.pow(a[2]-b[2],2));
    }
    /** Explicit operator test; no target re-selection, no basket leg or torque enable. */
    private void startGraspInPlace() throws Exception {
        if(following||planning.get()||pickupPhase!=PickupPhase.NONE)throw new IllegalStateException("Önce DUR.");
        requireWorkSurface();
        requireGripperSettings();
        RobotController c=controller;
        if(c==null||c.state()!=RobotController.State.HOLDING)throw new IllegalStateException("Önce mevcut duruşta tutma doğrulanmalı.");
        requireMarkerCalibration();
        int[] measured=c.positions();
        pickupSpeed=SPEEDS[speedIndex];
        GoalTrajectory closing=PickupPlan.close(profile,measured,pickupSpeed);
        PickupPlan.lift(profile,closing.end(),pickupSpeed); // Check lift feasibility before jaw motion.
        c.startGrasp(closing);graspInPlace=true;pickupGoal=closing.end();pickupPhase=PickupPhase.CLOSING;
        motionEpoch.incrementAndGet();brain.disarm();pendingTarget=null;clearLastError();
        say("Bulunduğu yerde kavrama: yalnız kıskaç kapanıyor; ardından 5 cm kaldırıp bekleyecek.");
    }
    private void pickupTick(RobotController c) throws Exception {
        if(pickupPhase==PickupPhase.NONE||c.state()!=RobotController.State.HOLDING)return;
        int[] measured=c.positions();int difference=0;
        for(int i=0;i<6;i++)difference=Math.max(difference,Math.abs(measured[i]-pickupGoal[i]));
        boolean contact=pickupPhase==PickupPhase.CLOSING&&c.graspOutcome()==RobotController.GraspOutcome.CONTACT_POSSIBLE;
        if(contact){difference=0;for(int i=0;i<5;i++)difference=Math.max(difference,Math.abs(measured[i]-pickupGoal[i]));}
        if(difference>20)throw new IllegalStateException("Çevrim hedefi encoder ile doğrulanmadı; aynı incir yeniden denenmeyecek.");
        if(pickupPhase==PickupPhase.SEATING){
            // Always compare with the original seat, never the compensated command.
            // This checks model arrival only, not the unknown physical grasp centre.
            int[] desiredSeat=pickupCycle.legs().get(1).end();
            GraspAlignment.Residual residual=GraspAlignment.evaluate(profile,measured,desiredSeat);
            android.util.Log.i("FigbotPickup",String.format(Locale.US,
                    "seatResidual=%.2fmm pitch=%.2fdeg correctionUsed=%s raw=%s desired=%s",
                    residual.positionMm(),Math.toDegrees(residual.pitchRadians()),alignmentCorrectionUsed,
                    java.util.Arrays.toString(measured),java.util.Arrays.toString(desiredSeat)));
            if(!residual.aligned()){
                if(alignmentCorrectionUsed)throw new IllegalStateException(String.format(Locale.US,
                        "Kavrama konumu tek düzeltmeden sonra %.1f mm / %.1f° farklı; kapanmadı. Aynı hedef tekrar seçilmeyecek.",
                        residual.positionMm(),Math.toDegrees(residual.pitchRadians())));
                GoalTrajectory correction=GraspAlignment.correction(profile,measured,desiredSeat,Math.min(pickupSpeed,600));
                alignmentCorrectionUsed=true;c.start(correction);pickupGoal=correction.end();
                say("Kapanmadan önce küçük konum farkı bir kez düzeltiliyor.");return;
            }
        }
        if(pickupPhase==PickupPhase.CLOSING){
            retainedJaw=c.heldJawTarget();
            android.util.Log.i("FigbotPickup","grasp="+c.graspOutcome()+" raw="+java.util.Arrays.toString(measured)+" jawCurrent="+c.feedback().get(6).currentRaw());
            if(graspInPlace){
                int[] lifted=PickupPlan.lift(profile,measured,pickupSpeed).end();lifted[5]=retainedJaw;
                GoalTrajectory lift=PickupPlan.checked(profile,measured,lifted,pickupSpeed);
                c.start(lift);pickupGoal=lift.end();pickupPhase=PickupPhase.LIFTING;
                say("Kapanma tamamlandı; nesnenin tutulması doğrulanmadı. Açıklık korunarak 5 cm kaldırılıyor.");return;
            }
        }
        if(pickupPhase==PickupPhase.LIFTING&&(graspInPlace||getIntent().getBooleanExtra("grasp_test_only",false))){
            graspInPlace=false;
            pickupPhase=PickupPhase.NONE;getIntent().removeExtra("grasp_test_only");
            say("Kavrama/kaldırma denemesi bitti; sepet hareketi yapılmadı. İnciri görüntüden doğrula.");ui.post(()->followButton.setText("Hedefe Git"));return;
        }
        if(++pickupLeg<pickupCycle.legs().size()){
            GoalTrajectory next=pickupCycle.legFromMeasured(profile,pickupLeg,measured,retainedJaw,pickupSpeed);
            if(pickupLeg==2)c.startGrasp(next);else c.start(next);pickupGoal=next.end();
            pickupPhase=PickupPhase.values()[pickupLeg+1];
            say(new String[]{"Yaklaşma","Kıskaç açık; yatay 1–1,5 cm yerleştirme.","Kıskaç kapanıyor; akım ve konum izleniyor.","Kapanma tamam; nesne tutulması doğrulanmadı. 5 cm kaldırılıyor.","Kayıtlı sepet konumuna gidiliyor.","Sepet konumunda kıskaç açılıyor."}[pickupLeg]);
        }else{
            pickupPhase=PickupPhase.NONE;
            say("Alma ve bırakma hareketi tamamlandı; bu konum tekrar seçilmeyecek. Kavrama görüntüden doğrulanmalı.");
            ui.post(()->followButton.setText("Hedefe Git"));
        }
    }

    private List<FollowBrain.Detection> robotDetections(long now) {
        Detections snapshot = latestDetections.get();
        List<FollowBrain.Detection> result = new ArrayList<>();
        if (snapshot == null || markerCalibration == null || !workSurfaceReady
                || !cameraReferenceReady || !cameraAtCalibrationPose()) return result;
        if (!ObservationTiming.fresh(snapshot.capturedNs(), now)) return result;
        So101Kinematics kinematics = new So101Kinematics(profile);
        for (double[] robot : lastRobotFrames) {
            if (robot != null && robot.length >= 5 && !attemptedTargets.contains(robot)
                    && Math.abs(robot[3] - snapshot.capturedNs()) < 10_000_000L) {
                double[] xyz = {robot[0], robot[1], robot[2]};
                // Reject impossible detections before confidence ranking locks onto
                // them. This is only a broad reach check; full IK/path checks remain.
                if (!kinematics.withinGeometricReach(xyz)) continue;
                result.add(new FollowBrain.Detection(
                        xyz, robot[4], snapshot.capturedNs()));
            }
        }
        return result;
    }

    /** Robot-frame results of the newest render pass: {x, y, z, capturedNs, confidence}. */
    private volatile double[][] lastRobotFrames = new double[0][];

    private void updateTargetLine(RobotController c) {
        HoldControl.Action holdAction = HoldControl.action(c);
        ui.post(() -> {
            holdButton.setText(switch (holdAction) {
                case HOLD -> "Kolu tut";
                case RELEASE -> "Kolu bırak";
                case WAIT -> "Duruyor…";
                case UNKNOWN -> "Kolu tut";
            });
            holdButton.setEnabled(holdAction == HoldControl.Action.HOLD || holdAction == HoldControl.Action.RELEASE);
        });
        double[] target = brain.followTarget();
        String stateText;
        if (c == null) stateText = "Kol bağlı değil · Bağlan";
        else if (calibrating)
            stateText = "ETİKET ÖLÇÜMÜ " + calibStep + "/"+markerSampleCount()+" · " + (autoScan?"yavaş otomatik tarama":"kolu elle taşı, her duruşta bekle");
        else switch (c.state()) {
            case DISARMED -> stateText = "Tork kapalı · kolu destekle ve Kolu tut";
            case HOLDING -> stateText = "Kol tutuyor";
            case MOVING, STOPPING -> stateText = "Kol hareket halinde";
            case FAULT_HOLD -> stateText = "Hata sonrası tutmada · kolu kontrol et";
            case FAULT_UNKNOWN -> stateText = "Durum belirsiz · kolu kontrol et";
            default -> stateText = c.state().toString();
        }
        String text;
        if (c == null || calibrating) {
            text = stateText;
        } else if (target == null) {
            text = stateText + " · hedef bekleniyor";
        } else {
            try {
                ArucoTracker.Observation mo=markerObservation.get();
                double[] gripper = markerCalibration!=null&&mo!=null&&mo.fresh(System.nanoTime(),visionGeneration)
                        ?markerCalibration.observedTool(mo.cameraMarker()).translation():new So101Kinematics(profile).forward(c.positions());
                double error = Math.sqrt(Math.pow(gripper[0] - target[0], 2)
                        + Math.pow(gripper[1] - target[1], 2)
                        + Math.pow(gripper[2] - gripZMm(), 2));
                text = String.format(Locale.US,
                        "HEDEF %.0f / %.0f mm · UÇ %.0f / %.0f / %.0f mm · SAPMA %.0f mm",
                        target[0], target[1], gripper[0], gripper[1], gripper[2], error);
            } catch (Exception unavailable) {
                text = "HEDEF " + Math.round(target[0]) + " / " + Math.round(target[1]) + " mm";
            }
        }
        String finalText = text;
        ui.post(() -> targetLine.setText(finalText));
        ArucoTracker.Observation obs=markerObservation.get();
        String markerText=markerDisplay.get(System.nanoTime(),visionGeneration)!=null?"Etiket izleniyor · ölçüm yenileniyor":markerError;
        if(obs!=null&&obs.fresh(System.nanoTime(),visionGeneration)){
            double distance=obs.cameraMarker().distance(RigidPose.identity());
            markerText=obs.usable()
                    ?String.format(Locale.US,"ETİKET 0 · %.1f cm · %.0f° · %s",distance/10,obs.quality().incidenceDegrees(),markerSteady?"kararlı":"ölçümler birleşiyor")
                    :"ETİKET 0 · "+obs.measurementProblem();
            if(markerCalibration!=null)markerText+=String.format(Locale.US," · kontrol %.1f mm",markerCalibration.heldRmsMm());
        }
        final String markerLabel=markerText;ui.post(()->markerLine.setText(markerLabel));
        boolean stableNow = cameraStable;
        ui.post(() -> {
            chip.setText(stableNow ? "STABİL" : "HAREKETLİ");
            chip.setBackgroundResource(stableNow ? R.drawable.bg_chip_stable : R.drawable.bg_chip_moving);
        });
    }

    // ---------------- Camera / AR ----------------

    @Override protected void onResume() {
        super.onResume();
        visionActive=true;visionGeneration++;reuseRejected=false;calibrationReuse.reset();
        for(int type:new int[]{Sensor.TYPE_GAME_ROTATION_VECTOR,Sensor.TYPE_LINEAR_ACCELERATION}){
            Sensor sensor=mountSensors.getDefaultSensor(type);
            if(sensor!=null)mountSensors.registerListener(mountListener,sensor,SensorManager.SENSOR_DELAY_GAME);
        }
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST);
            return;
        }
        if (session == null && !createSession()) return;
        try {
            session.resume();
            surfaceView.onResume();
        } catch (CameraNotAvailableException error) {
            session = null;
            say("Kamera açılamadı: " + error.getMessage());
        }
    }

    @Override protected void onPause() {
        if(teachingCamera!=null)teachingCamera.clear();
        mountSensors.unregisterListener(mountListener);mountReference.clear();
        visionActive=false;trackingActive=false;cameraReferenceReady=false;visionGeneration++;markerObservation.set(null);markerDisplay.clear();figDisplay.clear();markerSteady=false;markerCalibration=null;calibration=null;
        brain.disarm();following=false;motionEpoch.incrementAndGet();pickupPhase=PickupPhase.NONE;pendingTarget=null;calibrating=false;autoScan=false;
        if(controller!=null)controller.requestStop();
        latestDetections.set(null);
        super.onPause();
        surfaceView.onPause();
        if (session != null) session.pause();
    }

    @Override protected void onDestroy() {
        if(teachingCamera!=null)teachingCamera.close();
        if(cameraControls!=null)cameraControls.dispose();
        motionEpoch.incrementAndGet();planner.shutdownNow();
        brain.disarm();
        motor.schedule(() -> {
            if (bus != null) try {
                bus.close();
            } catch (Exception ignored) {
            }
            motor.shutdown();
        }, 400, TimeUnit.MILLISECONDS);
        markerExecutor.shutdown();
        inferenceExecutor.execute(() -> { try { if (detector != null) detector.close(); } catch (Exception ignored) {} });
        inferenceExecutor.shutdown();

        unregisterReceiver(usbReceiver);
        if (session != null) {
            session.close();
            session = null;
        }
        super.onDestroy();
    }

    @Override public void onUserInteraction(){super.onUserInteraction();if(cameraControls!=null)cameraControls.interacted();}
    @Override public boolean onKeyUp(int code,android.view.KeyEvent event){
        if(code==android.view.KeyEvent.KEYCODE_BACK&&cameraControls!=null&&cameraControls.visible()){
            cameraControls.show(false);return true;
        }return super.onKeyUp(code,event);
    }

    private boolean createSession() {
        try {
            ArCoreApk.InstallStatus status = ArCoreApk.getInstance().requestInstall(this, !installRequested);
            if (status == ArCoreApk.InstallStatus.INSTALL_REQUESTED) {
                installRequested = true;
                say("Google Play Services for AR kurulması bekleniyor.");
                return false;
            }
            session = new Session(this);
            Config config = session.getConfig();
            config.setFocusMode(Config.FocusMode.AUTO);
            config.setPlaneFindingMode(Config.PlaneFindingMode.HORIZONTAL_AND_VERTICAL);
            config.setDepthMode(session.isDepthModeSupported(Config.DepthMode.AUTOMATIC)
                    ? Config.DepthMode.AUTOMATIC : Config.DepthMode.DISABLED);
            android.util.Log.i("FigbotDepth","mode="+config.getDepthMode());
            session.configure(config);
            cameraTextureBound = false;
            return true;
        } catch (UnavailableException | RuntimeException error) {
            say("ARCore başlatılamadı: " + error.getClass().getSimpleName());
            return false;
        }
    }

    @Override public void onSurfaceCreated(javax.microedition.khronos.opengles.GL10 gl,
                                          javax.microedition.khronos.egl.EGLConfig config) {
        backgroundRenderer.createOnGlThread();
        cameraTextureBound = false;
    }

    @Override public void onSurfaceChanged(javax.microedition.khronos.opengles.GL10 gl, int width, int height) {
        surfaceWidth = width;
        surfaceHeight = height;
        // EGL context is preserved during rotation: its old viewport otherwise
        // squeezes the camera into the portrait width while overlay uses landscape.
        android.opengl.GLES20.glViewport(0,0,width,height);
        backgroundRenderer.invalidateGeometry();
        ui.post(()->{overlayView.setToolCorners(null);overlayView.setFigMarkers(List.of(),false);});
    }

    @Override public void onDrawFrame(javax.microedition.khronos.opengles.GL10 gl) {
        Session active = session;
        if (active == null) return;
        try {
            if (!cameraTextureBound) {
                active.setCameraTextureName(backgroundRenderer.getTextureId());
                cameraTextureBound = true;
            }
            int rotation = getWindowManager().getDefaultDisplay().getRotation();
            active.setDisplayGeometry(rotation, surfaceWidth, surfaceHeight);
            Frame frame = active.update();
            backgroundRenderer.draw(frame);
            Camera camera = frame.getCamera();
            boolean worldTracked=camera.getTrackingState()==TrackingState.TRACKING;
            if(worldTracked!=worldTrackingActive)android.util.Log.i("FigbotCamera","AR world tracking="+worldTracked+"; CPU marker/table processing remains independent");
            worldTrackingActive=worldTracked;
            if (camera.getTrackingState() == TrackingState.STOPPED || frame.getTimestamp()<=0) {
                if(trackingActive)visionGeneration++;
                trackingActive=false;latestDetections.set(null);
                markerObservation.set(null);markerDisplay.clear();figDisplay.clear();markerSteady=false;
                cameraStable = false;
                ui.post(()->{overlayView.setToolCorners(null);overlayView.setFigMarkers(List.of(),false);});
                return;
            }
            trackingActive=true;
            cameraStable=mountReference.readyNow();
            if(worldTrackingActive)currentCameraPose=camera.getPose();
            if(frame.getTimestamp()>0&&frame.getTimestamp()!=lastCameraFrameTimestamp){
                lastCameraFrameTimestamp=frame.getTimestamp();cameraFrameNs=System.nanoTime();
            }
            if(teachingCamera!=null)scheduleTeachingExport(frame);
            else {
                scheduleMarkerInference(frame);
                scheduleInference(frame);
            }
            if (fixedCamera != null && worldTrackingActive)
                fixedCamera.updatePose(camera.getPose().getTranslation(),
                        camera.getPose().getRotationQuaternion());
            renderOverlay(frame, camera);
        } catch (CameraNotAvailableException error) {
            latestDetections.set(null);
            say("Kamera bağlantısı kesildi; uygulamayı yeniden aç.");
        } catch (RuntimeException error) {
            latestDetections.set(null);
            if(System.nanoTime()-lastRenderDiagnostic>2_000_000_000L){lastRenderDiagnostic=System.nanoTime();android.util.Log.w("FigbotCamera","Render/inference dispatch failed",error);}
        }
    }

    private void recordPose(Pose pose) {
        long now = System.nanoTime();
        synchronized (poseHistory) {
            poseHistory.addLast(new PoseSample(now, pose.getTranslation().clone(), pose.getRotationQuaternion().clone()));
            while (!poseHistory.isEmpty() && now - poseHistory.getFirst().t > STABILITY_WINDOW_NS + 300_000_000L)
                poseHistory.removeFirst();
            PoseSample oldest = null;
            for (PoseSample sample : poseHistory)
                if (now - sample.t >= STABILITY_WINDOW_NS) oldest = sample;
            cameraStable = oldest != null && ObservationTiming.stationary(
                    oldest.translation(), pose.getTranslation(),
                    oldest.quaternion(), pose.getRotationQuaternion());
        }
    }

    /** Camera-only teaching must not queue ArUco/YOLO work behind its raw image.
     * Keep the existing CPU capture skew/freshness gate unchanged. */
    private void scheduleTeachingExport(Frame frame) {
        long now=System.nanoTime();
        if(!visionActive||now-lastMarkerRequestNs<50_000_000L||!markerRunning.compareAndSet(false,true))return;
        lastMarkerRequestNs=now;
        final Image image;
        try{image=frame.acquireCameraImage();}
        catch(NotYetAvailableException|ResourceExhaustedException e){markerRunning.set(false);return;}
        final long captured=ObservationTiming.cpuCapture(frame.getTimestamp(),image.getTimestamp(),lastMarkerImageTimestamp,now);
        if(captured==0){image.close();markerRunning.set(false);return;}
        lastMarkerImageTimestamp=image.getTimestamp();
        final float[] focal=frame.getCamera().getImageIntrinsics().getFocalLength();
        final float[] principal=frame.getCamera().getImageIntrinsics().getPrincipalPoint();
        final int generation=visionGeneration;
        try {
            markerExecutor.execute(()->{
                try(image){
                    if(teachingCamera!=null&&visionActive&&generation==visionGeneration)
                        teachingCamera.offer(image,captured,generation,focal,principal);
                } catch(RuntimeException error){
                    android.util.Log.w("FigbotTeaching","Raw camera export failed",error);
                } finally {markerRunning.set(false);}
            });
        } catch(java.util.concurrent.RejectedExecutionException error){
            image.close();markerRunning.set(false);
        }
    }

    private void scheduleMarkerInference(Frame frame) {
        long now=System.nanoTime();
        if(!visionActive||markerDetector==null||now-lastMarkerRequestNs<90_000_000L||!markerRunning.compareAndSet(false,true))return;
        lastMarkerRequestNs=now;
        final Image image;
        try{image=frame.acquireCameraImage();}catch(NotYetAvailableException|ResourceExhaustedException e){markerRunning.set(false);return;}
        long delay=frame.getTimestamp()-image.getTimestamp();
        final long captured=ObservationTiming.cpuCapture(frame.getTimestamp(),image.getTimestamp(),lastMarkerImageTimestamp,now);
        if(captured==0){
            if(now-lastRenderDiagnostic>2_000_000_000L){lastRenderDiagnostic=now;android.util.Log.w("FigbotCamera","CPU image rejected delay_ms="+delay/1_000_000+" duplicate="+(image.getTimestamp()<=lastMarkerImageTimestamp));}
            image.close();markerRunning.set(false);return;
        }
        lastMarkerImageTimestamp=image.getTimestamp();
        final Pose pose=frame.getCamera().getPose();
        final float[]focal=frame.getCamera().getImageIntrinsics().getFocalLength(),principal=frame.getCamera().getImageIntrinsics().getPrincipalPoint();
        markerView=new MarkerVisibility(focal[0],focal[1],principal[0],principal[1],image.getWidth(),image.getHeight());
        final int generation=visionGeneration;
        markerExecutor.execute(()->{
            long began=System.nanoTime();
            try(image){
                if(teachingCamera!=null&&visionActive&&generation==visionGeneration)
                    teachingCamera.offer(image,captured,generation,focal,principal);
                ArucoTracker.Observation obs=markerDetector.detect(image,focal,principal,pose,captured,generation);
                if(!visionActive||!trackingActive||generation!=visionGeneration)return;
                markerAttempts++;
                if(obs!=null){
                    markerSeen++;if(obs.usable())markerClear++;
                    markerObservation.set(obs);markerDisplay.offer(obs,captured,generation);
                    if(obs.usable())previewWindow.add(captured,generation,obs.cameraMarker());
                    else previewWindow.clear();
                }
                // A miss does not invent a new timestamp. Motor freshness still expires at 400 ms.
                markerSteady=previewWindow.result(System.nanoTime(),generation)!=null;
                if(System.nanoTime()-lastVisionLog>1_000_000_000L){
                    lastVisionLog=System.nanoTime();
                    Detections figs=latestDetections.get();
                    android.util.Log.i("FigbotVision","frames="+markerAttempts+" seen="+markerSeen+" clear="+markerClear
                        +" steady="+markerSteady+" marker_ms="+(lastVisionLog-began)/1_000_000+" fig_ms="+figInferenceMs
                        +" view="+(obs==null?"none":obs.quality())+" usable="+(obs!=null&&obs.usable())
                        +" figs="+(figs==null?0:figs.boxes().size())+" calib="+calibStep+" window="+stableMarkerFrames);
                    if(markerDiagnostics&&obs!=null)try{
                        RobotController current=controller;
                        MarkerDiagnostics.save(new java.io.File(getFilesDir(),"marker_debug"),markerDiagnosticSlot++,image,obs,focal,principal,
                                current==null?null:current.positions());
                    }catch(Exception diagnosticError){android.util.Log.w("FigbotVision","Marker diagnostic capture failed",diagnosticError);}
                }
            }catch(Exception e){markerError="Etiket ölçümü bekleniyor";}
            finally{markerRunning.set(false);}
        });
    }

    private void scheduleInference(Frame frame) {
        long now=System.nanoTime();
        if(!visionActive||!detectorReady||now-lastInferenceRequestNs<INFERENCE_INTERVAL_NS||!inferenceRunning.compareAndSet(false,true))return;
        lastInferenceRequestNs=now;
        final Image image;
        try{image=frame.acquireCameraImage();}catch(NotYetAvailableException|ResourceExhaustedException e){inferenceRunning.set(false);return;}
        final long captured=ObservationTiming.cpuCapture(frame.getTimestamp(),image.getTimestamp(),lastFigImageTimestamp,now);
        if(captured==0){image.close();inferenceRunning.set(false);return;}
        lastFigImageTimestamp=image.getTimestamp();
        final Pose capturePose=frame.getCamera().getPose();final int generation=visionGeneration;
        inferenceExecutor.execute(()->{
            long began=System.nanoTime();
            try(image){
                List<FigDetection> boxes=detector.detect(image);
                if(visionActive&&trackingActive&&generation==visionGeneration){
                    Detections result=new Detections(boxes,captured,capturePose,generation);
                    latestDetections.set(result);
                    if(!boxes.isEmpty())figDisplay.offer(result,captured,generation);
                }
            }catch(Exception error){latestDetections.set(null);}
            finally{figInferenceMs=(System.nanoTime()-began)/1_000_000;inferenceRunning.set(false);}
        });
    }

    /** Re-tests each detection against the current frame, resolves robot XYZ, draws markers. */
    private void renderOverlay(Frame frame, Camera camera) {
        long now=System.nanoTime();
        if(now-lastOverlayNs<50_000_000L)return;
        lastOverlayNs=now;
        renderToolMarker(frame);
        Detections raw = latestDetections.get();
        Detections snapshot = figDisplay.get(now,visionGeneration);
        boolean measured=snapshot!=null && snapshot==raw && ObservationTiming.fresh(snapshot.capturedNs(),now);
        List<TargetOverlayView.FigMarker> markers = new ArrayList<>();
        double[][] robotFrames = new double[Math.min(6, snapshot == null ? 0 : snapshot.boxes().size())][];
        int kept = 0;
        if (snapshot != null && snapshot.generation()==visionGeneration
                && mountReference.readyNow()) {
            double[] followTarget = brain.followTarget();
            for (FigDetection detection : snapshot.boxes()) {
                if (kept >= robotFrames.length) break;
                float[] view = imageToView(frame, detection);
                if (view == null) continue;
                if(!measured){
                    markers.add(new TargetOverlayView.FigMarker(view[4],view[5],"İncir · görüntü yenileniyor",false,false));continue;
                }
                FigTargetGeometry.Measurement measuredTarget=groundTarget(frame,camera,view);
                if(measuredTarget==null){
                    String reason=!workSurfaceReady?"zemin yüksekliğini ayarla":markerCalibration==null
                            ?(savedMarkerCalibration!=null?"etiket/kol eşlemesi doğrulanmalı":"etiketle zemin eşlemesi gerekli")
                            :"zemin referansı veya temas noktası geçersiz";
                    markers.add(new TargetOverlayView.FigMarker(view[4],view[5],"Mesafe ölçülemedi · "+reason,false,false));
                    continue;
                }
                double[] robot={measuredTarget.xMm(),measuredTarget.yMm(),measuredTarget.gripZMm()};
                robotFrames[kept++] = new double[]{robot[0], robot[1], robot[2], snapshot.capturedNs(), detection.confidence()};
                boolean tracked = followTarget != null
                        && Math.hypot(robot[0] - followTarget[0], robot[1] - followTarget[1]) <= 60;
                String label = String.format(Locale.US, "Zemin hesabı %.1f cm · X %.0f Y %.0f Z %.0f mm%s",
                        measuredTarget.cameraRangeMm()/10,robot[0], robot[1], robot[2], tracked ? " · HEDEF" : "");
                markers.add(new TargetOverlayView.FigMarker(view[4], view[5], label, cameraStable, tracked));
            }
        }
        lastRobotFrames = java.util.Arrays.copyOf(robotFrames, kept);
        ui.post(()->overlayView.setFigMarkers(markers,cameraStable));
    }

    /** Intersect the measured work plane in the unchanged robot-base frame.
     * Intersect the upright box's bottom centre, not its elevated visual centre. */
    private FigTargetGeometry.Measurement groundTarget(Frame frame,Camera camera,float[] view){
        MarkerCalibration.Result reference=markerCalibration;
        if(!workSurfaceReady||reference==null||!cameraReferenceReady||!cameraAtCalibrationPose())return null;
        float bottom=Math.max(view[1],view[3]);
        if(bottom>=surfaceHeight-4)return null;
        FloatBuffer in=directFloatBuffer(new float[]{(view[0]+view[2])/2,bottom}),out=directFloatBuffer(new float[2]);
        try{
            frame.transformCoordinates2d(Coordinates2d.VIEW,in,Coordinates2d.IMAGE_PIXELS,out);
            float[] f=camera.getImageIntrinsics().getFocalLength(),p=camera.getImageIntrinsics().getPrincipalPoint();
            return FigTargetGeometry.resolve(true,reference.baseWorld(),out.get(0),out.get(1),f[0],f[1],p[0],p[1],profile.groundZMm(),GRIP_CLEARANCE_MM);
        }catch(RuntimeException rejected){return null;}
    }

    private void renderToolMarker(Frame frame){
        ArucoTracker.Observation obs=markerDisplay.get(System.nanoTime(),visionGeneration);
        if(obs==null){ui.post(()->overlayView.setToolCorners(null));return;}
        FloatBuffer in=directFloatBuffer(obs.imageCorners()),out=directFloatBuffer(new float[8]);
        frame.transformCoordinates2d(Coordinates2d.IMAGE_PIXELS,in,Coordinates2d.VIEW,out);
        float[]points=new float[8];out.get(points);ui.post(()->overlayView.setToolCorners(points));
    }

    private float[] imageToView(Frame frame, FigDetection detection) {
        FloatBuffer input = directFloatBuffer(new float[]{detection.left(), detection.top(),
                detection.right(), detection.bottom(), detection.centerX(), detection.centerY()});
        FloatBuffer output = directFloatBuffer(new float[6]);
        try {
            frame.transformCoordinates2d(Coordinates2d.IMAGE_PIXELS, input, Coordinates2d.VIEW, output);
            output.rewind();
            float[] result = new float[6];
            output.get(result);
            return result;
        } catch (RuntimeException error) {
            return null;
        }
    }

    private float[] hitWorld(Frame frame, float viewX, float viewY) {
        if(!worldTrackingActive)return null;
        for (HitResult hit : frame.hitTest(viewX, viewY)) {
            if (hit.getTrackable() instanceof DepthPoint
                    || hit.getTrackable() instanceof Plane plane && plane.isPoseInPolygon(hit.getHitPose())) {
                float[] t = hit.getHitPose().getTranslation();
                if(System.nanoTime()-lastDepthLog>2_000_000_000L){
                    lastDepthLog=System.nanoTime();
                    android.util.Log.i("FigbotDepth","hit="+hit.getTrackable().getClass().getSimpleName()+" distance_m="+hit.getDistance());
                }
                return new float[]{t[0], t[1], t[2]};
            }
        }
        return null;
    }
    private long lastDepthLog;

    private static FloatBuffer directFloatBuffer(float[] values) {
        FloatBuffer buffer = ByteBuffer.allocateDirect(values.length * Float.BYTES)
                .order(ByteOrder.nativeOrder()).asFloatBuffer();
        buffer.put(values);
        buffer.rewind();
        return buffer;
    }
}
