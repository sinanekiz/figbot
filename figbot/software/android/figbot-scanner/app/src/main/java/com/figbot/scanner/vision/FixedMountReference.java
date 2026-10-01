package com.figbot.scanner.vision;

/** Fixed physical mount contract; IMU is a disturbance detector, not a translation tracker.
 * A slow translation can evade it: marker/encoder validation is also required.
 * Does not consume AR world coordinates, which can change while a camera is stationary.
 */
public final class FixedMountReference {
    private final java.util.function.LongSupplier clock;
    public FixedMountReference(){this(System::nanoTime);}
    FixedMountReference(java.util.function.LongSupplier clock){this.clock=java.util.Objects.requireNonNull(clock);}
    // Read the clock under the same lock as callbacks: a motor-loop timestamp
    // taken before a new sensor callback must not make that sample look future-dated.
    public synchronized boolean readyNow(){return ready(clock.getAsLong());}
    public synchronized boolean validNow(){return valid(clock.getAsLong());}
    public synchronized boolean settledNow(){return settled(clock.getAsLong());}
    public synchronized void armNow(){arm(clock.getAsLong());}
    private float[] rotation, anchor;
    private long rotationNs, accelerationNs, accelerationSince;
    private double acceleration;
    private boolean disturbed;
    private float[] quietRotation;
    private long quietSince;
    public synchronized void rotation(float[] q,long now) {
        if(quietRotation==null||now-rotationNs>=500_000_000L||!sameRotation(quietRotation,q,.3)){
            quietRotation=q.clone();quietSince=now;
        }
        rotation=q.clone();rotationNs=now;
        if(anchor!=null&&!sameRotation(anchor,q))disturbed=true;
    }
    public synchronized void acceleration(float x,float y,float z,long now) {
        acceleration=Math.sqrt(x*x+y*y+z*z);accelerationNs=now;
        if(!Double.isFinite(acceleration)||acceleration>.8){
            quietSince=now;
            if(accelerationSince==0)accelerationSince=now;
            if(anchor!=null&&now-accelerationSince>=200_000_000L)disturbed=true;
        }else accelerationSince=0;
    }
    public synchronized boolean ready(long now) {
        return rotation!=null&&now>=rotationNs&&now-rotationNs<500_000_000L
                &&accelerationNs>0&&now>=accelerationNs&&now-accelerationNs<500_000_000L
                &&Double.isFinite(acceleration)&&acceleration<=.8;
    }
    public synchronized void arm(long now) {
        if(!ready(now))throw new IllegalStateException("Telefon hareket sensörleri hazır değil; sabit tut.");
        anchor=rotation.clone();disturbed=false;accelerationSince=0;
    }
    public synchronized boolean valid(long now) {return anchor!=null&&!disturbed&&ready(now);}
    /** Only used to revalidate a moved rig after it has stopped, never mid-flight. */
    public synchronized boolean settled(long now){return ready(now)&&quietSince>0&&now-quietSince>=600_000_000L;}
    public synchronized void clear() {anchor=null;rotation=null;quietRotation=null;quietSince=0;rotationNs=accelerationNs=0;disturbed=false;}
    private static boolean sameRotation(float[] a,float[] b) {
        return sameRotation(a,b,1);
    }
    private static boolean sameRotation(float[] a,float[] b,double degrees) {
        if(a.length!=4||b.length!=4)return false;
        double dot=0,aa=0,bb=0;
        for(int i=0;i<4;i++){dot+=a[i]*b[i];aa+=a[i]*a[i];bb+=b[i]*b[i];}
        return aa>0&&bb>0&&Double.isFinite(dot)&&2*Math.acos(Math.min(1,Math.abs(dot)/Math.sqrt(aa*bb)))<=Math.toRadians(degrees);
    }
}
