package com.figbot.scanner.so101;

/** Pure SO-101 vendor-URDF kinematics. Units: millimetres and radians.
 * Geometry does not imply verified physical calibration or collision clearance.
 */
public final class So101Kinematics {
    public static final double POSITION_TOLERANCE_MM = 2.0;
    public static final double PITCH_TOLERANCE_RADIANS = .035;
    private static final double COUNT_RAD = 2 * Math.PI / 4096;
    // Exact decimal origins from so101_new_calib.urdf; tiny values are retained.
    private static final double[][] ORIGINS = {
            {.0388353, -8.97657e-9, .0624, 3.14159, 4.18253e-17, -3.14159},
            {-.0303992, -.0182778, -.0542, -1.5708, -1.5708, 0},
            {-.11257, -.028, 1.73763e-16, -3.63608e-16, 8.74301e-16, 1.5708},
            {-.1349, .0052, 3.62355e-17, 4.02456e-15, 8.67362e-16, -1.5708},
            {5.55112e-17, -.0611, .0181, 1.5708, .0486795, 3.14159}
    };
    private static final double[] TIP = {-.0079, -.000218121, -.0981274, 0, 3.14159, 0};
    private static final double[][] LIMITS = {
            {-1.91986, 1.91986}, {-1.74533, 1.74533}, {-1.69, 1.69},
            {-1.65806, 1.65806}, {-2.74385, 2.84121}
    };
    private final ArmProfile profile;
    private final int[] raw0, signs;
    private final double[] q0;
    private final double[][][] origins = new double[5][][];
    private final double[][] tip = origin(TIP);
    private final double maximumReachMm;

    public So101Kinematics(ArmProfile profile) {
        if (profile == null) throw new IllegalArgumentException("Arm profile is required");
        this.profile = profile;
        raw0 = profile.referenceRaw();
        q0 = profile.referenceRadians();
        signs = profile.directionSigns();
        double reach = norm3(TIP);
        for (int i = 0; i < 5; i++) {
            origins[i] = origin(ORIGINS[i]);
            reach += norm3(ORIGINS[i]);
        }
        maximumReachMm = reach * 1000;
    }

    /** FK accepts measured poses outside model joint limits, but never wraps encoders. */
    public double[] forward(int[] raw6) {
        return pose(angles(raw6));
    }

    /** Vendor tool frame -> base, translation in mm. Does not certify encoder calibration. */
    public double[][] forwardTransform(int[] raw6) {
        double[] q = angles(raw6);
        double[][] t = identity();
        for (int i=0;i<5;i++) t=multiply(multiply(t,origins[i]),rotationZ(q[i]));
        t=multiply(t,tip);
        for(int i=0;i<3;i++) t[i][3]*=1000;
        return t;
    }

    /** Cheap necessary reach bound in the unchanged robot base frame. True does
     * not prove joint-limited IK, tabletop clearance, or a collision-free path. */
    public boolean withinGeometricReach(double[] xyzMm) {
        if(xyzMm==null||xyzMm.length!=3)return false;
        for(double value:xyzMm)if(!Double.isFinite(value))return false;
        return norm3(xyzMm)<=maximumReachMm+POSITION_TOLERANCE_MM;
    }

