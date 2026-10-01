package com.figbot.scanner.so101;

/** Immutable encoder map and measured task poses. No hardware or Android access.
 * The bundled map is a geometric estimate, not autonomous-motion calibration.
 */
public final class ArmProfile {
    public static final String VENDOR_URDF_SHA256 =
            "3a65d2d35e68a8d2f0c2cc176d19b884506543c93ba72980145b80abe276022c";
    public static final String FRAME = "vendor_base_link";
    private final int[] offsets, referenceRaw, signs, home, basket;
    private final double[] referenceRadians;
    private final int[][] envelopes;
    private final int closed, open;
    private final double groundZMm;
    private final boolean physicalCalibrationVerified, passiveWristRoll;
    private final String calibrationStatus;

    public ArmProfile(int[] offsets, int[] referenceRaw, double[] referenceRadians,
                      int[] directionSigns, int[][] envelopes, int[] home, int[] basket,
                      int gripperClosed, int gripperOpen, boolean physicalCalibrationVerified,
                      String calibrationStatus) {
        this(offsets, referenceRaw, referenceRadians, directionSigns, envelopes, home, basket,
                gripperClosed, gripperOpen, physicalCalibrationVerified, calibrationStatus, false, 0);
    }
    private ArmProfile(int[] offsets, int[] referenceRaw, double[] referenceRadians,
                       int[] directionSigns, int[][] envelopes, int[] home, int[] basket,
                       int gripperClosed, int gripperOpen, boolean physicalCalibrationVerified,
                       String calibrationStatus, boolean passiveWristRoll, double groundZMm) {
        this.passiveWristRoll = passiveWristRoll;
        if (!Double.isFinite(groundZMm) || Math.abs(groundZMm) > 1500)
            throw new IllegalArgumentException("Çalışma düzlemi yüksekliği sonlu ve -1500–1500 mm arasında olmalı.");
        this.groundZMm = groundZMm;
        requireRawPose(offsets);
        requireRawPose(home);
        requireRawPose(basket);
        if (referenceRaw == null || referenceRaw.length != 5 || referenceRadians == null
                || referenceRadians.length != 5 || directionSigns == null || directionSigns.length != 5)
            throw new IllegalArgumentException("Five explicit reference entries are required");
        for (int i = 0; i < 5; i++) {
            if (referenceRaw[i] < -4096 || referenceRaw[i] > 8191
                    || !Double.isFinite(referenceRadians[i])
                    || (directionSigns[i] != -1 && directionSigns[i] != 1))
                throw new IllegalArgumentException("Invalid explicit encoder reference");
        }
        if (envelopes == null || envelopes.length != 6)
            throw new IllegalArgumentException("Six encoder envelopes are required");
        this.envelopes = new int[6][2];
        for (int i = 0; i < 6; i++) {
            if (envelopes[i] == null || envelopes[i].length != 2 || envelopes[i][0] < 0
                    || envelopes[i][1] > 4095 || envelopes[i][0] > envelopes[i][1])
                throw new IllegalArgumentException("Invalid encoder envelope");
            this.envelopes[i] = envelopes[i].clone();
        }
        if (gripperClosed < this.envelopes[5][0] || gripperOpen > this.envelopes[5][1]
                || gripperOpen <= gripperClosed)
            throw new IllegalArgumentException("Gripper must open toward increasing encoder values");
        if (calibrationStatus == null || calibrationStatus.trim().isEmpty())
            throw new IllegalArgumentException("Calibration provenance is required");
        this.offsets = offsets.clone();
        this.referenceRaw = referenceRaw.clone();
        this.referenceRadians = referenceRadians.clone();
        this.signs = directionSigns.clone();
        this.home = home.clone();
        this.basket = basket.clone();
        this.closed = gripperClosed;
        this.open = gripperOpen;
        this.physicalCalibrationVerified = physicalCalibrationVerified;
        this.calibrationStatus = calibrationStatus;
        validatePose(this.home);
        validatePose(this.basket);
    }

    /** Session examples from the measured desktop route; verification remains false. */
    public static ArmProfile unverifiedDefaults() {
        return new ArmProfile(new int[]{4080, 2861, 85, 85, 85, 85},
                new int[]{1996, 1824, 3107, 1878, 4208},
                new double[]{0, Math.toRadians(-13.967960079826165),
                        Math.toRadians(16.17545169197406), Math.toRadians(-2.207491612147896), 0},
                new int[]{1, 1, 1, 1, 1},
                new int[][]{{1905, 3385}, {751, 2891}, {2315, 3974},
                        {1789, 2732}, {3104, 3150}, {769, 1201}},
                new int[]{1971, 921, 3946, 2681, 3129, 791},
                new int[]{3363, 2177, 2602, 2593, 3125, 1153}, 894, 1153,
                false, "LOCAL_GEOMETRIC_ESTIMATE; PHYSICAL_ACCURACY_AND_CAMERA_TRANSFORM_UNVERIFIED");
    }

    /** Saving task poses does not grant physical calibration or autonomous permission. */
    public ArmProfile withSavedPoses(int[] home, int[] basket, int closed, int open) {
        return new ArmProfile(offsets, referenceRaw, referenceRadians, signs, envelopes,
                home, basket, closed, open, physicalCalibrationVerified, calibrationStatus, passiveWristRoll, groundZMm);
    }

    /** Caller must provide its independently measured calibration evidence. */
    public ArmProfile withPhysicalCalibrationVerified(boolean verified) {
        return new ArmProfile(offsets, referenceRaw, referenceRadians, signs, envelopes,
                home, basket, closed, open, verified, calibrationStatus, passiveWristRoll, groundZMm);
    }

