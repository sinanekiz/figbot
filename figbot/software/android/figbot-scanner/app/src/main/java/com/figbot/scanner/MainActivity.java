package com.figbot.scanner;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.media.Image;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.WindowManager;
import android.view.MotionEvent;
import android.view.Surface;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import com.google.ar.core.ArCoreApk;
import com.google.ar.core.Camera;
import com.google.ar.core.Config;
import com.google.ar.core.Coordinates2d;
import com.google.ar.core.DepthPoint;
import com.google.ar.core.Frame;
import com.google.ar.core.HitResult;
import com.google.ar.core.Plane;
import com.google.ar.core.Point;
import com.google.ar.core.Pose;
import com.google.ar.core.Session;
import com.google.ar.core.TrackingState;
import com.google.ar.core.exceptions.CameraNotAvailableException;
import com.google.ar.core.exceptions.NotYetAvailableException;
import com.google.ar.core.exceptions.ResourceExhaustedException;
import com.google.ar.core.exceptions.UnavailableException;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/** ARCore field scanner with automatic, offline fig detection. */
public final class MainActivity extends Activity implements GLSurfaceView.Renderer {
    private static final int CAMERA_PERMISSION_REQUEST = 41;
    private static final long OVERLAY_INTERVAL_NS = 100_000_000L;
    private static final long INFERENCE_INTERVAL_NS = 250_000_000L;

    private enum TapMode { NONE, ORIGIN, POSITIVE_X, ROBOT_POINT }
    private PhoneHarvest harvest;
    private record PendingTap(float x, float y, TapMode mode) {}
    private record SelectedHit(HitResult hit, String source) {}
    private record DetectionSnapshot(List<FigDetection> detections, long inferenceMillis,
            long capturedNs, long imageTimestampNs, Pose pose, int rotation, int generation) {
        static DetectionSnapshot empty() { return new DetectionSnapshot(List.of(), 0, 0, 0, null, -1, -1); }
    }
    private record ObservationSnapshot(String json, long capturedNs) {}
    private record ResolvedTarget(
            int trackId,
            float confidence,
            Vec3 worldPoint,
            Vec3 basePoint,
            double cameraDistanceMetres,
            String depthSource) {}

    private GLSurfaceView surfaceView;
    private TargetOverlayView overlayView;
    private TextView statusText;
    private TextView calibrationText;
    private EditText endpointText;
    private TextView streamStatus;
    private Button streamButton;
    private final Handler streamHandler = new Handler(Looper.getMainLooper());
    private volatile boolean streaming;
    private volatile boolean activityActive;
    private final AtomicBoolean sending = new AtomicBoolean();
    private volatile int observationGeneration;
    private volatile ObservationSnapshot observation;
    private final String observationSession = UUID.randomUUID().toString();
    private long observationSequence;
    private String streamEndpoint = "";
    private final Runnable streamTick = new Runnable() {
        @Override public void run() {
            if (!streaming || !activityActive) return;
            sendObservation(streamEndpoint);
            streamHandler.postDelayed(this, 500);
        }
    };
    private final BackgroundRenderer backgroundRenderer = new BackgroundRenderer();
    private final BaseFrameCalibration calibration = new BaseFrameCalibration();
    private final AtomicReference<PendingTap> pendingTap = new AtomicReference<>();
    private final AtomicReference<TapMode> tapMode = new AtomicReference<>(TapMode.NONE);
    private final AtomicReference<DetectionSnapshot> detectorSnapshot =
            new AtomicReference<>(DetectionSnapshot.empty());
    private final AtomicBoolean inferenceRunning = new AtomicBoolean();
    private final ExecutorService inferenceExecutor = Executors.newSingleThreadExecutor();
    private final ExecutorService ioExecutor = Executors.newSingleThreadExecutor();

