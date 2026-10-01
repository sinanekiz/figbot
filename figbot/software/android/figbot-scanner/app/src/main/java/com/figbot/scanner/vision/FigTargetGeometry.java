package com.figbot.scanner.vision;

/** Metric contact from a validated camera/plane reference, never from AR hit tests.
 * No AR world-tracking or camera-motion prerequisite. This is model geometry,
 * not independent proof of physical accuracy or a successful grasp.
 */
public final class FigTargetGeometry {
    private FigTargetGeometry() {}
    public record Measurement(double xMm, double yMm, double surfaceZMm,
                              double gripZMm, double cameraRangeMm) {}

    public static Measurement resolve(boolean referenceReady, RigidPose baseCamera,
                                      double u, double v, double fx, double fy,
                                      double cx, double cy, double surfaceZMm,
                                      double clearanceMm) {
        if (!referenceReady || baseCamera == null || !Double.isFinite(clearanceMm)
                || clearanceMm < 0) return null;
        try {
            double[] contact = GroundProjection.contact(baseCamera, u, v, fx, fy, cx, cy, surfaceZMm);
            double[] origin = baseCamera.translation();
            double range = Math.sqrt(Math.pow(contact[0] - origin[0], 2)
                    + Math.pow(contact[1] - origin[1], 2) + Math.pow(contact[2] - origin[2], 2));
            return new Measurement(contact[0], contact[1], surfaceZMm, surfaceZMm + clearanceMm, range);
        } catch (IllegalArgumentException invalid) {
            return null;
        }
    }
}
