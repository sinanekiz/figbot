package com.figbot.scanner;

import java.util.Locale;

/** Small dependency-free vector used by calibration and tests. Units are metres. */
public record Vec3(double x, double y, double z) {
    public Vec3 {
        if (!Double.isFinite(x) || !Double.isFinite(y) || !Double.isFinite(z)) {
            throw new IllegalArgumentException("Vector values must be finite");
        }
    }

    public Vec3 subtract(Vec3 other) {
        return new Vec3(x - other.x, y - other.y, z - other.z);
    }

    public Vec3 scale(double value) {
        return new Vec3(x * value, y * value, z * value);
    }

    public double dot(Vec3 other) {
        return x * other.x + y * other.y + z * other.z;
    }

    public Vec3 cross(Vec3 other) {
        return new Vec3(
                y * other.z - z * other.y,
                z * other.x - x * other.z,
                x * other.y - y * other.x);
    }

    public double norm() {
        return Math.sqrt(dot(this));
    }

    public Vec3 normalized() {
        double length = norm();
        if (length < 1.0e-9) {
            throw new IllegalArgumentException("Zero-length vector cannot be normalized");
        }
        return scale(1.0 / length);
    }

    public String millimetreText() {
        return String.format(Locale.US, "X %.0f  Y %.0f  Z %.0f mm", x * 1000, y * 1000, z * 1000);
    }
}
