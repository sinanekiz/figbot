package com.figbot.scanner.vision;

/** Motor-thread gate: keeps the original world reference through brief tracking glitches.
 * WAIT never authorizes motion or samples. INVALID is latched until calibration
 * or an independent fresh stationary marker/encoder validation resets the gate.
 * Timing values are policy, not evidence of physical camera accuracy.
 */
public final class CameraReferenceGuard {
    private final java.util.function.LongSupplier clock;
    public CameraReferenceGuard(){this(System::nanoTime);}
    CameraReferenceGuard(java.util.function.LongSupplier clock){this.clock=java.util.Objects.requireNonNull(clock);}
    /** Sample evaluation time after the caller has captured the frame timestamp. */
    public State updateNow(long frameNs,boolean sameReference,boolean observationsFresh){
        return update(clock.getAsLong(),frameNs,sameReference,observationsFresh);
    }
    public enum State { READY, WAIT, INVALID }
    public static final long MAX_FRAME_AGE_NS = 250_000_000L;
    public static final long RECOVERY_NS = 250_000_000L;
    public static final long LOSS_LIMIT_NS = 1_500_000_000L;
    private State state = State.READY;
    private long suspectSince = -1, goodSince = -1, poseGoodSince = -1, acceptAfter;

    public void reset() {
        state = State.READY; suspectSince = goodSince = poseGoodSince = -1; acceptAfter = 0;
    }
    public long acceptAfterNs() { return acceptAfter; }

    public State update(long now, long frameNs, boolean sameReference, boolean observationsFresh) {
        if (state == State.INVALID) return state;
        boolean poseGood = sameReference && frameNs > 0 && now >= frameNs
                && now - frameNs <= MAX_FRAME_AGE_NS;
        // Recover the camera independently of object visibility. A missed fig must
        // not prolong a past camera glitch into a false calibration invalidation.
        if (poseGood) {
            if (poseGoodSince < 0) poseGoodSince = frameNs;
            if (frameNs - poseGoodSince >= RECOVERY_NS) suspectSince = -1;
        } else poseGoodSince = -1;
        if (!poseGood && suspectSince < 0) suspectSince = now;
        if (suspectSince >= 0 && now - suspectSince >= LOSS_LIMIT_NS) {
            state = State.INVALID; return state;
        }
        if (!poseGood || !observationsFresh) {
            state = State.WAIT; goodSince = -1;
            acceptAfter = now;
        } else if (state == State.WAIT) {
            if (goodSince < 0) goodSince = frameNs;
            // Progress must come from new camera frames, not repeated motor ticks.
            if (frameNs - goodSince >= RECOVERY_NS) {
                state = State.READY; suspectSince = -1;
            }
        }
        return state;
    }
}
