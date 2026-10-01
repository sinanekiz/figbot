package com.figbot.scanner.so101;

import java.util.List;

/**
 * Adaptive fig-following brain. Pure decisions; the caller owns the bus.
 *
 * Camera MOVING (orange): the target keeps changing, so the arm re-aims at the
 * newest detection at most once per retarget interval (default 1 s).
 * Camera STABLE (green): the arm performs one smooth precise leg to the settled
 * position and holds it; it re-aims only if the target genuinely moves again.
 *
 * The caller supplies the current gripper position (robot frame, mm) measured
 * by the same kinematic model, so arrival is decided from feedback, not intent.
 */
public final class FollowBrain {

    /** Robot-frame detection fed by the camera pipeline. */
    public record Detection(double[] robotMm, double confidence, long capturedNs) {}

    public enum CameraState { MOVING, STABLE }

    public enum DecisionType {
        NONE,           // nothing to do this tick
        RETARGET,       // orange: re-aim at the moving target (stop current leg, plan a new one)
        PRECISE_MOVE,   // green/stable: single smooth leg to the settled target
        ARRIVED,        // holding within the arrival radius of the target
        LOST_TARGET     // following is armed but no fresh detection exists
    }

    public record Decision(DecisionType type, double[] targetMm, String reason) {
        public static Decision none() { return new Decision(DecisionType.NONE, null, ""); }
        static Decision of(DecisionType type, double[] target, String reason) {
            return new Decision(type, target, reason);
        }
    }

    private final long retargetIntervalNs;
    private final double associationMm;   // XY distance treated as the same physical fig
    private final double retargetShiftMm; // only re-aim when the target moved this much
    private final double arrivalMm;        // feedback-based success radius

    private double[] followTarget;      // newest accepted target, robot frame mm
    private double[] plannedTarget;     // target of the trajectory currently in flight
    private long lastPlanNs;
    private boolean following;          // armed by the user's "follow" button
    private boolean arrivedAnnounced;  // suppress repeated ARRIVED spam while holding

    public FollowBrain(long retargetIntervalNs, double associationMm,
                       double retargetShiftMm, double arrivalMm) {
        if (retargetIntervalNs <= 0 || associationMm <= 0 || retargetShiftMm <= 0 || arrivalMm <= 0)
            throw new IllegalArgumentException("Positive follow parameters required");
        this.retargetIntervalNs = retargetIntervalNs;
        this.associationMm = associationMm;
        this.retargetShiftMm = retargetShiftMm;
        this.arrivalMm = arrivalMm;
    }

    public static FollowBrain standard() {
        return new FollowBrain(1_000_000_000L, 60, 8, 15);
    }

    /** User pressed follow / Hedefe Git. */
    public void arm(long nowNs) { following = true; arrivedAnnounced = false; lastPlanNs = 0; followTarget=null; plannedTarget=null; }
    /** User pressed stop / DUR. */
    public void disarm() { following = false; followTarget = null; plannedTarget = null; }
    public boolean isFollowing() { return following; }
    /** Target the caller should treat as "in flight" once it starts a leg. */
    public void confirmPlanned(double[] targetMm, long nowNs) { plannedTarget = targetMm; lastPlanNs = nowNs; }
    public double[] followTarget() { return followTarget; }

    public Decision tick(long nowNs, CameraState camera, List<Detection> detections,
                        boolean armHolding, boolean armMoving, double[] gripperMm) {
        if (!following) return Decision.none();
        // Lock identity for this pickup. Occlusion must never select another fig.
        Detection best = null;
        for (Detection d : detections) {
            if (d == null || d.robotMm() == null || !Double.isFinite(d.confidence())) continue;
            if (best == null || d.confidence() > best.confidence()) best = d;
        }
        if (followTarget != null) {
            Detection same = null;
            for (Detection d : detections) {
                if (d == null || d.robotMm() == null) continue;
                if (xyDistance(d.robotMm(), followTarget) <= associationMm
                        && (same == null || xyDistance(d.robotMm(), followTarget) < xyDistance(same.robotMm(), followTarget))) same = d;
            }
            best = same;
        }
        if (best == null) {
            return Decision.of(DecisionType.LOST_TARGET, null, "Taze incir görüntüsü yok");
        }
        followTarget = best.robotMm().clone();
        double[] target = followTarget;
        double reached = gripperMm == null ? Double.MAX_VALUE : distance(gripperMm, target);
        if (armHolding && reached <= arrivalMm) {
            if (!arrivedAnnounced) {
                arrivedAnnounced = true;
                return Decision.of(DecisionType.ARRIVED, target,
                        String.format(java.util.Locale.US, "%.0f mm", reached));
            }
            return Decision.none();
        }
        arrivedAnnounced = false;
        if (camera == CameraState.MOVING) {
            if (armMoving) {
                // Already heading somewhere: re-aim at most once per interval and only
                // when the target drifted far enough to be worth another leg.
                if (nowNs - lastPlanNs < retargetIntervalNs) return Decision.none();
                if (plannedTarget != null && distance(target, plannedTarget) <= retargetShiftMm)
                    return Decision.none();
                return Decision.of(DecisionType.RETARGET, target, "Kamera hareketli · uyum");
            }
            if (nowNs - lastPlanNs < retargetIntervalNs && plannedTarget != null) return Decision.none();
            if (plannedTarget != null && distance(target, plannedTarget) <= retargetShiftMm)
                return Decision.none();
            return Decision.of(DecisionType.RETARGET, target, "Kamera hareketli · uyum");
        }
        // Camera STABLE: one clean leg to the settled position.
        if (armMoving) {
            if (plannedTarget != null && distance(target, plannedTarget) <= retargetShiftMm)
                return Decision.none();          // current leg already aims at the settled target
            return Decision.of(DecisionType.RETARGET, target, "Hedef yeşile dönerken düzeltme");
        }
        if (reached > arrivalMm)
            return Decision.of(DecisionType.PRECISE_MOVE, target, "Kamera stabil · düzgün yaklaşma");
        return Decision.none();
    }

    static double distance(double[] a, double[] b) {
        double dx = a[0]-b[0], dy = a[1]-b[1], dz = a[2]-b[2];
        return Math.sqrt(dx*dx + dy*dy + dz*dz);
    }
    private static double xyDistance(double[] a, double[] b) {
        double dx = a[0]-b[0], dy = a[1]-b[1];
        return Math.sqrt(dx*dx + dy*dy);
    }
}
