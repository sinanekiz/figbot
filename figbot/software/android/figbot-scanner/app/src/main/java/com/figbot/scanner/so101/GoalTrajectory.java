package com.figbot.scanner.so101;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Endpoint-driven, simultaneous C2 joint trajectories; no taught intermediates.
 * This is joint-space geometry, not Cartesian collision or grasp verification.
 * Nominal jaw opening MUST be gated by measured feedback in the live controller.
 */
public final class GoalTrajectory {
    private static final double PEAK_QUINTIC_VELOCITY = 1.875;
    private static final double PEAK_QUINTIC_ACCELERATION = 10 / Math.sqrt(3);
    private final ArmProfile profile;
    private final List<Segment> segments = new ArrayList<>();
    private final int[] initial;
    private int[] current;
    private double duration, maxSpeed, maxAcceleration;
    private double pickupTime = Double.NaN, basketArrival = Double.NaN;
    private double releaseStart = Double.NaN, releaseEnd = Double.NaN;
    private final int closed, opened;

    public GoalTrajectory(ArmProfile profile, int[] start, int[] pickup, int[] basket, boolean returnHome) {
        this(profile, start);
        profile.validatePose(pickup);
        profile.validatePose(basket);
        int[] grasp = pickup.clone(), release = basket.clone();
        grasp[4] = initial[4]; grasp[5] = closed;
        release[4] = initial[4]; release[5] = opened;
        int[] carry = release.clone(); carry[5] = closed;
        if (armDistance(grasp, release) == 0)
            throw new IllegalArgumentException("Pickup and basket must be distinct arm targets");
        boolean fromHome = armDistance(initial, profile.home()) <= 20;
        appendLeg(grasp, !fromHome, opened, fromHome, profile.speedLimit());
        pickupTime = duration;
        appendLeg(carry, true, closed, false, profile.speedLimit());
        basketArrival = duration;
        double stroke = opened - closed;
        double openDuration = Math.max(.56, Math.max(PEAK_QUINTIC_VELOCITY * stroke / profile.speedLimit(),
                Math.sqrt(PEAK_QUINTIC_ACCELERATION * stroke / (profile.accelerationLimit() * 100.))));
        releaseStart = basketArrival - .18;
        releaseEnd = releaseStart + openDuration;
        appendReleaseHold(release, releaseEnd - basketArrival);
        maxSpeed = Math.max(maxSpeed, PEAK_QUINTIC_VELOCITY * stroke / openDuration);
        maxAcceleration = Math.max(maxAcceleration, PEAK_QUINTIC_ACCELERATION * stroke / (openDuration * openDuration));
        if (returnHome) appendLeg(withPassiveRoll(profile.home()), false, closed, true, profile.speedLimit());
        checkBudget();
    }

    private GoalTrajectory(ArmProfile profile, int[] start) {
        if (profile == null) throw new IllegalArgumentException("Arm profile is required");
        profile.validatePose(start);
        this.profile = profile;
        this.initial = start.clone();
        this.current = start.clone();
        this.closed = profile.gripperClosed();
        this.opened = profile.gripperOpen();
    }

    /** Single supervised home leg, with no release windows or automatic enabling. */
    public static GoalTrajectory moveToHome(ArmProfile profile, int[] start) {
        GoalTrajectory result = new GoalTrajectory(profile, start);
        int[] home = result.withPassiveRoll(profile.home());
        double middleJaw = Math.max(Math.min(start[5], home[5]), Math.min(Math.max(start[5], home[5]), result.closed));
        result.appendLeg(home, false, middleJaw, true, profile.speedLimit());
        result.checkBudget();
        return result;
    }

    /** A single supervised raw target; the wrist-roll encoder remains unchanged. */
    public static GoalTrajectory moveTo(ArmProfile profile, int[] start, int[] target, int speedLimit) {
        requireSpeed(speedLimit);
        GoalTrajectory result = new GoalTrajectory(profile, start);
        profile.validatePose(target);
        int[] finish = result.withPassiveRoll(target);
        result.appendLeg(finish, false, (start[5] + finish[5]) / 2., true, speedLimit);
        result.checkBudget();
        return result;
    }

    public double duration() { return duration; }
    public double pickupTime() { return pickupTime; }
    public double basketArrival() { return basketArrival; }
    public double releaseStart() { return releaseStart; }
    public double releaseEnd() { return releaseEnd; }
    public double maxSpeed() { return maxSpeed; }
    public double maxAcceleration() { return maxAcceleration; }
    public int[] start() { return initial.clone(); }
    public int[] end() { return current.clone(); }