    /** Solve four bounded axes; wrist roll and gripper stay exactly at the seed. */
    public int[] inverse(double[] xyzMm, double pitch, int[] seed) {
        if (xyzMm == null || xyzMm.length != 3 || !Double.isFinite(pitch)
                || Math.abs(pitch) > Math.PI / 2 + 1e-9)
            throw new IllegalArgumentException("Finite XYZ millimetres and tool pitch are required");
        for (double v : xyzMm) if (!Double.isFinite(v))
            throw new IllegalArgumentException("Target contains a nonfinite coordinate");
        if (!withinGeometricReach(xyzMm))
            throw new IllegalArgumentException("Target is outside the geometric reach bound");
        profile.validatePose(seed);
        double[] seedQ = angles(seed);
        int[][] envelopes = profile.envelopes();
        double[] lo = new double[4], hi = new double[4], initial = new double[4];
        for (int i = 0; i < 4; i++) {
            // Explicit branch and vendor model bounds; no +/-4096 alternative.
            int rawLo = Math.max(envelopes[i][0], raw0[i] - 2047);
            int rawHi = Math.min(envelopes[i][1], raw0[i] + 2047);
            double a = q0[i] + signs[i] * (rawLo - raw0[i]) * COUNT_RAD;
            double b = q0[i] + signs[i] * (rawHi - raw0[i]) * COUNT_RAD;
            lo[i] = Math.max(Math.min(a, b), LIMITS[i][0]);
            hi[i] = Math.min(Math.max(a, b), LIMITS[i][1]);
            if (lo[i] > hi[i]) throw new IllegalArgumentException("Empty model/profile joint interval");
            initial[i] = clamp(seedQ[i], lo[i], hi[i]);
        }
        double[] best = null;
        double bestCost = Double.POSITIVE_INFINITY;
        // Deterministic bounded seeds help near elbow singularities. None changes
        // the measured wrist roll or enables an alternate encoder branch.
        for (int attempt = 0; attempt < 6; attempt++) {
            double[] guess = initial.clone();
            if (attempt == 1) for (int i = 0; i < 4; i++) guess[i] = (lo[i] + hi[i]) / 2;
            if (attempt >= 2) {
                guess[1] = clamp(initial[1] + ((attempt & 1) == 0 ? .6 : -.6), lo[1], hi[1]);
                guess[2] = clamp(initial[2] + (attempt < 4 ? .6 : -.6), lo[2], hi[2]);
            }
            double[] solution = solve(guess, seedQ[4], xyzMm, pitch, lo, hi);
            double cost = squared(residual(solution, seedQ[4], xyzMm, pitch));
            if (cost < bestCost) { best = solution; bestCost = cost; }
            if (bestCost < 1e-10) break;
        }
        int[] raw = seed.clone();
        for (int i = 0; i < 4; i++) {
            raw[i] = (int) Math.round(raw0[i] + signs[i] * (best[i] - q0[i]) / COUNT_RAD);
            // Quantization may cross a model edge; select an inward integer.
            double q = q0[i] + signs[i] * (raw[i] - raw0[i]) * COUNT_RAD;
            if (q < lo[i]) raw[i] += signs[i];
            if (q > hi[i]) raw[i] -= signs[i];
        }
        profile.validatePose(raw);
        double[] result = forward(raw);
        double error = Math.hypot(Math.hypot(result[0] - xyzMm[0], result[1] - xyzMm[1]),
                result[2] - xyzMm[2]);
        if (error > POSITION_TOLERANCE_MM || Math.abs(result[3] - pitch) > PITCH_TOLERANCE_RADIANS)
            throw new IllegalArgumentException("Target cannot be solved within position/pitch limits");
        return raw;
    }

    private double[] angles(int[] raw) {
        ArmProfile.requireRawPose(raw);
        double[] q = new double[5];
        for (int i = 0; i < 5; i++) {
            int delta = raw[i] - raw0[i];
            if (!(i == 4 && profile.passiveWristRoll()) && Math.abs(delta) >= 2048)
                throw new IllegalArgumentException("Ambiguous encoder branch; no automatic wrapping");
            q[i] = q0[i] + signs[i] * delta * COUNT_RAD;
        }
        return q;
    }

    private double[] pose(double[] q) {
        double[][] transform = identity();
        for (int i = 0; i < 5; i++) transform = multiply(multiply(transform, origins[i]), rotationZ(q[i]));
        transform = multiply(transform, tip);
        return new double[]{transform[0][3] * 1000, transform[1][3] * 1000, transform[2][3] * 1000,
                Math.atan2(transform[2][2], Math.hypot(transform[0][2], transform[1][2]))};
    }

    private double[] residual(double[] q4, double roll, double[] target, double pitch) {
        double[] p = pose(new double[]{q4[0], q4[1], q4[2], q4[3], roll});
        return new double[]{p[0] - target[0], p[1] - target[1], p[2] - target[2], 100 * (p[3] - pitch)};
    }

