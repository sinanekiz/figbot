package com.figbot.scanner.so101;

import org.junit.Test;
import static org.junit.Assert.*;

public class ArmProfileTest {
    @Test public void passiveRollCanBeObservedAcrossZeroWithoutChangingActiveAxisBranches() {
        ArmProfile p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] q=p.home();q[4]=1152;p.validatePose(q);
        assertTrue(p.withPhysicalCalibrationVerified(true).passiveWristRoll());
        So101Kinematics k=new So101Kinematics(p);
        q[4]=0;double[][] a=k.forwardTransform(q);q[4]=4095;double[][] b=k.forwardTransform(q);
        assertTrue(com.figbot.scanner.vision.RigidPose.fromMatrix(a).angle(
                com.figbot.scanner.vision.RigidPose.fromMatrix(b))<.002);
        q[2]=0;assertThrows(IllegalArgumentException.class,()->k.forwardTransform(q));
    }
    @Test public void outsideTravelErrorIdentifiesJointValueAndRecovery() {
        ArmProfile p=ArmProfile.unverifiedDefaults();int[] q=p.home();q[2]=4000;
        String error=assertThrows(IllegalArgumentException.class,()->p.validatePose(q)).getMessage();
        assertTrue(error.contains("Dirsek (ID3)"));assertTrue(error.contains("4000"));
        assertTrue(error.contains("2315–3974"));assertTrue(error.contains("Elle ölçüm"));
    }
    @Test public void bundledPhysicalCalibrationIsExplicitlyUnverified() {
        ArmProfile p = ArmProfile.unverifiedDefaults();
        assertFalse(p.physicalCalibrationVerified());
        assertTrue(p.calibrationStatus().contains("UNVERIFIED"));
        assertArrayEquals(new int[]{4080, 2861, 85, 85, 85, 85}, p.offsets());
        assertEquals(4208, p.referenceRaw()[4]);
        assertEquals(1200, p.speedLimit());
        assertEquals(1000, p.homeJointSpeedLimit());
        assertEquals(50, p.accelerationLimit());
    }

    @Test public void returnedArraysCannotMutateTheProfile() {
        ArmProfile p = ArmProfile.unverifiedDefaults();
        p.home()[0] = 0; p.offsets()[0] = 0; p.referenceRaw()[0] = 0;
        p.referenceRadians()[0] = 42; p.directionSigns()[0] = -1;
        p.envelopes()[0][0] = 0;
        assertEquals(1971, p.home()[0]);
        assertEquals(4080, p.offsets()[0]);
        assertEquals(1996, p.referenceRaw()[0]);
        assertEquals(0, p.referenceRadians()[0], 0);
        assertEquals(1, p.directionSigns()[0]);
        assertEquals(1905, p.envelopes()[0][0]);
    }

    @Test public void savingTaskPosesDoesNotVerifyPhysicalCalibration() {
        ArmProfile p = ArmProfile.unverifiedDefaults();
        int[] home = p.home(), basket = p.basket(); home[0] += 5;
        ArmProfile saved = p.withSavedPoses(home, basket, 900, 1180);
        home[0] = 0;
        assertEquals(1976, saved.home()[0]);
        assertEquals(900, saved.gripperClosed());
        assertEquals(1180, saved.gripperOpen());
        assertFalse(saved.physicalCalibrationVerified());
        assertTrue(saved.withPhysicalCalibrationVerified(true).physicalCalibrationVerified());
        assertFalse(saved.physicalCalibrationVerified());
    }

    @Test public void recordedSessionValidationKeepsMapAndRequiresProvenance() {
        ArmProfile p = ArmProfile.unverifiedDefaults();
        ArmProfile test = p.withRecordedSessionValidation("RECORDED_SESSION_2026_09_20_21");
        // Travel gate opens, but the same recorded encoder map is preserved untouched.
        assertTrue(test.physicalCalibrationVerified());
        assertTrue(test.calibrationStatus().contains("RECORDED_SESSION_2026_09_20_21"));
        assertArrayEquals(p.offsets(), test.offsets());
        assertArrayEquals(p.referenceRaw(), test.referenceRaw());
        assertArrayEquals(p.directionSigns(), test.directionSigns());
        assertArrayEquals(p.home(), test.home());
        assertArrayEquals(p.basket(), test.basket());
        assertEquals(p.gripperClosed(), test.gripperClosed());
        assertEquals(p.gripperOpen(), test.gripperOpen());
        assertEquals(1200, test.speedLimit());
        // Bundled default stays explicitly unverified; only the derived test profile opens.
        assertFalse(p.physicalCalibrationVerified());
        assertThrows(IllegalArgumentException.class,
                () -> p.withRecordedSessionValidation("  "));
    }

    @Test public void relaxedWristRollEnvelopeAcceptsAnyInBranchRestingPose() {
        ArmProfile p = ArmProfile.unverifiedDefaults();
        // The recorded window is 46 counts wide; a hand-repositioned wrist resting at
        // raw 3080 must not block planning in the follow app (roll stays passive).
        assertThrows(IllegalArgumentException.class, () -> {
            int[] rest = p.home(); rest[4] = 3080; p.validatePose(rest);
        });
        ArmProfile relaxed = p.withWristRollEnvelope(0, 4095);
        assertEquals(2161, relaxed.envelopes()[4][0]);
        assertEquals(4095, relaxed.envelopes()[4][1]);
        int[] rest = relaxed.home(); rest[4] = 3080;
        relaxed.validatePose(rest);          // in-branch resting pose is now plannable
        int[] crossBranch = relaxed.home(); crossBranch[4] = 100;   // reference branch is 4208
        assertThrows(IllegalArgumentException.class, () -> relaxed.validatePose(crossBranch));
        // Other joints and the home/basket poses stay identical and validated.
        assertArrayEquals(p.envelopes()[0], relaxed.envelopes()[0]);
        assertArrayEquals(p.envelopes()[5], relaxed.envelopes()[5]);
        assertArrayEquals(p.home(), relaxed.home());
        assertArrayEquals(p.basket(), relaxed.basket());
        assertThrows(IllegalArgumentException.class, () -> p.withWristRollEnvelope(3000, 2000));
    }

    @Test public void invalidSavedEnvelopeAndReversedJawWidthsAreRejected() {
        ArmProfile p = ArmProfile.unverifiedDefaults();
        int[] invalid = p.home(); invalid[1] = 0;
        assertThrows(IllegalArgumentException.class, () -> p.withSavedPoses(invalid, p.basket(), 894, 1153));
        assertThrows(IllegalArgumentException.class, () -> p.withSavedPoses(p.home(), p.basket(), 1153, 894));
        assertThrows(IllegalArgumentException.class, () -> ArmProfile.requireRawPose(new int[]{1, 2, 3}));
    }

    @Test public void measuredWorkplaneChangesNoEncoderGeometryOrCalibrationEvidence() {
        ArmProfile original=ArmProfile.unverifiedDefaults();
        assertEquals(0,original.groundZMm(),0);
        ArmProfile raisedBase=original.withGroundZMm(-65);
        assertEquals(-65,raisedBase.groundZMm(),0);
        assertEquals(0,original.groundZMm(),0);
        assertArrayEquals(original.offsets(),raisedBase.offsets());
        assertArrayEquals(original.referenceRaw(),raisedBase.referenceRaw());
        assertArrayEquals(original.referenceRadians(),raisedBase.referenceRadians(),0);
        assertArrayEquals(original.directionSigns(),raisedBase.directionSigns());
        for(int i=0;i<6;i++)assertArrayEquals(original.envelopes()[i],raisedBase.envelopes()[i]);
        assertArrayEquals(original.home(),raisedBase.home());assertArrayEquals(original.basket(),raisedBase.basket());
        assertEquals(original.calibrationStatus(),raisedBase.calibrationStatus());
        assertFalse(raisedBase.physicalCalibrationVerified());
        assertArrayEquals(new So101Kinematics(original).forward(original.home()),
                new So101Kinematics(raisedBase).forward(original.home()),0);
    }

    @Test public void allDerivedProfilesPreserveMeasuredWorkplane() {
        ArmProfile p=ArmProfile.unverifiedDefaults().withGroundZMm(-65);
        int[] ingress=p.home();ingress[0]=p.envelopes()[0][0]-4;
        ArmProfile[] copies={p.withSavedPoses(p.home(),p.basket(),870,1153),
                p.withPhysicalCalibrationVerified(true),p.withPhysicalCalibrationVerified(false),
                p.withRecordedSessionValidation("recorded evidence"),
                p.withWristRollEnvelope(0,4095),p.withPassiveWristRoll(),p.calibrationIngress(ingress)};
        for(ArmProfile copy:copies)assertEquals(-65,copy.groundZMm(),0);
        assertEquals(-65,p.withPassiveWristRoll().withSavedPoses(p.home(),p.basket(),870,1153)
                .withPhysicalCalibrationVerified(true).calibrationIngress(ingress).groundZMm(),0);
    }

    @Test public void gripperEncoderSettingsRemainCompatibleAfterWorkplaneChange() {
        ArmProfile original=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        var settings=GripperSettings.from(original,870,1153,"Explicit endpoints");
        ArmProfile raisedBase=original.withGroundZMm(-65);
        ArmProfile applied=GripperSettings.decode(raisedBase,settings.encode()).apply(raisedBase);
        assertEquals(-65,applied.groundZMm(),0);
        assertEquals(870,applied.gripperClosed());
        assertTrue(applied.passiveWristRoll());
    }

    @Test public void nonfiniteOrImplausiblyLargeWorkplanesAreRejected() {
        ArmProfile p=ArmProfile.unverifiedDefaults();
        for(double value:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,-1500.001,1500.001})
            assertThrows(IllegalArgumentException.class,()->p.withGroundZMm(value));
        assertEquals(-1500,p.withGroundZMm(-1500).groundZMm(),0);
        assertEquals(1500,p.withGroundZMm(1500).groundZMm(),0);
        assertEquals(0,p.groundZMm(),0);
    }
}