    /** Supervised test moves only: the encoder map is the one physically exercised in the
     * recorded 2026-09-20/21 sessions (user-confirmed IK pick), not freshly tip-measured. */
    public ArmProfile withRecordedSessionValidation(String status) {
        if (status == null || status.trim().isEmpty())
            throw new IllegalArgumentException("Recorded-session provenance is required");
        return new ArmProfile(offsets, referenceRaw, referenceRadians, signs, envelopes,
                home, basket, closed, open, true, status, passiveWristRoll, groundZMm);
    }

    /** The follow app never commands the passive wrist roll (ID5), so its recorded
     * 46-count window must not veto trajectories that merely start elsewhere in the
     * same encoder branch. Bounds stay inside the reference's unambiguous branch. */
    public ArmProfile withWristRollEnvelope(int low, int high) {
        if (low < 0 || high > 4095 || low > high)
            throw new IllegalArgumentException("Invalid wrist roll envelope");
        int reference = referenceRaw[4];
        low = Math.max(low, reference - 2047);
        high = Math.min(high, Math.min(4095, reference + 2047));
        int[][] relaxed = envelopes.clone();
        for (int i = 0; i < 6; i++) relaxed[i] = relaxed[i].clone();
        relaxed[4] = new int[]{low, high};
        return new ArmProfile(offsets, referenceRaw, referenceRadians, signs, relaxed,
                home, basket, closed, open, physicalCalibrationVerified, calibrationStatus, passiveWristRoll, groundZMm);
    }

    /** Measured roll is periodic in FK; the controller still never commands ID5. */
    public ArmProfile withPassiveWristRoll() {
        int[][] bounds = envelopes(); bounds[4] = new int[]{0, 4095};
        return new ArmProfile(offsets, referenceRaw, referenceRadians, signs, bounds,
                home, basket, closed, open, physicalCalibrationVerified, calibrationStatus, true, groundZMm);
    }
    public boolean passiveWristRoll() { return passiveWristRoll; }

    /** Local calibration ingress only, at most 8 counts beyond the recorded travel sample.
     * The planner must move inward and keep every subsequent target inside the original bounds. */
    public ArmProfile calibrationIngress(int[] start) {
        requireRawPose(start);
        int[][] bounds = envelopes();
        for (int i=0;i<4;i++) {
            if (start[i] < bounds[i][0]-8 || start[i] > bounds[i][1]+8) {
                validatePose(start); // Detailed joint/value error; never clamp a distant start.
            }
            bounds[i][0] = Math.min(bounds[i][0], start[i]);
            bounds[i][1] = Math.max(bounds[i][1], start[i]);
        }
        ArmProfile local = new ArmProfile(offsets, referenceRaw, referenceRadians, signs, bounds,
                home, basket, closed, open, physicalCalibrationVerified, calibrationStatus, passiveWristRoll, groundZMm);
        local.validatePose(start);
        return local;
    }

    /** Explicitly measured workplane Z in the unchanged vendor base frame.
     * A table 65 mm below the base reference is -65 mm. This changes neither
     * the robot geometry nor encoder calibration and does not verify either.
     * The finite +/-1500 mm bound catches invalid input; it is not reachability.
     */
    public ArmProfile withGroundZMm(double measuredGroundZMm) {
        return new ArmProfile(offsets, referenceRaw, referenceRadians, signs, envelopes,
                home, basket, closed, open, physicalCalibrationVerified, calibrationStatus,
                passiveWristRoll, measuredGroundZMm);
    }
    public double groundZMm() { return groundZMm; }

    public int[] offsets() { return offsets.clone(); }
    public int[] referenceRaw() { return referenceRaw.clone(); }
    public double[] referenceRadians() { return referenceRadians.clone(); }
    public int[] directionSigns() { return signs.clone(); }
    public int[] home() { return home.clone(); }
    public int[] basket() { return basket.clone(); }
    public int gripperClosed() { return closed; }
    public int gripperOpen() { return open; }
    public boolean physicalCalibrationVerified() { return physicalCalibrationVerified; }
    public String calibrationStatus() { return calibrationStatus; }
    public int speedLimit() { return 1200; }
    public int homeJointSpeedLimit() { return 1000; }
    public int accelerationLimit() { return 50; }
    public int[][] envelopes() {
        int[][] copy = new int[6][];
        for (int i = 0; i < 6; i++) copy[i] = envelopes[i].clone();
        return copy;
    }

    public static void requireRawPose(int[] raw) {
        if (raw == null || raw.length != 6)
            throw new IllegalArgumentException("Six raw encoder positions are required");
        for (int p : raw) if (p < 0 || p > 4095)
            throw new IllegalArgumentException("Encoder position is outside 0..4095");
    }

    public void validatePose(int[] raw) {
        requireRawPose(raw);
        for (int i = 0; i < 6; i++) if (raw[i] < envelopes[i][0] || raw[i] > envelopes[i][1])
            throw new IllegalArgumentException(jointName(i) + " (ID" + (i + 1) + ") konumu " + raw[i]
                    + "; kayıtlı hareket aralığı " + envelopes[i][0] + "–" + envelopes[i][1]
                    + ". Otomatik hareket başlamadı. Kolu destekle → Kolu bırak → elle uygun duruşa getir veya Elle ölçüm seç.");
        for (int i = 0; i < 5; i++) if (!(i == 4 && passiveWristRoll) && Math.abs(raw[i] - referenceRaw[i]) >= 2048)
            throw new IllegalArgumentException("Ambiguous encoder branch; automatic wrapping is disabled");
    }

    private static String jointName(int index) {
        return new String[]{"Taban", "Omuz", "Dirsek", "Bilek eğimi", "Bilek dönüşü", "Kıskaç"}[index];
    }
}