    private double[] solve(double[] q, double roll, double[] target, double pitch, double[] lo, double[] hi) {
        double lambda = .001;
        double[] r = residual(q, roll, target, pitch);
        for (int iteration = 0; iteration < 180; iteration++) {
            if (squared(r) < 1e-12) break;
            double[][] jacobian = new double[4][4];
            for (int col = 0; col < 4; col++) {
                double[] lower = q.clone(), upper = q.clone();
                lower[col] = Math.max(lo[col], q[col] - 1e-5);
                upper[col] = Math.min(hi[col], q[col] + 1e-5);
                double span = upper[col] - lower[col];
                if (span < 1e-12) continue;
                double[] a = residual(lower, roll, target, pitch), b = residual(upper, roll, target, pitch);
                for (int row = 0; row < 4; row++) jacobian[row][col] = (b[row] - a[row]) / span;
            }
            double[][] normal = new double[4][4];
            double[] rhs = new double[4];
            for (int i = 0; i < 4; i++) {
                for (int row = 0; row < 4; row++) rhs[i] -= jacobian[row][i] * r[row];
                for (int j = 0; j < 4; j++) for (int row = 0; row < 4; row++)
                    normal[i][j] += jacobian[row][i] * jacobian[row][j];
                normal[i][i] += lambda * Math.max(1., normal[i][i]);
            }
            double[] step = linearSolve(normal, rhs);
            if (step == null) { lambda *= 10; continue; }
            double maximum = 0;
            for (double v : step) maximum = Math.max(maximum, Math.abs(v));
            double[] next = q.clone();
            for (int i = 0; i < 4; i++) next[i] = clamp(q[i] + step[i] * Math.min(1, .25 / Math.max(maximum, 1e-12)), lo[i], hi[i]);
            double[] candidate = residual(next, roll, target, pitch);
            if (squared(candidate) < squared(r)) {
                q = next; r = candidate; lambda = Math.max(1e-9, lambda / 3);
            } else {
                lambda *= 10;
                if (lambda > 1e12) break;
            }
        }
        return q;
    }

    private static double[] linearSolve(double[][] matrix, double[] rhs) {
        double[][] a = new double[4][5];
        for (int i = 0; i < 4; i++) { System.arraycopy(matrix[i], 0, a[i], 0, 4); a[i][4] = rhs[i]; }
        for (int col = 0; col < 4; col++) {
            int pivot = col;
            for (int i = col + 1; i < 4; i++) if (Math.abs(a[i][col]) > Math.abs(a[pivot][col])) pivot = i;
            if (Math.abs(a[pivot][col]) < 1e-14) return null;
            double[] swap = a[col]; a[col] = a[pivot]; a[pivot] = swap;
            double divisor = a[col][col];
            for (int j = col; j < 5; j++) a[col][j] /= divisor;
            for (int i = 0; i < 4; i++) if (i != col) {
                double factor = a[i][col];
                for (int j = col; j < 5; j++) a[i][j] -= factor * a[col][j];
            }
        }
        return new double[]{a[0][4], a[1][4], a[2][4], a[3][4]};
    }

    private static double[][] identity() {
        double[][] a = new double[4][4];
        for (int i = 0; i < 4; i++) a[i][i] = 1;
        return a;
    }
    private static double[][] rotationZ(double angle) {
        double[][] a = identity(); double c = Math.cos(angle), s = Math.sin(angle);
        a[0][0] = c; a[0][1] = -s; a[1][0] = s; a[1][1] = c;
        return a;
    }
    private static double[][] origin(double[] p) {
        double r = p[3], pitch = p[4], y = p[5];
        double cr = Math.cos(r), sr = Math.sin(r), cp = Math.cos(pitch), sp = Math.sin(pitch), cy = Math.cos(y), sy = Math.sin(y);
        double[][] a = identity();
        a[0][0] = cy * cp; a[0][1] = cy * sp * sr - sy * cr; a[0][2] = cy * sp * cr + sy * sr;
        a[1][0] = sy * cp; a[1][1] = sy * sp * sr + cy * cr; a[1][2] = sy * sp * cr - cy * sr;
        a[2][0] = -sp; a[2][1] = cp * sr; a[2][2] = cp * cr;
        for (int i = 0; i < 3; i++) a[i][3] = p[i];
        return a;
    }
    private static double[][] multiply(double[][] a, double[][] b) {
        double[][] result = new double[4][4];
        for (int i = 0; i < 4; i++) for (int j = 0; j < 4; j++) for (int k = 0; k < 4; k++) result[i][j] += a[i][k] * b[k][j];
        return result;
    }
    private static double norm3(double[] values) { return Math.hypot(Math.hypot(values[0], values[1]), values[2]); }
    private static double squared(double[] values) { double sum = 0; for (double v : values) sum += v * v; return sum; }
    private static double clamp(double x, double lo, double hi) { return Math.max(lo, Math.min(hi, x)); }
}