    private volatile List<ResolvedTarget> resolvedTargets = List.of();
    private volatile OnnxFigDetector detector;
    private volatile boolean detectorReady;
    private Session session;
    private boolean installRequested;
    private boolean cameraTextureBound;
    private boolean depthSupported;
    private volatile int surfaceWidth;
    private volatile int surfaceHeight;
    private long lastOverlayUpdateNs;
    private long lastInferenceRequestNs;
    private long lastInferenceImageTimestampNs;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        ControlUi.insets(this, findViewById(R.id.cameraRoot));

        surfaceView = findViewById(R.id.surfaceView);
        overlayView = findViewById(R.id.targetOverlay);
        statusText = findViewById(R.id.statusText);
        calibrationText = findViewById(R.id.calibrationText);
        endpointText = findViewById(R.id.endpointText);
        streamStatus = findViewById(R.id.streamStatus);
        streamButton = findViewById(R.id.streamButton);
        harvest=new PhoneHarvest(this,findViewById(R.id.robotStatus),()->tapMode.set(TapMode.ROBOT_POINT));
        findViewById(R.id.robotPreview).setOnClickListener(v->harvest.preview());
        findViewById(R.id.robotStart).setOnClickListener(v->harvest.start());
        findViewById(R.id.robotStop).setOnClickListener(v->harvest.stop());
        Button speedButton=findViewById(R.id.speedButton);
        speedButton.setOnClickListener(v->speedButton.setText(harvest.cycleSpeed()));
        findViewById(R.id.homeButton).setOnClickListener(v->harvest.goHome());
        endpointText.setText(getPreferences(MODE_PRIVATE).getString("endpoint",
                "http://127.0.0.1:8872/api/targets"));
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        streamButton.setOnClickListener(v -> {
            if (streaming) { stopStreaming(); return; }
            streamEndpoint = endpointText.getText().toString().trim();
            if (streamEndpoint.isEmpty()) { streamStatus.setText("Gönderim adresi gerekli"); return; }
            getPreferences(MODE_PRIVATE).edit().putString("endpoint", streamEndpoint).apply();
            streaming = true;
            endpointText.setEnabled(false);
            streamButton.setText("Canlı aktarımı durdur");
            streamHandler.post(streamTick);
        });

        surfaceView.setPreserveEGLContextOnPause(true);
        surfaceView.setEGLContextClientVersion(2);
        surfaceView.setRenderer(this);
        surfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
        surfaceView.setOnTouchListener((view, event) -> {
            if (event.getAction() == MotionEvent.ACTION_UP && tapMode.get() != TapMode.NONE) {
                pendingTap.set(new PendingTap(event.getX(), event.getY(), tapMode.get()));
                view.performClick();
            }
            return true;
        });

