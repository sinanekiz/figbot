package com.figbot.scanner.so101;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Fixed camera-to-base calibration from known mounting geometry.
 *
 * The camera (phone) is rigidly mounted to the arm base at a measured position
 * and orientation. Therefore the camera frame to robot base frame transform
 * (T_B_C) is CONSTANT and can be shipped as an asset instead of being
 * re-measured with the manual 4+3 point correspondence procedure.
 *
 * ARCore reports detections in its session-local world frame. Each frame the
 * camera pose T_W_C (world <- camera) is combined with the fixed T_B_C to
 * produce T_B_W (world -> robot base):
 *
 *     T_B_W = T_B_C @ inverse(T_W_C)
 *     P_base = R_B_W @ P_world + t_B_W
 *
 * Conventions:
 *   Robot base frame: +X forward (pickup), +Y right, +Z up, millimetres.
 *   ARCore camera: optical centre origin, metres, session axes.
 */
public final class FixedCameraCalibration {

    /** Flat measured ground: z = groundZMm in robot base frame. */
    public static final class FlatGround {
        public final double groundZMm, minObjectHeightMm, maxObjectHeightMm, pickOffsetMm;
        public FlatGround(double groundZMm, double minHeight, double maxHeight, double pickOffset) {
            this.groundZMm = groundZMm;
            this.minObjectHeightMm = minHeight;
            this.maxObjectHeightMm = maxHeight;
            this.pickOffsetMm = pickOffset;
        }
        public double heightAt(double xMm, double yMm) { return groundZMm; }
    }

    private final double[][] rotationBC = new double[3][3]; // camera -> base
    private final double[] translationBC = new double[3];  // mm, camera origin in base
    private final String sourceDescription;

    // Per-frame world -> base transform, updated from ARCore camera pose.
    private double[][] rotationBW = new double[3][3];
    private double[] translationBW = new double[3];
    private boolean poseSet;

    private FlatGround ground;

    private FixedCameraCalibration(String description) { sourceDescription = description; }

    /** Loads the bundled camera_calibration.json asset. */
    public static FixedCameraCalibration fromAsset(InputStream stream) throws Exception {
        byte[] bytes;
        try (InputStream in = stream) {
            java.io.ByteArrayOutputStream buffer = new java.io.ByteArrayOutputStream();
            byte[] chunk = new byte[8192];
            int read;
            while ((read = in.read(chunk)) != -1) buffer.write(chunk, 0, read);
            bytes = buffer.toByteArray();
        }
        JSONObject root = new JSONObject(new String(bytes, StandardCharsets.UTF_8));
        JSONObject transform = root.getJSONObject("camera_to_base");
        JSONArray matrix = transform.getJSONArray("matrix");
        if (matrix.length() != 4)
            throw new IllegalArgumentException("camera_to_base.matrix must be 4x4");
        FixedCameraCalibration result = new FixedCameraCalibration(
                root.optJSONObject("mounting") != null
                        ? root.getJSONObject("mounting").optString("description", "fixed mount")
                        : "fixed mount");
        for (int i = 0; i < 3; i++) {
            JSONArray row = matrix.getJSONArray(i);
            if (row.length() != 4) throw new IllegalArgumentException("matrix row must have 4 columns");
            for (int j = 0; j < 3; j++) result.rotationBC[i][j] = row.getDouble(j);
            result.translationBC[i] = row.getDouble(3);
        }
        return result;
    }

    /**
     * Updates the world -> base transform from the ARCore camera pose.
     * @param cameraTranslationM world position of camera optical centre (ARCore pose translation, metres)
     * @param quaternionXyzw ARCore pose rotation quaternion (x, y, z, w)
     */
    public synchronized void updatePose(float[] cameraTranslationM, float[] quaternionXyzw) {
        if (cameraTranslationM == null || cameraTranslationM.length != 3
                || quaternionXyzw == null || quaternionXyzw.length != 4)
            throw new IllegalArgumentException("Camera translation and quaternion required");
        double x = quaternionXyzw[0], y = quaternionXyzw[1], z = quaternionXyzw[2], w = quaternionXyzw[3];
        double norm = Math.sqrt(x * x + y * y + z * z + w * w);
        if (norm < 1e-12) throw new IllegalArgumentException("Invalid quaternion");
        x /= norm; y /= norm; z /= norm; w /= norm;
        // R_W_C from quaternion (world <- camera)
        double[][] rWC = {
                {1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)},
                {2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)},
                {2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)}
        };
        // R_B_W = R_B_C @ R_W_C^T
        double[][] rCW = transpose(rWC);
        rotationBW = multiply(rotationBC, rCW);
        // t_B_W = t_B_C - R_B_W @ t_W_C   (t_W_C in mm)
        double[] tWCmm = {cameraTranslationM[0] * 1000, cameraTranslationM[1] * 1000, cameraTranslationM[2] * 1000};
        double[] rotated = multiply(rotationBW, tWCmm);
        for (int i = 0; i < 3; i++) translationBW[i] = translationBC[i] - rotated[i];
        poseSet = true;
    }

    /** Converts an ARCore world point (metres) to robot base millimetres. */
    public synchronized double[] toRobotMm(double[] worldMetres) {
        if (!poseSet) throw new IllegalStateException("Camera pose not yet received");
        if (worldMetres == null || worldMetres.length != 3)
            throw new IllegalArgumentException("World XYZ required");
        double[] mm = {worldMetres[0] * 1000, worldMetres[1] * 1000, worldMetres[2] * 1000};
        double[] out = multiply(rotationBW, mm);
        for (int i = 0; i < 3; i++) out[i] += translationBW[i];
        return out;
    }

    /**
     * Converts to the pick target: XY from detection, Z clamped to the
     * measured ground plane plus the configured pick offset.
     */
    public synchronized double[] toPickTargetMm(double[] worldMetres) {
        double[] target = toRobotMm(worldMetres);
        if (ground == null) throw new IllegalStateException("Ground and grip measurements required");
        double groundZ = ground.heightAt(target[0], target[1]);
        double height = target[2] - groundZ;
        if (height < ground.minObjectHeightMm || height > ground.maxObjectHeightMm)
            throw new IllegalArgumentException("Detection outside configured fig height range");
        target[2] = groundZ + ground.pickOffsetMm;
        return target;
    }

    public synchronized void setGround(FlatGround plane) {
        if (plane == null) throw new IllegalArgumentException("Ground measurements required");
        ground = plane;
    }
    public synchronized FlatGround ground() { return ground; }
    public synchronized boolean isReady() { return poseSet; }
    public synchronized boolean isComplete() { return poseSet && ground != null; }
    public String description() { return sourceDescription; }
    public double[][] rotationBc() {
        double[][] copy = new double[3][3];
        for (int i = 0; i < 3; i++) copy[i] = rotationBC[i].clone();
        return copy;
    }
    public double[] translationBcMm() { return translationBC.clone(); }

    private static double[][] transpose(double[][] m) {
        double[][] r = new double[3][3];
        for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) r[i][j] = m[j][i];
        return r;
    }
    private static double[][] multiply(double[][] a, double[][] b) {
        double[][] r = new double[3][3];
        for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++)
            for (int k = 0; k < 3; k++) r[i][j] += a[i][k] * b[k][j];
        return r;
    }
    private static double[] multiply(double[][] m, double[] v) {
        double[] r = new double[3];
        for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) r[i] += m[i][j] * v[j];
        return r;
    }
}