    public int[] sample(double seconds) {
        double[] q = evaluate(seconds, 0);
        int[] raw = new int[6];
        for (int i = 0; i < 6; i++) raw[i] = (int) Math.round(q[i]);
        return raw;
    }
    public double[] velocity(double seconds) { return evaluate(seconds, 1); }
    public double[] acceleration(double seconds) { return evaluate(seconds, 2); }
    public double[] knotTimes() {
        List<Double> times = new ArrayList<>(); times.add(0.);
        for (Segment segment : segments) times.add(segment.start + segment.duration);
        if (Double.isFinite(releaseStart)) times.add(releaseStart);
        Collections.sort(times);
        double[] result = new double[times.size()];
        for (int i = 0; i < result.length; i++) result[i] = times.get(i);
        return result;
    }

    private double[] evaluate(double seconds, int derivative) {
        if (!Double.isFinite(seconds)) throw new IllegalArgumentException("Finite trajectory time is required");
        double t = Math.max(0, Math.min(duration, seconds));
        Segment selected = segments.get(segments.size() - 1);
        for (Segment s : segments) if (t <= s.start + s.duration) { selected = s; break; }
        double[] result = selected.evaluate(t, derivative);
        if (Double.isFinite(releaseStart) && t >= releaseStart && t <= releaseEnd) {
            double span = releaseEnd - releaseStart;
            double u = Math.max(0, Math.min(1, (t - releaseStart) / span));
            double[] c = polynomial(closed, opened, 0, 0, span);
            result[5] = value(derive(c, derivative), u) / Math.pow(span, derivative);
        }
        return result;
    }

    private void appendLeg(int[] targetInput, boolean bow, double middleJaw, boolean homeLeg, int speedLimit) {
        requireSpeed(speedLimit);
        int[] target = withPassiveRoll(targetInput);
        profile.validatePose(target);
        for (int i = 0; i < 6; i++) if (Math.abs(target[i] - current[i]) >= 2048)
            throw new IllegalArgumentException("Leg crosses an ambiguous encoder branch");
        int delta = armDistance(current, target);
        double seconds = Math.max(.3, Math.max(PEAK_QUINTIC_VELOCITY * delta / speedLimit,
                Math.sqrt(PEAK_QUINTIC_ACCELERATION * delta / (profile.accelerationLimit() * 100.))));
        double[] middle = new double[6];
        for (int i = 0; i < 6; i++) middle[i] = (current[i] + target[i]) / 2.;
        if (bow) {
            double shoulderTravel = Math.abs(target[1] - current[1]);
            // At most one eighth of this leg's shoulder travel maintains
            // monotonic quintic halves even for nearby arbitrary targets.
            double clearance = Math.max(0, Math.min(64, Math.min(shoulderTravel / 8., 1024 - shoulderTravel / 2.)));
            middle[1] -= clearance;
        }
        middle[5] = middleJaw;
        double[][] first = new double[6][], second = new double[6][];
        double[] speedCaps = new double[6];
        for (int i = 0; i < 6; i++) {
            speedCaps[i] = homeLeg && (i == 1 || i == 2)
                    ? Math.min(speedLimit, profile.homeJointSpeedLimit()) : speedLimit;
            double velocity = i == 5 ? 0 : PEAK_QUINTIC_VELOCITY * (target[i] - current[i]) / seconds;
            first[i] = polynomial(current[i], middle[i], 0, velocity, seconds / 2);
            second[i] = polynomial(middle[i], target[i], velocity, 0, seconds / 2);
            validatePosition(first[i], current[i], middle[i], i);
            validatePosition(second[i], middle[i], target[i], i);
        }
        double scale = 1;
        for (int i = 0; i < 6; i++) for (double[] c : new double[][]{first[i], second[i]}) {
            double v = absoluteMaximum(derive(c, 1)) / (seconds / 2);
            double a = absoluteMaximum(derive(c, 2)) / Math.pow(seconds / 2, 2);
            scale = Math.max(scale, Math.max(v / speedCaps[i], Math.sqrt(a / (profile.accelerationLimit() * 100.))));
        }
        double half = seconds * scale / 2;
        addSegment(new Segment(duration, half, first));
        addSegment(new Segment(duration, half, second));
        current = target;
    }

    private void appendReleaseHold(int[] target, double seconds) {
        if (!(seconds > 0) || !Double.isFinite(seconds))
            throw new IllegalArgumentException("Invalid release duration");
        double[][] c = new double[6][6];
        for (int i = 0; i < 6; i++) c[i][0] = target[i];
        // The nominal jaw on this span is provided by the independent overlap
        // polynomial, which is validated over its full physical stroke time.
        addSegment(new Segment(duration, seconds, c));
        current = target.clone();
    }

    private void addSegment(Segment s) {
        segments.add(s);
        for (int i = 0; i < 6; i++) {
            maxSpeed = Math.max(maxSpeed, absoluteMaximum(derive(s.c[i], 1)) / s.duration);
            maxAcceleration = Math.max(maxAcceleration, absoluteMaximum(derive(s.c[i], 2)) / (s.duration * s.duration));
        }
        duration += s.duration;
    }

