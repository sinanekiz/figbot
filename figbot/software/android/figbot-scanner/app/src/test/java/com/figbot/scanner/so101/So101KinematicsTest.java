package com.figbot.scanner.so101;

import org.junit.Test;
import java.util.Arrays;
import static org.junit.Assert.*;

public class So101KinematicsTest {
    private final ArmProfile profile = ArmProfile.unverifiedDefaults();
    private final So101Kinematics kinematics = new So101Kinematics(profile);

    @Test public void geometricPrefilterRejectsDistantVisionCandidateWithoutDiscardingNearbyFruit(){
        double[] distant={1030,-535,-37},fruit={200,-140,-40};
        assertFalse(kinematics.withinGeometricReach(distant));
        assertTrue(kinematics.withinGeometricReach(fruit));
        assertEquals("Target is outside the geometric reach bound",
                assertThrows(IllegalArgumentException.class,()->kinematics.inverse(distant,0,profile.home())).getMessage());
        assertArrayEquals(new double[]{200,-140,-40},fruit,0);
    }

    @Test public void geometricSphereStaysInBaseFrameRegardlessOfMeasuredGround(){
        var raised=new So101Kinematics(profile.withGroundZMm(-65));
        for(double[] xyz:new double[][]{{200,-140,-40},{450,0,0},{0,0,-400},{600,0,0},{1030,-535,-37}})
            assertEquals(kinematics.withinGeometricReach(xyz),raised.withinGeometricReach(xyz));
        assertTrue(raised.withinGeometricReach(new double[]{200,-140,-40}));
        // The sphere alone deliberately makes no tabletop-clearance claim.
        assertTrue(raised.withinGeometricReach(new double[]{0,0,-400}));
        assertFalse(raised.withinGeometricReach(new double[]{600,0,0}));
    }

    @Test public void geometricPrefilterRejectsMalformedOrNonfiniteCoordinates(){
        assertFalse(kinematics.withinGeometricReach(null));
        assertFalse(kinematics.withinGeometricReach(new double[0]));
        assertFalse(kinematics.withinGeometricReach(new double[2]));
        assertFalse(kinematics.withinGeometricReach(new double[4]));
        for(double value:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY})
            for(int axis=0;axis<3;axis++){
                double[] xyz={200,-140,-40};xyz[axis]=value;
                assertFalse(kinematics.withinGeometricReach(xyz));
                assertEquals("Target contains a nonfinite coordinate",
                        assertThrows(IllegalArgumentException.class,()->kinematics.inverse(xyz,0,profile.home())).getMessage());
            }
        assertFalse(kinematics.withinGeometricReach(new double[]{Double.MAX_VALUE,Double.MAX_VALUE,0}));
    }

    @Test public void forwardMatchesPythonVendorUrdfFixturesInMillimetres() {
        // Generated with software/st3215_test/cartesian.py + the pinned vendor
        // URDF and cartesian_reference.json; these are model, not physical, data.
        int[][] raw = {
                {1971, 921, 3946, 2681, 3129, 791},
                {2308, 2871, 2337, 1864, 3127, 894},
                {3363, 2177, 2602, 2593, 3125, 1153},
                {2390, 2700, 2490, 1930, 3127, 894},
                {2100, 1600, 3200, 2200, 3130, 950}
        };
        double[][] expected = {
                {157.36459503890038, 12.235877350610682, 7.340423186143433, -1.1336055469648294},
                {411.7221983684636, -184.81272068168025, -4.866286526775891, -.40343202383072263},
                {-118.070844056144, -285.46114918310894, 126.72386075984127, -.8636273408743181},
                {380.36267525071196, -226.52291570446312, 18.121422915287408, -.47706338749520966},
                {312.8295276456086, -36.303021573964, 207.56331700931622, -.29298459446306396}
        };
        for (int i = 0; i < raw.length; i++) assertArrayEquals(expected[i], kinematics.forward(raw[i]), 1e-7);
    }

    @Test public void inverseSolvesReachablePoseWithPassiveRollAndJawPreserved() {
        int[] seed = {2308, 2871, 2337, 1864, 3127, 1153};
        int[] target = {2390, 2700, 2490, 1930, 3127, 894};
        checkInverse(seed, target);
    }

    @Test public void inverseAcceptsMeasuredBasketSeedOutsideVendorPanLimit() {
        // The measured raw basket may be used as a numerical seed, but the
        // returned IK pose must be inside both the model and profile bounds.
        int[] seed = profile.basket();
        int[] target = {2390, 2700, 2490, 1930, seed[4], 894};
        checkInverse(seed, target);
    }

    @Test public void inverseSolvesDistinctReachableConfigurations() {
        int[][] targets = {
                {2100, 1600, 3200, 2200, 3129, 950},
                {2150, 2000, 2900, 2100, 3129, 950},
                {2700, 2450, 2600, 2100, 3129, 950}
        };
        for (int[] target : targets) checkInverse(profile.home(), target);
    }

    private void checkInverse(int[] seed, int[] target) {
        double[] desired = kinematics.forward(target);
        int[] solved = kinematics.inverse(Arrays.copyOf(desired, 3), desired[3], seed);
        double[] achieved = kinematics.forward(solved);
        double error = Math.hypot(Math.hypot(achieved[0] - desired[0], achieved[1] - desired[1]), achieved[2] - desired[2]);
        assertTrue("XYZ residual " + error, error <= So101Kinematics.POSITION_TOLERANCE_MM);
        assertEquals(desired[3], achieved[3], So101Kinematics.PITCH_TOLERANCE_RADIANS);
        assertEquals(seed[4], solved[4]); assertEquals(seed[5], solved[5]);
        profile.validatePose(solved);
        double[] ref = profile.referenceRadians(); int[] raw0 = profile.referenceRaw();
        double[][] limits = {{-1.91986, 1.91986}, {-1.74533, 1.74533}, {-1.69, 1.69}, {-1.65806, 1.65806}};
        for (int i = 0; i < 4; i++) {
            double angle = ref[i] + (solved[i] - raw0[i]) * 2 * Math.PI / 4096;
            assertTrue(angle >= limits[i][0] && angle <= limits[i][1]);
        }
    }

    @Test public void invalidAndUnreachableTargetsCannotProduceMotorGoals() {
        assertThrows(IllegalArgumentException.class, () -> kinematics.inverse(new double[]{10000, 0, 0}, 0, profile.home()));
        assertThrows(IllegalArgumentException.class, () -> kinematics.inverse(new double[]{Double.NaN, 0, 0}, 0, profile.home()));
        assertThrows(IllegalArgumentException.class, () -> kinematics.inverse(new double[]{0, 0, 0}, Math.PI, profile.home()));
        int[] wrongBranch = profile.home(); wrongBranch[4] = 112;
        assertThrows(IllegalArgumentException.class, () -> kinematics.forward(wrongBranch));
        int[] outOfRange = profile.home(); outOfRange[0] = 4096;
        assertThrows(IllegalArgumentException.class, () -> kinematics.forward(outOfRange));
    }
}