        Button setOrigin = findViewById(R.id.setOriginButton);
        Button setX = findViewById(R.id.setXButton);
        Button clear = findViewById(R.id.clearButton);
        Button export = findViewById(R.id.exportButton);
        Button send = findViewById(R.id.sendButton);
        setOrigin.setOnClickListener(view -> selectMode(TapMode.ORIGIN,
                "Robot J1 taban merkezine dokunun (orijin)."));
        setX.setOnClickListener(view -> selectMode(TapMode.POSITIVE_X,
                "Robotun +X yönünde, orijinden en az 50 mm uzakta bir noktaya dokunun."));
        clear.setOnClickListener(view -> clearScan());
        export.setOnClickListener(view -> exportJson());
        send.setOnClickListener(view -> sendJson());
        findViewById(R.id.cameraMenuButton).setOnClickListener(v -> finish());
        findViewById(R.id.cameraMotorsButton).setOnClickListener(v -> harvest.connect());
        if(getIntent().getBooleanExtra("pc_bridge",false))((Button)findViewById(R.id.cameraMotorsButton)).setText("PC’ye bağlan");
        findViewById(R.id.harvestGateButton).setOnClickListener(v -> harvest.settings());
        loadDetector();
    }

    private void loadDetector() {
        inferenceExecutor.execute(() -> {
            try {
                detector = new OnnxFigDetector(getApplicationContext());
                detectorReady = true;
                updateStatus("Kuru incir modeli hazır. Kamerayı yere tutun; algılama otomatik çalışır.");
            } catch (Exception error) {
                detectorReady = false;
                updateStatus("Kuru incir modeli yüklenemedi: " + error.getClass().getSimpleName());
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        activityActive = true;
        if (!hasCameraPermission()) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST);
            return;
        }
        if (session == null && !createSession()) return;
        try {
            session.resume();
            surfaceView.onResume();
            updateStatus("Kamerayı yavaşça hareket ettirin; otomatik kuru incir taraması hazırlanıyor.");
        } catch (CameraNotAvailableException error) {
            session = null;
            updateStatus("Kamera kullanılamıyor: " + error.getMessage());
        }
    }

    @Override
    protected void onPause() {
        activityActive = false;
        stopStreaming();
        invalidateObservation();
        super.onPause();
        surfaceView.onPause();
        if (session != null) session.pause();
    }

    @Override
    protected void onDestroy() {
        if(harvest!=null)harvest.close();
        if (session != null) {
            session.close();
            session = null;
        }
        inferenceExecutor.shutdownNow();
        ioExecutor.shutdownNow();
        OnnxFigDetector activeDetector = detector;
        if (activeDetector != null) {
            try {
                activeDetector.close();
            } catch (Exception ignored) {
                // Activity is already shutting down.
            }
        }
        super.onDestroy();
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == CAMERA_PERMISSION_REQUEST
                && (results.length == 0 || results[0] != PackageManager.PERMISSION_GRANTED)) {
            updateStatus("Kamera izni olmadan tarama yapılamaz.");
        }
    }

    private boolean createSession() {
        try {
            ArCoreApk.InstallStatus installStatus = ArCoreApk.getInstance()
                    .requestInstall(this, !installRequested);
            if (installStatus == ArCoreApk.InstallStatus.INSTALL_REQUESTED) {
                installRequested = true;
                updateStatus("Google Play Services for AR kurulumu bekleniyor.");
                return false;
            }
            session = new Session(this);
            Config config = session.getConfig();
            config.setFocusMode(Config.FocusMode.AUTO);
            config.setPlaneFindingMode(Config.PlaneFindingMode.HORIZONTAL_AND_VERTICAL);
            depthSupported = session.isDepthModeSupported(Config.DepthMode.AUTOMATIC);
            if (depthSupported) config.setDepthMode(Config.DepthMode.AUTOMATIC);
            session.configure(config);
            cameraTextureBound = false;
            return true;
        } catch (UnavailableException | RuntimeException error) {
            updateStatus("ARCore başlatılamadı: " + error.getClass().getSimpleName());
            return false;
        }
    }

    private boolean hasCameraPermission() {
        return checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED;
    }

    private void selectMode(TapMode mode, String instruction) {
        tapMode.set(mode);
        updateStatus(instruction);
    }

    private void clearScan() {
        synchronized (calibration) {
            calibration.clear();
            invalidateObservation();
        }
        resolvedTargets = List.of();
        detectorSnapshot.set(DetectionSnapshot.empty());
        tapMode.set(TapMode.NONE);
        overlayView.setMarkers(List.of());
        overlayView.setDetectionBoxes(List.of());
        updateCalibrationText();
        updateStatus("Kalibrasyon temizlendi; otomatik kuru incir taraması devam ediyor.");
    }

    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        GLES20.glClearColor(0f, 0f, 0f, 1f);
        backgroundRenderer.createOnGlThread();
        cameraTextureBound = false;
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        surfaceWidth = width;
        surfaceHeight = height;
        GLES20.glViewport(0, 0, width, height);
    }

    @Override
    public void onDrawFrame(GL10 gl) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT | GLES20.GL_DEPTH_BUFFER_BIT);
        Session activeSession = session;
        if (activeSession == null) return;
        try {
            if (!cameraTextureBound) {
                activeSession.setCameraTextureName(backgroundRenderer.getTextureId());
                cameraTextureBound = true;
            }
            int rotation = getWindowManager().getDefaultDisplay().getRotation();
            if (rotation < Surface.ROTATION_0 || rotation > Surface.ROTATION_270) rotation = Surface.ROTATION_0;
            activeSession.setDisplayGeometry(rotation, surfaceWidth, surfaceHeight);
            Frame frame = activeSession.update();
            backgroundRenderer.draw(frame);
            Camera camera = frame.getCamera();
            if (camera.getTrackingState() != TrackingState.TRACKING) {
                invalidateObservation();
                runOnUiThread(() -> overlayView.setDetectionBoxes(List.of()));
                return;
            }
            processPendingTap(frame);
            scheduleInference(frame);
            updateOverlay(frame, camera);
        } catch (CameraNotAvailableException error) {
            invalidateObservation();
            updateStatus("Kamera bağlantısı kesildi; uygulamayı yeniden açın.");
        } catch (RuntimeException error) {
            invalidateObservation();
            updateStatus("AR işleme hatası: " + error.getClass().getSimpleName());
        }
    }

    private void scheduleInference(Frame frame) {
        long now = System.nanoTime();
        if (!detectorReady || now - lastInferenceRequestNs < INFERENCE_INTERVAL_NS
                || !inferenceRunning.compareAndSet(false, true)) return;
        lastInferenceRequestNs = now;
        final Image image;
        try {
            image = frame.acquireCameraImage();
        } catch (NotYetAvailableException | ResourceExhaustedException error) {
            inferenceRunning.set(false);
            return;
        }
        final long imageTimestamp = image.getTimestamp();
        final long imageDelay = frame.getTimestamp() - imageTimestamp;
        if (imageTimestamp <= lastInferenceImageTimestampNs || imageDelay < 0 || imageDelay > 100_000_000L) {
            image.close();
            inferenceRunning.set(false);
            return;
        }
        lastInferenceImageTimestampNs = imageTimestamp;
        final long capturedNs = System.nanoTime() - imageDelay;
        final Pose capturePose = frame.getCamera().getPose();
        final int captureRotation = getWindowManager().getDefaultDisplay().getRotation();
        final int generation = observationGeneration;
        inferenceExecutor.execute(() -> {
            long start = System.nanoTime();
            try (image) {
                List<FigDetection> detections = detector.detect(image);
                long elapsed = (System.nanoTime() - start) / 1_000_000L;
                if (activityActive && generation == observationGeneration) {
                    detectorSnapshot.set(new DetectionSnapshot(detections, elapsed,
                            capturedNs, imageTimestamp, capturePose, captureRotation, generation));
                }
                if (tapMode.get() == TapMode.NONE) {
                    updateStatus(String.format(Locale.US,
                            "Otomatik tarama: %d kuru incir adayı · %d ms · eşik %.0f%%",
                            detections.size(), elapsed, OnnxFigDetector.CONFIDENCE_THRESHOLD * 100));
                }
            } catch (Exception error) {
                invalidateObservation();
                updateStatus("Kuru incir algılama hatası: " + error.getClass().getSimpleName());
            } finally {
                inferenceRunning.set(false);
            }
        });
    }

    private void processPendingTap(Frame frame) {
        PendingTap tap = pendingTap.getAndSet(null);
        if (tap == null || tap.mode() == TapMode.NONE) return;
        SelectedHit selected = selectHit(frame.hitTest(tap.x(), tap.y()));
        if (selected == null) {
            updateStatus("Bu noktada derinlik/düzlem bulunamadı. Cihazı hareket ettirip tekrar deneyin.");
            return;
        }
        Vec3 worldPoint = vec(selected.hit().getHitPose());
        if(tap.mode()==TapMode.ROBOT_POINT){
            tapMode.set(TapMode.NONE);
            harvest.worldTap(new double[]{worldPoint.x(),worldPoint.y(),worldPoint.z()});
            return;
        }
        try {
            synchronized (calibration) {
            invalidateObservation();
            if (tap.mode() == TapMode.ORIGIN) {
                calibration.setOrigin(worldPoint);
                tapMode.set(TapMode.POSITIVE_X);
                updateStatus("Orijin alındı. Robotun +X yönündeki ikinci noktaya dokunun.");
            } else {
                calibration.setPositiveXPoint(worldPoint);
                tapMode.set(TapMode.NONE);
                updateStatus("base_link hazır. Kuru incirler otomatik algılanıyor; dokunmanız gerekmiyor.");
            }
            }
            updateCalibrationText();
        } catch (IllegalArgumentException | IllegalStateException error) {
            updateStatus(error.getMessage());
        }
    }

    private SelectedHit selectHit(List<HitResult> hits) {
        return hits.stream().filter(this::isUsableHit)
                .min(Comparator.comparingInt(this::hitPriority))
                .map(hit -> new SelectedHit(hit, hitSource(hit))).orElse(null);
    }

    private boolean isUsableHit(HitResult hit) {
        if (hit.getTrackable() instanceof DepthPoint) return true;
        if (hit.getTrackable() instanceof Plane plane) return plane.isPoseInPolygon(hit.getHitPose());
        return hit.getTrackable() instanceof Point;
    }

    private int hitPriority(HitResult hit) {
        if (hit.getTrackable() instanceof DepthPoint) return 0;
        if (hit.getTrackable() instanceof Plane) return 1;
        return 2;
    }

    private String hitSource(HitResult hit) {
        if (hit.getTrackable() instanceof DepthPoint) return "ARCORE_DEPTH_HIT";
        if (hit.getTrackable() instanceof Plane) return "ARCORE_PLANE_HIT";
        return "ARCORE_FEATURE_POINT_HIT";
    }

    private void updateOverlay(Frame frame, Camera camera) {
        long now = System.nanoTime();
        if (now - lastOverlayUpdateNs < OVERLAY_INTERVAL_NS || surfaceWidth <= 0 || surfaceHeight <= 0) return;
        lastOverlayUpdateNs = now;

        DetectionSnapshot snapshot = detectorSnapshot.get();
        Pose pose = camera.getPose();
        if (!ObservationTiming.fresh(snapshot.capturedNs(), now) || snapshot.pose() == null
                || snapshot.generation() != observationGeneration
                || snapshot.rotation() != getWindowManager().getDefaultDisplay().getRotation()
                || !ObservationTiming.stationary(snapshot.pose().getTranslation(), pose.getTranslation(),
                        snapshot.pose().getRotationQuaternion(), pose.getRotationQuaternion())) {
            observation = null;
            resolvedTargets = List.of();
            if(harvest!=null)harvest.lost();
            runOnUiThread(() -> overlayView.setDetectionBoxes(List.of()));
            return;
        }

        synchronized (calibration) {
        List<TargetOverlayView.DetectionBox> boxes = new ArrayList<>();
        List<ResolvedTarget> resolved = new ArrayList<>();
        int trackId = 1;
        for (FigDetection detection : snapshot.detections()) {
            float[] coordinates = imageBoxToView(frame, detection);
            if (coordinates == null) continue;
            float left = Math.min(coordinates[0], coordinates[2]);
            float top = Math.min(coordinates[1], coordinates[3]);
            float right = Math.max(coordinates[0], coordinates[2]);
            float bottom = Math.max(coordinates[1], coordinates[3]);
            SelectedHit selected = selectHit(frame.hitTest(coordinates[4], coordinates[5]));
            Vec3 world = null;
            Vec3 base = null;
            double distance = Double.NaN;
            String source = "NO_DEPTH_HIT";
            if (selected != null) {
                world = vec(selected.hit().getHitPose());
                distance = world.subtract(vec(camera.getPose())).norm();
                source = selected.source();
                if (calibration.isReady()) base = calibration.toBase(world);
            }
            String coordinate = base == null ? "XYZ yok" : base.millimetreText();
            String label = String.format(Locale.US, "Kuru incir #%d %.0f%% | %s",
                    trackId, detection.confidence() * 100, coordinate);
            boxes.add(new TargetOverlayView.DetectionBox(left, top, right, bottom, label));
            resolved.add(new ResolvedTarget(trackId, detection.confidence(), world, base, distance, source));
            trackId++;
        }
        resolvedTargets = List.copyOf(resolved);
        if(harvest!=null){
            List<PhoneHarvest.Seen> seen=new ArrayList<>();
            for(ResolvedTarget target:resolved)if(target.worldPoint()!=null)
                seen.add(new PhoneHarvest.Seen(new double[]{target.worldPoint().x(),target.worldPoint().y(),target.worldPoint().z()},target.confidence(),target.depthSource()));
            harvest.frame(snapshot.capturedNs(),observationSession+":"+observationGeneration,seen,pose.getTranslation(),pose.getRotationQuaternion());
        }
        try {
            JSONObject payload = encodePayload();
            payload.put("schema", "figbot.target-observations.v3");
            payload.put("session_id", observationSession);
            payload.put("sequence", ++observationSequence);
            payload.put("calibration_revision", observationGeneration);
            payload.put("camera_tracking", "TRACKING");
            payload.put("image_timestamp_ns", snapshot.imageTimestampNs());
            payload.put("depth_frame_timestamp_ns", frame.getTimestamp());
            payload.put("inference_ms", snapshot.inferenceMillis());
            payload.put("association", "STATIONARY_SCENE_APPROXIMATION");
            payload.put("target_id_scope", "FRAME_LOCAL_NOT_TRACKED");
            payload.put("robot_model_transform", "UNVERIFIED");
            payload.put("origin_world_m", vectorJson(calibration.getOrigin()));
            payload.put("positive_x_world_m", vectorJson(calibration.getPositiveXPoint()));
            payload.put("camera_translation_world_m", vectorJson(vec(pose)));
            payload.put("camera_quaternion_xyzw", new JSONArray(pose.getRotationQuaternion()));
            if (calibration.isReady()) {
                Vec3 delta = calibration.getPositiveXPoint().subtract(calibration.getOrigin());
                payload.put("axis_horizontal_length_mm", Math.hypot(delta.x(), delta.z()) * 1000);
            }
            if (activityActive && snapshot.generation() == observationGeneration)
                observation = new ObservationSnapshot(payload.toString(), snapshot.capturedNs());
        } catch (JSONException error) {
            observation = null;
        }

        float[] view = new float[16];
        float[] projection = new float[16];
        float[] viewProjection = new float[16];
        camera.getViewMatrix(view, 0);
        camera.getProjectionMatrix(projection, 0, 0.05f, 100f);
        Matrix.multiplyMM(viewProjection, 0, projection, 0, view, 0);
        List<TargetOverlayView.Marker> markers = new ArrayList<>();
        if (calibration.hasOrigin()) {
            addProjectedMarker(markers, calibration.getOrigin(), "BASE (0,0,0)",
                    TargetOverlayView.MarkerType.ORIGIN, viewProjection);
        }
        if (calibration.getPositiveXPoint() != null) {
            addProjectedMarker(markers, calibration.getPositiveXPoint(), "+X",
                    TargetOverlayView.MarkerType.POSITIVE_X, viewProjection);
        }
        runOnUiThread(() -> {
            overlayView.setDetectionBoxes(boxes);
            overlayView.setMarkers(markers);
        });
        }
    }

    private float[] imageBoxToView(Frame frame, FigDetection detection) {
        FloatBuffer input = directFloatBuffer(new float[]{
                detection.left(), detection.top(), detection.right(), detection.bottom(),
                detection.centerX(), detection.centerY()});
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

    private static FloatBuffer directFloatBuffer(float[] values) {
        FloatBuffer buffer = ByteBuffer.allocateDirect(values.length * Float.BYTES)
                .order(ByteOrder.nativeOrder()).asFloatBuffer();
        buffer.put(values);
        buffer.rewind();
        return buffer;
    }

    private void addProjectedMarker(List<TargetOverlayView.Marker> markers, Vec3 point,
                                    String label, TargetOverlayView.MarkerType type,
                                    float[] viewProjection) {
        float[] world = {(float) point.x(), (float) point.y(), (float) point.z(), 1f};
        float[] clip = new float[4];
        Matrix.multiplyMV(clip, 0, viewProjection, 0, world, 0);
        if (clip[3] <= 0f) return;
        float ndcX = clip[0] / clip[3];
        float ndcY = clip[1] / clip[3];
        if (ndcX < -1.2f || ndcX > 1.2f || ndcY < -1.2f || ndcY > 1.2f) return;
        markers.add(new TargetOverlayView.Marker(
                (ndcX + 1f) * 0.5f * surfaceWidth,
                (1f - ndcY) * 0.5f * surfaceHeight,
                label, type));
    }

    private JSONObject encodePayload() throws JSONException {
        JSONObject payload = new JSONObject();
        payload.put("schema", "figbot.target-observations.v2");
        payload.put("coordinate_frame", "base_link");
        payload.put("units", "millimetres");
        payload.put("arm_motion_authorized", false);
        payload.put("calibration_status", calibration.isReady()
                ? "UNVERIFIED — PHYSICAL VALIDATION REQUIRED" : "UNCALIBRATED");
        payload.put("depth_api_supported", depthSupported);
        payload.put("automatic_detector_status", detectorReady
                ? "BOOTSTRAP_MODEL_UNVERIFIED" : "UNAVAILABLE");
        payload.put("inference_ms", detectorSnapshot.get().inferenceMillis());
        JSONArray items = new JSONArray();
        for (ResolvedTarget target : resolvedTargets) {
            JSONObject item = new JSONObject();
            item.put("track_id", target.trackId());
            item.put("class", "dry_fig_candidate");
            item.put("confidence", target.confidence());
            item.put("depth_source", target.depthSource());
            item.put("coordinate_status", target.basePoint() == null
                    ? "NO_BASE_COORDINATE" : "UNVERIFIED — PHYSICAL VALIDATION REQUIRED");
            if (Double.isFinite(target.cameraDistanceMetres())) item.put("distance_m", target.cameraDistanceMetres());
            if (target.basePoint() != null) {
                item.put("robot_x_mm", target.basePoint().x() * 1000);
                item.put("robot_y_mm", target.basePoint().y() * 1000);
                item.put("robot_z_mm", target.basePoint().z() * 1000);
            }
            items.put(item);
        }
        payload.put("targets", items);
        return payload;
    }

    private static Object vectorJson(Vec3 value) throws JSONException {
        if (value == null) return JSONObject.NULL;
        return new JSONArray(new double[]{value.x(), value.y(), value.z()});
    }

    private JSONObject buildPayload() throws JSONException {
        ObservationSnapshot snapshot = observation;
        long now = System.nanoTime();
        if (!activityActive || snapshot == null || !ObservationTiming.fresh(snapshot.capturedNs(), now)) {
            JSONObject empty = new JSONObject();
            empty.put("schema", "figbot.target-observations.v3");
            empty.put("coordinate_frame", "base_link");
            empty.put("units", "millimetres");
            empty.put("arm_motion_authorized", false);
            empty.put("session_id", observationSession);
            empty.put("calibration_revision", observationGeneration);
            empty.put("observation_status", "UNAVAILABLE_OR_STALE");
            empty.put("targets", new JSONArray());
            return empty;
        }
        JSONObject payload = new JSONObject(snapshot.json());
        payload.put("observation_status", "RECENT_STATIONARY_SCENE");
        payload.put("capture_age_ms_at_send", (now - snapshot.capturedNs()) / 1_000_000.0);
        return payload;
    }

    private synchronized void invalidateObservation() {
        if(harvest!=null)harvest.lost();
        observationGeneration++;
        observation = null;
        resolvedTargets = List.of();
        detectorSnapshot.set(DetectionSnapshot.empty());
    }

    private void stopStreaming() {
        streaming = false;
        streamHandler.removeCallbacks(streamTick);
        endpointText.setEnabled(true);
        streamButton.setText("Canlı aktarımı başlat");
    }

    private void exportJson() {
        try {
            JSONObject payload = buildPayload();
            File directory = getExternalFilesDir("scans");
            if (directory == null) throw new IOException("Harici uygulama klasörü bulunamadı");
            if (!directory.exists() && !directory.mkdirs()) throw new IOException("Tarama klasörü oluşturulamadı");
            File file = new File(directory, "figbot-scan-" + System.currentTimeMillis() + ".json");
            try (OutputStreamWriter writer = new OutputStreamWriter(
                    new FileOutputStream(file), StandardCharsets.UTF_8)) {
                writer.write(payload.toString(2));
            }
            updateStatus("JSON kaydedildi: " + file.getAbsolutePath());
            Toast.makeText(this, "Otomatik hedefler JSON olarak kaydedildi", Toast.LENGTH_SHORT).show();
        } catch (IOException | JSONException error) {
            updateStatus("JSON kaydedilemedi: " + error.getMessage());
        }
    }

    private void sendJson() {
        String endpoint = endpointText.getText().toString().trim();
        if (endpoint.isEmpty()) {
            updateStatus("FIGBOT HTTP hedefini girin.");
            return;
        }
        getPreferences(MODE_PRIVATE).edit().putString("endpoint", endpoint).apply();
        sendObservation(endpoint);
    }

    private void sendObservation(String endpoint) {
        if (!activityActive || !sending.compareAndSet(false, true)) return;
        ioExecutor.execute(() -> {
            HttpURLConnection connection = null;
            try {
                if (!activityActive) return;
                String body = buildPayload().toString();
                connection = (HttpURLConnection) new URL(endpoint).openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(4000);
                connection.setReadTimeout(4000);
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
                connection.setFixedLengthStreamingMode(bytes.length);
                try (var output = connection.getOutputStream()) { output.write(bytes); }
                int code = connection.getResponseCode();
                runOnUiThread(() -> streamStatus.setText("PC yanıtı: HTTP " + code
                        + " · " + (streaming ? "Canlı aktarım açık" : "Tek gönderim")));
            } catch (IOException | JSONException error) {
                runOnUiThread(() -> streamStatus.setText("Gönderim başarısız: " + error.getMessage()));
            } finally {
                if (connection != null) connection.disconnect();
                sending.set(false);
            }
        });
    }

    private void updateCalibrationText() {
        String text;
        if (calibration.isReady()) {
            text = "Kalibrasyon: base_link hazır · UNVERIFIED / PHYSICAL VALIDATION REQUIRED";
        } else if (calibration.hasOrigin()) {
            text = "Kalibrasyon: Orijin tamam · +X noktası bekleniyor";
        } else {
            text = "Kalibrasyon: Orijin ve +X bekleniyor";
        }
        runOnUiThread(() -> calibrationText.setText(text));
    }

    private void updateStatus(String message) {
        runOnUiThread(() -> statusText.setText(message));
    }

    private static Vec3 vec(Pose pose) {
        float[] translation = pose.getTranslation();
        return new Vec3(translation[0], translation[1], translation[2]);
    }
}
