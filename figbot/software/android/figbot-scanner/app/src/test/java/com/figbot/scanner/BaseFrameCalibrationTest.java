package com.figbot.scanner;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.assertThrows;

import org.junit.Test;

public class BaseFrameCalibrationTest {
    private static final double EPSILON = 1.0e-9;

    @Test
    public void convertsWorldAxesToRightHandedBaseFrame() {
        BaseFrameCalibration calibration = new BaseFrameCalibration();
        calibration.setOrigin(new Vec3(1.0, 0.5, 2.0));
        calibration.setPositiveXPoint(new Vec3(2.0, 0.5, 2.0));

        Vec3 result = calibration.toBase(new Vec3(1.4, 0.8, 1.7));

        assertEquals(0.4, result.x(), EPSILON);
        assertEquals(0.3, result.y(), EPSILON);
        assertEquals(0.3, result.z(), EPSILON);
    }

    @Test
    public void ignoresHeightDifferenceWhenDefiningPositiveX() {
        BaseFrameCalibration calibration = new BaseFrameCalibration();
        calibration.setOrigin(new Vec3(0, 0, 0));
        calibration.setPositiveXPoint(new Vec3(1, 0.4, 1));

        Vec3 pointOnBaseX = calibration.toBase(new Vec3(0.5, 0, 0.5));

        assertEquals(Math.sqrt(0.5), pointOnBaseX.x(), EPSILON);
        assertEquals(0, pointOnBaseX.y(), EPSILON);
        assertEquals(0, pointOnBaseX.z(), EPSILON);
    }

    @Test
    public void rejectsAxisPointTooCloseToOrigin() {
        BaseFrameCalibration calibration = new BaseFrameCalibration();
        calibration.setOrigin(new Vec3(0, 0, 0));

        assertThrows(IllegalArgumentException.class,
                () -> calibration.setPositiveXPoint(new Vec3(0.01, 1.0, 0.01)));
    }

    @Test
    public void resetInvalidatesCalibration() {
        BaseFrameCalibration calibration = new BaseFrameCalibration();
        calibration.setOrigin(new Vec3(0, 0, 0));
        calibration.setPositiveXPoint(new Vec3(1, 0, 0));
        assertTrue(calibration.isReady());

        calibration.clear();

        assertFalse(calibration.hasOrigin());
        assertFalse(calibration.isReady());
    }
}
