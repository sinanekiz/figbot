package com.figbot.scanner.so101;

/** Table height in the existing robot-base frame; does not move its origin. */
public record WorkSurface(double baseHeightMm) {
    public WorkSurface {
        if (!Double.isFinite(baseHeightMm) || baseHeightMm < 0 || baseHeightMm > 1000)
            throw new IllegalArgumentException("Taban yüksekliği 0–100 cm arasında olmalı.");
        if (baseHeightMm == 0) baseHeightMm = 0; // Normalize negative zero.
    }

    /** UI distance from the table up to the base bottom, using either decimal separator. */
    public static WorkSurface fromCentimeters(String text) {
        String value = text == null ? "" : text.trim();
        if (!value.matches("(?:[0-9]+(?:[.,][0-9]+)?|[.,][0-9]+)"))
            throw new IllegalArgumentException("Yüksekliği santimetre olarak gir; örneğin 6,5.");
        return new WorkSurface(Double.parseDouble(value.replace(',', '.')) * 10);
    }

    public double groundZMm() { return -baseHeightMm; }

    public double gripZMm(double clearanceMm) {
        if (!Double.isFinite(clearanceMm) || clearanceMm < 0)
            throw new IllegalArgumentException("Masa üzerindeki kavrama yüksekliği sonlu ve negatif olmayan bir değer olmalı.");
        return groundZMm() + clearanceMm;
    }
}
