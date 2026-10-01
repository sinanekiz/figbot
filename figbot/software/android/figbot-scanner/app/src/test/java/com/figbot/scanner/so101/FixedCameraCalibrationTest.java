package com.figbot.scanner.so101;

import static org.junit.Assert.*;
import org.junit.Test;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** Verifies the fixed camera-to-base transform math and asset parsing. */
public class FixedCameraCalibrationTest {

    private static final String ASSET_JSON = "{"
            + "\"schema\":\"figbot.camera_calib.v1\","
            + "\"camera_to_base\":{"
            + "\"translation_mm\":[0.0,200.0,150.0],"
            + "\"rotation_deg\":{\"yaw\":-30.0,\"pitch\":-45.0,\"roll\":0.0},"
            + "\"matrix\":[[0.612372,0.5,-0.612372,0.0],"
            + "[-0.353553,0.866025,0.353553,200.0],"
            + "[0.707107,0.0,0.707107,150.0],"
            + "[0.0,0.0,0.0,1.0]]},"
            + "\"mounting\":{\"position_mm\":{\"x\":0,\"y\":200,\"z\":150},"
            + "\"orientation_deg\":{\"yaw\":-30,\"pitch\":-45,\"roll\":0},"
            + "\"description\":\"test mount\"},"
            + "\"verified\":false}";

    private static InputStream asset() {
        return new ByteArrayInputStream(ASSET_JSON.getBytes(StandardCharsets.UTF_8));
    }

    @Test
    public void loadsAssetMatrixAndTranslation() throws Exception {
        FixedCameraCalibration calib = FixedCameraCalibration.fromAsset(asset());
        assertArrayEquals(new double[]{0, 200, 150}, calib.translationBcMm(), 1e-9);
        double[][] r = calib.rotationBc();
        // Column norms of a rotation matrix are 1.
        for (int j = 0; j < 3; j++)
            assertEquals(1.0, Math.sqrt(r[0][j]*r[0][j]+r[1][j]*r[1][j]+r[2][j]*r[2][j]), 1e-6);
        // Determinant must be +1 (proper rotation).
        double det = r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1])
                - r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0])
                + r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0]);
        assertEquals(1.0, det, 1e-6);
        assertFalse(calib.isReady());
        assertFalse(calib.isComplete());
    }

    @Test
    public void identityCameraPoseMapsCameraOriginToMountPosition() throws Exception {
        FixedCameraCalibration calib = FixedCameraCalibration.fromAsset(asset());
        // AR session starts exactly at the camera: identity world pose.
        calib.updatePose(new float[]{0, 0, 0}, new float[]{0, 0, 0, 1});
        assertTrue(calib.isReady());
        // A point at the AR world origin is the camera origin itself, which sits
        // at [0, 200, 150] mm in robot base coordinates.
        double[] robot = calib.toRobotMm(new double[]{0, 0, 0});
        assertArrayEquals(new double[]{0, 200, 150}, robot, 1e-6);
    }

    @Test
    public void translatedWorldPoseShiftsRobotOriginConsistently() throws Exception {
        FixedCameraCalibration calib = FixedCameraCalibration.fromAsset(asset());
        // Camera 0.5 m above AR world origin, upright orientation.
        calib.updatePose(new float[]{0, 0, 0.5f}, new float[]{0, 0, 0, 1});
        // World origin in camera coordinates is (0,0,-500) mm; base result is
        // R_B_C @ (0,0,-500) + t_B_C = (306.186, 23.223, -203.553) mm.
        double[] robot = calib.toRobotMm(new double[]{0, 0, 0});
        assertArrayEquals(new double[]{306.1862, 23.2233, -203.5534}, robot, 1e-3);
    }

    @Test
    public void pickTargetClampsToGroundPlusOffset() throws Exception {
        FixedCameraCalibration calib = FixedCameraCalibration.fromAsset(asset());
        calib.updatePose(new float[]{0, 0, 0}, new float[]{0, 0, 0, 1});
        calib.setGround(new FixedCameraCalibration.FlatGround(0, 5, 60, 10));
        // Camera origin is 150 mm above the base plane; height 150 within 5..60 fails.
        try {
            calib.toPickTargetMm(new double[]{0, 0, 0});
            fail("Expected out-of-range fig height rejection");
        } catch (IllegalArgumentException expected) { }
        // A world point 145 mm below the camera maps to base z = 5..15 range.
        // With identity pose the world -Z direction maps to base -(0.5,0.866,0);
        // pick a point 0.2 m in front of camera along world +X for a valid height.
        // Simpler: use the camera origin minus enough world-Z to land at z=30.
        // World -Z 0.2 m maps to base z: 150 + 0.2*1000*0.7071? Column 2 of R_B_C
        // corresponds to camera +Z; with identity AR pose world +Z == camera +Z,
        // base direction = (-0.612372, 0.353553, 0.707107). So 0.2 m along world
        // -Z gives base z = 150 - 141.4 = 8.6 mm -> inside 5..60.
        double[] target = calib.toPickTargetMm(new double[]{0, 0, -0.2});
        // Z must equal ground (0) + pick offset (10).
        assertEquals(10, target[2], 1e-6);
    }

    @Test
    public void rejectsUseBeforePoseAndBadInput() throws Exception {
        FixedCameraCalibration calib = FixedCameraCalibration.fromAsset(asset());
        try { calib.toRobotMm(new double[]{0, 0, 0}); fail("pose required"); }
        catch (IllegalStateException expected) { }
        try { calib.updatePose(new float[]{0,0}, new float[]{0,0,0,1}); fail("bad translation"); }
        catch (IllegalArgumentException expected) { }
        try { calib.updatePose(new float[]{0,0,0}, new float[]{0,0,0}); fail("bad quaternion"); }
        catch (IllegalArgumentException expected) { }
        try { FixedCameraCalibration.fromAsset(new ByteArrayInputStream("{}".getBytes(StandardCharsets.UTF_8))); fail("bad asset"); }
        catch (Exception expected) { }
    }

    @Test
    public void fixedCameraIsStableAcrossArbitraryPoses() throws Exception {
        FixedCameraCalibration calib = FixedCameraCalibration.fromAsset(asset());
        // A fixed rigid mount means the world->base transform must move rigidly:
        // rotating the camera pose must rotate the composed transform and keep distances.
        calib.updatePose(new float[]{0.1f, -0.2f, 0.3f}, new float[]{0, 0, 0, 1});
        double[] a1 = calib.toRobotMm(new double[]{0.4, 0.2, -0.1});
        double[] b1 = calib.toRobotMm(new double[]{-0.15, 0.33, 0.05});
        double d1 = dist(a1, b1);
        // Rotate the camera pose 90 deg about world Z and recompute; the same
        // world points must stay at the same distance from each other. Float
        // quaternion precision keeps this at ~1e-3 mm, not exact.
        double half = Math.sqrt(0.5);
        calib.updatePose(new float[]{0.1f, -0.2f, 0.3f}, new float[]{0, 0, (float) half, (float) half});
        double[] a2 = calib.toRobotMm(new double[]{0.4, 0.2, -0.1});
        double[] b2 = calib.toRobotMm(new double[]{-0.15, 0.33, 0.05});
        assertEquals(d1, dist(a2, b2), 1e-3);
        // And must not be identical points (rotation actually applied).
        assertTrue(dist(a1, a2) > 1);
    }

    private static double dist(double[] a, double[] b) {
        double dx = a[0]-b[0], dy = a[1]-b[1], dz = a[2]-b[2];
        return Math.sqrt(dx*dx + dy*dy + dz*dz);
    }
}
