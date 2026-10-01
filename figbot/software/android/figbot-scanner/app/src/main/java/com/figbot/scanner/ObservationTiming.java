package com.figbot.scanner;

/** Provisional stationary-scene gate, not a metric accuracy guarantee. */
public final class ObservationTiming {
    public static final long MAX_AGE_NS = 750_000_000L;
    /** ARCore's frame time base is unspecified; Xiaomi CPU images can lead it by
     * one frame. Permit bounded skew of either sign, age conservatively, and
     * never stamp a repeated image or a future host observation as fresh. */
    public static long cpuCapture(long frame,long image,long previous,long hostBeforeAcquire){
        if(frame<=0||image<=0||image<=previous)return 0;
        long skew=frame-image;
        if(skew < -100_000_000L || skew > 100_000_000L)return 0;
        return Math.max(0,hostBeforeAcquire-Math.abs(skew));
    }
    public static boolean fresh(long captured, long now) {
        return captured > 0 && now >= captured && now - captured <= MAX_AGE_NS;
    }
    public static boolean stationary(float[] a, float[] b, float[] qa, float[] qb) {
        double distance2 = 0;
        for (int i=0; i<3; i++) distance2 += (a[i]-b[i])*(a[i]-b[i]);
        double dot=0, na=0, nb=0;
        for (int i=0; i<4; i++) { dot+=qa[i]*qb[i]; na+=qa[i]*qa[i]; nb+=qb[i]*qb[i]; }
        if (na == 0 || nb == 0 || !Double.isFinite(distance2)) return false;
        double angle = 2*Math.acos(Math.min(1, Math.abs(dot)/Math.sqrt(na*nb)));
        return distance2 <= 0.003*0.003 && angle <= Math.toRadians(0.5);
    }
    private ObservationTiming() {}
}
