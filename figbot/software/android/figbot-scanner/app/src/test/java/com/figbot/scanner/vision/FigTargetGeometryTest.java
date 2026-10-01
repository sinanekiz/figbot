package com.figbot.scanner.vision;

import org.junit.Test;
import static org.junit.Assert.*;

public class FigTargetGeometryTest {
    private final RigidPose down = new RigidPose(
            new double[][]{{1,0,0},{0,-1,0},{0,0,-1}}, new double[]{100,200,300});

    @Test public void stationaryStartupUsesKnownMetricPlaneWithoutArWorldOrMotion() {
        var m = FigTargetGeometry.resolve(true, down, 320,240,500,500,320,240,0,25);
        assertNotNull(m);
        assertEquals(300, m.cameraRangeMm(), 1e-9);
        assertEquals(100, m.xMm(), 1e-9);
        assertEquals(200, m.yMm(), 1e-9);
        assertEquals(0, m.surfaceZMm(), 1e-9);
        assertEquals(25, m.gripZMm(), 1e-9);
    }
    @Test public void unvalidatedSavedReferenceDoesNotProduceRangeOrRobotTarget() {
        assertNull(FigTargetGeometry.resolve(false, down, 320,240,500,500,320,240,0,25));
        assertNull(FigTargetGeometry.resolve(true, null, 320,240,500,500,320,240,0,25));
    }
    @Test public void rangeMeasuresSurfaceContactNotRaisedGraspPoint() {
        var m = FigTargetGeometry.resolve(true, down, 420,290,500,500,320,240,-65,25);
        assertNotNull(m);
        assertEquals(173, m.xMm(), 1e-9);
        assertEquals(163.5, m.yMm(), 1e-9);
        assertEquals(-40, m.gripZMm(), 1e-9);
        assertEquals(Math.sqrt(73*73+36.5*36.5+365*365), m.cameraRangeMm(), 1e-9);
    }
    @Test public void invalidOrHorizonRayHasNoFallbackTarget() {
        assertNull(FigTargetGeometry.resolve(true, RigidPose.identity(),320,240,500,500,320,240,0,25));
        assertNull(FigTargetGeometry.resolve(true, down,Double.NaN,240,500,500,320,240,0,25));
        assertNull(FigTargetGeometry.resolve(true, down,320,240,0,500,320,240,0,25));
        assertNull(FigTargetGeometry.resolve(true, down,320,240,500,500,320,240,400,25));
    }
    @Test public void referenceLossImmediatelyInvalidatesPreviouslyMeasurableTarget() {
        assertNotNull(FigTargetGeometry.resolve(true, down,320,240,500,500,320,240,0,25));
        assertNull(FigTargetGeometry.resolve(false, down,320,240,500,500,320,240,0,25));
    }
}
