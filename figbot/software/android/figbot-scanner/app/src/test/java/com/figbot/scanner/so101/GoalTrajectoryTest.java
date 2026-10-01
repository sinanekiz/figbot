package com.figbot.scanner.so101;

import org.junit.Test;
import static org.junit.Assert.*;

public class GoalTrajectoryTest {
    private final ArmProfile profile = ArmProfile.unverifiedDefaults();
    private final int[] pickup = {2308, 2871, 2337, 1864, 3127, 894};

    @Test public void autonomousCycleStartsAtBasketAndClosesDuringPickupApproach() {
        GoalTrajectory p = new GoalTrajectory(profile, profile.basket(), pickup, profile.basket(), false);
        assertArrayEquals(profile.basket(), p.sample(0));
        assertEquals(profile.gripperOpen(), p.sample(p.pickupTime() / 2)[5]);
        int approachingJaw = p.sample(p.pickupTime() * .75)[5];
        assertTrue(approachingJaw > profile.gripperClosed() && approachingJaw < profile.gripperOpen());
        assertEquals(profile.gripperClosed(), p.sample(p.pickupTime())[5]);
        for (int i = 0; i < 4; i++) assertEquals(pickup[i], p.sample(p.pickupTime())[i]);
        assertEquals(.18, p.basketArrival() - p.releaseStart(), 1e-9);
        assertEquals(.56, p.releaseEnd() - p.releaseStart(), 1e-9);
        assertEquals(p.releaseEnd(), p.duration(), 1e-9);
        assertArrayEquals(profile.basket(), p.sample(p.duration()));
        assertEquals(profile.gripperClosed(), p.sample((p.pickupTime() + p.releaseStart()) / 2)[5]);
        assertTrue(p.sample(p.basketArrival())[5] > profile.gripperClosed());
    }

    @Test public void generatedCurveHasContinuousVelocityAndAccelerationAtAllKnots() {
        GoalTrajectory p = new GoalTrajectory(profile, profile.home(), pickup, profile.basket(), true);
        for (double knot : p.knotTimes()) if (knot > 1e-5 && knot < p.duration() - 1e-5) {
            assertArrayEquals(p.velocity(knot - 1e-7), p.velocity(knot + 1e-7), .01);
            assertArrayEquals(p.acceleration(knot - 1e-7), p.acceleration(knot + 1e-7), .2);
        }
        assertArrayEquals(new double[6], p.velocity(0), 1e-7);
        assertArrayEquals(new double[6], p.velocity(p.duration()), 1e-7);
        assertArrayEquals(new double[6], p.acceleration(0), 1e-7);
        assertArrayEquals(new double[6], p.acceleration(p.duration()), 1e-7);
    }

    @Test public void arbitraryNearbyShoulderTargetsDoNotOvershootWithClearanceBow() {
        int[] closePickup = profile.basket(); closePickup[0] -= 163; closePickup[1] += 8;
        closePickup[2] += 8; closePickup[3] += 8;
        GoalTrajectory p = new GoalTrajectory(profile, profile.basket(), closePickup, profile.basket(), false);
        for (int i = 0; i <= 1000; i++) {
            int[] raw = p.sample(p.duration() * i / 1000.);
            assertTrue(raw[1] >= profile.basket()[1] && raw[1] <= closePickup[1]);
        }
    }

    @Test public void simultaneousSingleLegHasOneMinimumJerkTimeLaw() {
        int[] start = profile.home(), target = {2350, 2000, 3200, 2300, 3130, 791};
        GoalTrajectory p = GoalTrajectory.moveTo(profile, start, target, 1200);
        for (double fraction : new double[]{.1, .3, .5, .7, .9}) {
            double blend = 10 * Math.pow(fraction, 3) - 15 * Math.pow(fraction, 4) + 6 * Math.pow(fraction, 5);
            int[] actual = p.sample(fraction * p.duration());
            for (int i = 0; i < 4; i++) assertEquals(start[i] + blend * (target[i] - start[i]), actual[i], .51);
        }
        double[] peak = p.velocity(p.duration() / 2);
        for (int i = 0; i < 4; i++) assertEquals(1.875 * (target[i] - start[i]) / p.duration(), peak[i], 1e-7);
        assertTrue(Double.isNaN(p.pickupTime())); assertTrue(Double.isNaN(p.releaseStart()));
        assertEquals(start[4], p.sample(p.duration())[4]);
    }

    @Test public void extremaAndSamplesRespectFiniteMotorAndEnvelopeLimits() {
        GoalTrajectory p = new GoalTrajectory(profile, profile.home(), pickup, profile.basket(), true);
        int[][] bounds = profile.envelopes();
        assertTrue(p.maxSpeed() <= 1200.00001);
        assertTrue(p.maxAcceleration() <= 5000.00001);
        for (int n = 0; n <= 2000; n++) {
            double t = p.duration() * n / 2000.;
            int[] raw = p.sample(t); double[] velocity = p.velocity(t), acceleration = p.acceleration(t);
            for (int i = 0; i < 6; i++) {
                assertTrue(raw[i] >= bounds[i][0] && raw[i] <= bounds[i][1]);
                assertTrue(Math.abs(velocity[i]) <= 1200.0001);
                assertTrue(Math.abs(acceleration[i]) <= 5000.0001);
            }
            assertEquals(profile.home()[4], raw[4]);
        }
        int[] expectedHome = profile.home();
        assertArrayEquals(expectedHome, p.sample(p.duration()));
    }

    @Test public void homeOnlyLegHasNoReleaseWindowAndKeepsHomeAxisCap() {
        GoalTrajectory p = GoalTrajectory.moveToHome(profile, profile.basket());
        assertTrue(Double.isNaN(p.pickupTime())); assertTrue(Double.isNaN(p.basketArrival()));
        assertTrue(Double.isNaN(p.releaseStart())); assertTrue(Double.isNaN(p.releaseEnd()));
        for (int i = 0; i < 501; i++) {
            double[] speed = p.velocity(i * p.duration() / 500.);
            assertTrue(Math.abs(speed[1]) <= 1000.0001);
            assertTrue(Math.abs(speed[2]) <= 1000.0001);
        }
        int[] expected = profile.home(); expected[4] = profile.basket()[4];
        assertArrayEquals(expected, p.sample(p.duration()));
    }

    @Test public void alreadyHomeDoesNotOpenAndRecloseJaw() {
        GoalTrajectory p = GoalTrajectory.moveToHome(profile, profile.home());
        for (int i = 0; i <= 20; i++) assertArrayEquals(profile.home(), p.sample(p.duration() * i / 20.));
    }

    @Test public void invalidTargetsAndEncoderBranchJumpsAreRejected() {
        int[] invalid = pickup.clone(); invalid[2] = 4096;
        assertThrows(IllegalArgumentException.class, () -> new GoalTrajectory(profile, profile.basket(), invalid, profile.basket(), false));
        assertThrows(IllegalArgumentException.class, () -> GoalTrajectory.moveTo(profile, profile.home(), pickup, 0));
        int[] low = profile.home(), high = profile.home(); low[1] = 751; high[1] = 2891;
        assertThrows(IllegalArgumentException.class, () -> GoalTrajectory.moveTo(profile, low, high, 1200));
        GoalTrajectory p = GoalTrajectory.moveToHome(profile, profile.basket());
        assertThrows(IllegalArgumentException.class, () -> p.sample(Double.NaN));
        assertArrayEquals(p.start(), p.sample(-1));
        assertArrayEquals(p.end(), p.sample(p.duration() + 10));
    }
}
