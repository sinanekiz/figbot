package com.figbot.scanner.so101;

/** Model-space arrival checks immediately before closing the fingers.
 * Encoder/FK agreement is not proof of real jaw alignment or calibrated TCP.
 * The caller must use fresh, settled feedback and permit at most one correction
 * for the committed target, then evaluate again against the ORIGINAL desired pose.
 */
public final class GraspAlignment {
    public static final double POSITION_MM = 4.0;
    public static final double PITCH_RADIANS = Math.toRadians(2);
    public static final double MAX_CORRECTION_MM = 8.0;
    public static final double MAX_CORRECTION_PITCH_RADIANS = Math.toRadians(5);
    public static final int MAX_CORRECTION_COUNTS = 20;
    public static final int ROLL_TOLERANCE_COUNTS = 3;

    private GraspAlignment() {}

    public record Residual(double positionMm, double pitchRadians, boolean aligned) {}

    /** Jaw opening is deliberately excluded; this measures the arm's tool pose. */
    public static Residual evaluate(ArmProfile profile, int[] measured, int[] desired) {
        if (profile == null) throw new IllegalArgumentException("Kol profili gerekli.");
        profile.validatePose(measured);
        profile.validatePose(desired);
        So101Kinematics kin = new So101Kinematics(profile);
        double[] actual = finitePose(kin.forward(measured));
        double[] target = finitePose(kin.forward(desired));
        double distance = positionDistance(actual, target);
        double pitch = Math.abs(actual[3] - target[3]);
        return new Residual(distance, pitch, distance <= POSITION_MM
                && pitch <= PITCH_RADIANS
                && rollDifference(profile, measured, desired) <= ROLL_TOLERANCE_COUNTS);
    }

    /** A single bounded feed-forward compensation for a small measured joint lag.
     * Nothing is clipped at travel limits. Passive roll and jaw remain measured.
     * This command is not a new target: convergence is checked against desired,
     * not against the deliberately offset command, and must never be iterated.
     */
    public static GoalTrajectory correction(ArmProfile profile, int[] measured,
                                            int[] desired, int speed) {
        Residual residual = evaluate(profile, measured, desired);
        if (rollDifference(profile, measured, desired) > ROLL_TOLERANCE_COUNTS)
            throw new IllegalArgumentException("Pasif bilek dönmüş; kavrama düzeltmesi uygulanmadı.");
        if (residual.aligned())
            throw new IllegalArgumentException("Kavrama konumu zaten tolerans içinde; ek düzeltme gerekmiyor.");
        if (residual.positionMm() <= POSITION_MM
                || residual.positionMm() > MAX_CORRECTION_MM
                || residual.pitchRadians() > MAX_CORRECTION_PITCH_RADIANS)
            throw new IllegalArgumentException("Kavrama konum farkı tek düzeltmenin 4–8 mm / 5° aralığı dışında.");

        int[] command = measured.clone();
        for (int axis = 0; axis < 4; axis++) {
            int lag = desired[axis] - measured[axis];
            if (Math.abs(lag) > MAX_CORRECTION_COUNTS)
                throw new IllegalArgumentException("Kavrama düzeltmesi eklem başına 20 sayımı aşıyor.");
            command[axis] = desired[axis] + lag;
        }
        profile.validatePose(command);
        So101Kinematics kin = new So101Kinematics(profile);
        double[] target = finitePose(kin.forward(desired));
        double[] compensated = finitePose(kin.forward(command));
        if (positionDistance(target, compensated) > MAX_CORRECTION_MM
                || Math.abs(target[3] - compensated[3]) > MAX_CORRECTION_PITCH_RADIANS)
            throw new IllegalArgumentException("Kavrama telafisi modelde 8 mm / 5° sınırını aşıyor.");
        return PickupPlan.checked(profile, measured, command, speed);
    }

    private static int rollDifference(ArmProfile profile, int[] measured, int[] desired) {
        int delta = Math.abs(measured[4] - desired[4]);
        return profile.passiveWristRoll() ? Math.min(delta, 4096 - delta) : delta;
    }

    private static double[] finitePose(double[] pose) {
        for (double value : pose) if (!Double.isFinite(value))
            throw new IllegalArgumentException("Kavrama konum hesabı geçerli bir sayı üretmedi.");
        return pose;
    }

    private static double positionDistance(double[] a, double[] b) {
        return Math.hypot(Math.hypot(a[0] - b[0], a[1] - b[1]), a[2] - b[2]);
    }
}
