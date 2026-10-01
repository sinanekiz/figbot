package com.figbot.scanner.so101;

import org.junit.Test;
import java.util.Arrays;
import java.util.List;
import static org.junit.Assert.*;

/** Synthetic numerical evidence tests; none claims real arm measurement. */
public class ArmValidationTest {
    private final ArmProfile profile = ArmProfile.unverifiedDefaults();
    private final So101Kinematics model = new So101Kinematics(profile);
    private final int[][] spread = {
            {1971, 921, 3946, 2681, 3129, 791},
            {2308, 2871, 2337, 1864, 3127, 894},
            {3363, 2177, 2602, 2593, 3125, 1153}
    };
    private double[] point(int[] raw) { return Arrays.copyOf(model.forward(raw), 3); }

    @Test public void threeMatchingSpreadMeasurementsAreRequired() {
        ArmValidation validation = new ArmValidation(profile, 8);
        assertFalse(validation.isValid());
        validation.add(spread[0], point(spread[0])); assertFalse(validation.isValid());
        validation.add(spread[1], point(spread[1])); assertFalse(validation.isValid());
        validation.add(spread[2], point(spread[2])); assertTrue(validation.isValid());
        assertFalse("Numerical validation must not mutate the caller profile", profile.physicalCalibrationVerified());
        validation.clear();
        assertFalse(validation.isValid()); assertTrue(validation.measurements().isEmpty());
    }

    @Test public void aPhysicalFlagCannotInventMeasurementEvidence() {
        ArmValidation validation = new ArmValidation(profile.withPhysicalCalibrationVerified(true), 8);
        assertFalse(validation.isValid());
        double[] wrong = point(spread[0]); wrong[0] += 20;
        assertThrows(IllegalArgumentException.class, () -> validation.add(spread[0], wrong));
        assertFalse(validation.isValid());
        assertEquals(0, validation.measurements().size());
    }

    @Test public void mismatchAndDuplicateRejectionsDoNotCountAsNewEvidence() {
        ArmValidation validation = new ArmValidation(profile, 8);
        validation.add(spread[0], point(spread[0]));
        assertThrows(IllegalArgumentException.class, () -> validation.add(spread[0], point(spread[0])));
        double[] wrong = point(spread[1]); wrong[2] += 8.01;
        assertThrows(IllegalArgumentException.class, () -> validation.add(spread[1], wrong));
        assertEquals(1, validation.measurements().size()); assertFalse(validation.isValid());
        double[] accepted = point(spread[1]); accepted[2] += 7.5;
        assertEquals(7.5, validation.add(spread[1], accepted), 1e-8);
        assertFalse(validation.isValid());
    }

    @Test public void threeSeparatedPointsWithInsufficientSpanRemainInvalid() {
        ArmValidation validation = new ArmValidation(profile, 8);
        int[][] raw = {profile.home(), profile.home(), profile.home()};
        raw[0][0] = 1905; raw[1][0] = 2055; raw[2][0] = 2205;
        assertTrue(ArmValidation.distance(point(raw[0]), point(raw[1])) >= 20);
        assertTrue(ArmValidation.distance(point(raw[0]), point(raw[2])) < 80);
        for (int[] pose : raw) validation.add(pose, point(pose));
        assertEquals(3, validation.measurements().size()); assertFalse(validation.isValid());
    }

    @Test public void collinearMeasurementsCannotValidateAWorkspaceEvenWithEnoughSpan() {
        ArmValidation validation = new ArmValidation(profile, 8);
        int[][] raw = {profile.home(), profile.home(), profile.home()};
        raw[0][0] = 1905; raw[1][0] = 2145; raw[2][0] = 2385;
        double[] first = point(raw[0]), last = point(raw[2]), midpoint = new double[3];
        for (int i = 0; i < 3; i++) midpoint[i] = (first[i] + last[i]) / 2;
        // The synthetic midpoint lies within 8mm of this short circular arc,
        // but measured points themselves are collinear and prove no area.
        assertTrue(ArmValidation.distance(first, last) >= 80);
        assertTrue(ArmValidation.distance(point(raw[1]), midpoint) < 8);
        validation.add(raw[0], first); validation.add(raw[1], midpoint); validation.add(raw[2], last);
        assertEquals(3, validation.measurements().size()); assertFalse(validation.isValid());
    }

    @Test public void evidenceArraysAndReturnedListAreImmutableCopies() {
        ArmValidation validation = new ArmValidation(profile, 8);
        int[] raw = spread[0].clone(); double[] xyz = point(raw);
        validation.add(raw, xyz); raw[0] = 0; xyz[0] = 0;
        List<ArmValidation.Measurement> saved = validation.measurements();
        assertEquals(spread[0][0], saved.get(0).raw()[0]);
        assertEquals(point(spread[0])[0], saved.get(0).measuredMm()[0], 1e-9);
        saved.get(0).raw()[0] = 0; saved.get(0).measuredMm()[0] = 0;
        assertEquals(spread[0][0], validation.measurements().get(0).raw()[0]);
        assertThrows(UnsupportedOperationException.class, saved::clear);
    }

    @Test public void invalidUnitsShapesAndNonfiniteMeasurementsCannotValidate() {
        ArmValidation validation = new ArmValidation(profile, 8);
        double[] metres = point(spread[0]); for (int i = 0; i < 3; i++) metres[i] /= 1000;
        assertThrows(IllegalArgumentException.class, () -> validation.add(spread[0], metres));
        assertThrows(IllegalArgumentException.class, () -> validation.add(spread[0], new double[]{Double.NaN, 0, 0}));
        assertThrows(IllegalArgumentException.class, () -> validation.add(new int[3], new double[3]));
        for (double tolerance : new double[]{0, -1, 10.01, Double.NaN, Double.POSITIVE_INFINITY})
            assertThrows(IllegalArgumentException.class, () -> new ArmValidation(profile, tolerance));
        assertFalse(validation.isValid()); assertTrue(validation.measurements().isEmpty());
    }
}