    private int[] withPassiveRoll(int[] pose) {
        ArmProfile.requireRawPose(pose);
        int[] copy = pose.clone(); copy[4] = initial[4]; return copy;
    }
    private static int armDistance(int[] a, int[] b) {
        int maximum = 0; for (int i = 0; i < 4; i++) maximum = Math.max(maximum, Math.abs(a[i] - b[i])); return maximum;
    }
    private void checkBudget() {
        if (!Double.isFinite(duration) || duration <= 0 || duration > 50)
            throw new IllegalArgumentException("Trajectory exceeds finite 50-second budget");
        if (maxSpeed > 3400 + 1e-6 || maxAcceleration > profile.accelerationLimit() * 100. + 1e-5)
            throw new IllegalArgumentException("Trajectory exceeds hardware speed/acceleration cap");
    }
    private static void requireSpeed(int speed) {
        if (speed < 1 || speed > 3400) throw new IllegalArgumentException("Finite speed must be 1..3400");
    }

    private void validatePosition(double[] c, double start, double end, int axis) {
        int[] envelope = profile.envelopes()[axis];
        double lo = Math.max(envelope[0], Math.min(start, end));
        double hi = Math.min(envelope[1], Math.max(start, end));
        List<Double> candidates = roots(derive(c, 1)); candidates.add(0.); candidates.add(1.);
        for (double u : candidates) {
            double p = value(c, u);
            if (p < lo - 1e-7 || p > hi + 1e-7)
                throw new IllegalArgumentException("Generated path overshoots a joint interval");
        }
    }

    private static double[] polynomial(double start, double end, double startVelocity, double endVelocity, double seconds) {
        double delta = end - start, a = startVelocity * seconds, b = endVelocity * seconds;
        return new double[]{start, a, 0, 10 * delta - 6 * a - 4 * b,
                -15 * delta + 8 * a + 7 * b, 6 * delta - 3 * a - 3 * b};
    }
    private static double[] derive(double[] c, int times) {
        double[] result = c;
        for (int count = 0; count < times; count++) {
            double[] next = new double[Math.max(1, result.length - 1)];
            for (int i = 1; i < result.length; i++) next[i - 1] = i * result[i];
            result = next;
        }
        return result;
    }
    private static double value(double[] c, double u) {
        double result = 0; for (int i = c.length - 1; i >= 0; i--) result = result * u + c[i]; return result;
    }
    private static double absoluteMaximum(double[] c) {
        List<Double> points = roots(derive(c, 1)); points.add(0.); points.add(1.);
        double maximum = 0; for (double point : points) maximum = Math.max(maximum, Math.abs(value(c, point))); return maximum;
    }
    /** Isolate all polynomial extrema on [0,1], including repeated roots. */
    private static List<Double> roots(double[] c) {
        int degree = c.length - 1;
        double magnitude = 0; for (double v : c) magnitude = Math.max(magnitude, Math.abs(v));
        double epsilon = Math.max(1e-11, magnitude * 1e-12);
        while (degree > 0 && Math.abs(c[degree]) <= epsilon) degree--;
        List<Double> result = new ArrayList<>();
        if (degree == 0) return result;
        if (degree == 1) {
            double root = -c[0] / c[1]; if (root >= 0 && root <= 1) result.add(root); return result;
        }
        double[] trimmed = new double[degree + 1]; System.arraycopy(c, 0, trimmed, 0, degree + 1);
        List<Double> splits = roots(derive(trimmed, 1)); splits.add(0.); splits.add(1.); Collections.sort(splits);
        for (double u : splits) if (Math.abs(value(trimmed, u)) <= epsilon) addRoot(result, u);
        for (int i = 0; i + 1 < splits.size(); i++) {
            double lo = splits.get(i), hi = splits.get(i + 1), a = value(trimmed, lo), b = value(trimmed, hi);
            if (a * b >= 0 || hi - lo < 1e-12) continue;
            for (int iteration = 0; iteration < 60; iteration++) {
                double mid = (lo + hi) / 2, m = value(trimmed, mid);
                if (a * m <= 0) { hi = mid; } else { lo = mid; a = m; }
            }
            addRoot(result, (lo + hi) / 2);
        }
        Collections.sort(result); return result;
    }
    private static void addRoot(List<Double> roots, double root) {
        for (double existing : roots) if (Math.abs(existing - root) < 1e-9) return;
        roots.add(root);
    }

    private static final class Segment {
        final double start, duration;
        final double[][] c;
        Segment(double start, double duration, double[][] c) { this.start = start; this.duration = duration; this.c = c; }
        double[] evaluate(double time, int derivative) {
            double u = Math.max(0, Math.min(1, (time - start) / duration));
            double[] result = new double[6];
            for (int i = 0; i < 6; i++) result[i] = value(derive(c[i], derivative), u) / Math.pow(duration, derivative);
            return result;
        }
    }
}
