package com.figbot.scanner;

/**
 * Converts ARCore world coordinates to the FIGBOT base frame.
 *
 * <p>ARCore world +Y is gravity-up. The user measures the base origin and one point on the
 * robot's positive X axis. Base Z is gravity-up and base Y is derived to keep a right-handed
 * coordinate system. This field calibration remains UNVERIFIED until checked against measured
 * control points.</p>
 */
public final class BaseFrameCalibration {
    static final double MIN_AXIS_LENGTH_METRES = 0.05;
    private static final Vec3 WORLD_UP = new Vec3(0, 1, 0);

    private Vec3 origin;
    private Vec3 positiveXPoint;
    private Vec3 xAxis;
    private Vec3 yAxis;

    public synchronized void setOrigin(Vec3 value) {
        origin = value;
        positiveXPoint = null;
        xAxis = null;
        yAxis = null;
    }

    public synchronized void setPositiveXPoint(Vec3 value) {
        if (origin == null) {
            throw new IllegalStateException("Set the origin before the +X point");
        }
        Vec3 delta = value.subtract(origin);
        Vec3 horizontal = new Vec3(delta.x(), 0, delta.z());
        if (horizontal.norm() < MIN_AXIS_LENGTH_METRES) {
            throw new IllegalArgumentException("+X point must be at least 50 mm from the origin");
        }
        positiveXPoint = value;
        xAxis = horizontal.normalized();
        yAxis = WORLD_UP.cross(xAxis).normalized();
    }

    public synchronized boolean hasOrigin() {
        return origin != null;
    }

    public synchronized boolean isReady() {
        return origin != null && xAxis != null && yAxis != null;
    }

    public synchronized Vec3 getOrigin() {
        return origin;
    }

    public synchronized Vec3 getPositiveXPoint() {
        return positiveXPoint;
    }

    public synchronized Vec3 toBase(Vec3 worldPoint) {
        if (!isReady()) {
            throw new IllegalStateException("Base-frame calibration is incomplete");
        }
        Vec3 delta = worldPoint.subtract(origin);
        return new Vec3(delta.dot(xAxis), delta.dot(yAxis), delta.dot(WORLD_UP));
    }

    public synchronized void clear() {
        origin = null;
        positiveXPoint = null;
        xAxis = null;
        yAxis = null;
    }
}
