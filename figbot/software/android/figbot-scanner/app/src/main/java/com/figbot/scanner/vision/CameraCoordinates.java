package com.figbot.scanner.vision;

/** Camera-relative OpenCV convention, mm. The world pose and point must share one frame. */
public final class CameraCoordinates {
    public static double[] fromWorld(RigidPose worldCamera,double[] worldPointMm) {
        double[] ar=worldCamera.inverse().map(worldPointMm);
        return new double[]{ar[0],-ar[1],-ar[2]};
    }
    private CameraCoordinates() {}
}
