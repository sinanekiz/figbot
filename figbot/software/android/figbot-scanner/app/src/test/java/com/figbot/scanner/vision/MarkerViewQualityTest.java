package com.figbot.scanner.vision;

import org.junit.Test;
import static org.junit.Assert.*;

public class MarkerViewQualityTest {
    static RigidPose pose(double degrees,double x,double z) {
        double a=Math.toRadians(degrees),c=Math.cos(a),s=Math.sin(a);
        return new RigidPose(new double[][]{{c,0,-s},{0,-1,0},{-s,0,-c}},new double[]{x,0,z});
    }
    static float[] pixels(RigidPose pose,double focal) {
        float[] pixels=new float[8];int i=0;
        for(double[] corner:new double[][]{{-18,18,0},{18,18,0},{18,-18,0},{-18,-18,0}}){
            double[] p=pose.map(corner);pixels[i++]=(float)(focal*p[0]/p[2]+320);pixels[i++]=(float)(focal*p[1]/p[2]+240);
        }
        return pixels;
    }
    @Test public void preciseObliqueViewsAreUsableWithoutAngleCorrectionToCoordinates(){
        for(double tilt:new double[]{20,40,60,70}){
            RigidPose p=pose(tilt,0,300);double[] before=p.translation();
            MarkerViewQuality q=MarkerViewQuality.evaluate(p,pixels(p,900),900,900,.1);
            assertEquals(tilt,q.incidenceDegrees(),1e-8);assertTrue(q.toString(),q.usable());
            assertArrayEquals(before,p.translation(),0);
        }
    }
    @Test public void uncertaintyIncreasesAtDistanceEvenWithZeroReprojectionError(){
        RigidPose near=pose(45,0,300),far=pose(45,0,1500);
        var a=MarkerViewQuality.evaluate(near,pixels(near,600),600,600,0);
        var b=MarkerViewQuality.evaluate(far,pixels(far,600),600,600,0);
        assertTrue(a.usable());assertFalse(b.usable());assertTrue(b.positionSensitivityMm()>a.positionSensitivityMm()*10);
    }
    @Test public void viewingAngleUsesMarkerRayRatherThanOpticalAxis(){
        RigidPose p=pose(0,300,300);
        assertEquals(45,MarkerViewQuality.incidence(p),1e-8);
    }
    @Test public void thinDiamondCannotPassJustBecauseAllEdgesAreLong(){
        float[] p={0,0,80,80,84,76,4,-4};
        for(int i=0;i<4;i++){int j=(i+1)%4;assertTrue(Math.hypot(p[2*i]-p[2*j],p[2*i+1]-p[2*j+1])>5);}
        assertTrue(MarkerViewQuality.thickness(p)<6);
        assertFalse(MarkerViewQuality.evaluate(pose(45,0,300),p,900,900,0).usable());
        // All four edges > 28, but nearly edge-on rhombus only 7 px thick.
        assertTrue(MarkerViewQuality.thickness(new float[]{0,0,70,0,140,7,70,7})<8);
    }
    @Test public void grazingBackfacesAndInvalidInputsFailClosed(){
        for(double tilt:new double[]{82,100,180}){
            RigidPose p=pose(tilt,0,300);assertFalse(MarkerViewQuality.evaluate(p,pixels(p,2000),2000,2000,0).usable());
        }
        assertFalse(MarkerViewQuality.evaluate(pose(30,0,300),new float[8],600,600,0).usable());
        assertFalse(MarkerViewQuality.evaluate(pose(30,0,300),pixels(pose(30,0,300),600),Double.NaN,600,0).usable());
    }
    @Test public void predictedScanQualityRejectsVisibleButImprecisePose(){
        MarkerVisibility v=new MarkerVisibility(600,600,320,240,640,480);
        assertTrue(v.contains(pose(0,0,650),28));
        assertFalse(v.measurable(pose(0,0,650),28));
        assertTrue(v.measurable(pose(45,0,300),28));
    }
    @Test public void uncertainObservationCannotAuthorizeMeasurement(){
        RigidPose p=pose(45,0,300);float[] corners=pixels(p,600);
        var q=MarkerViewQuality.evaluate(p,corners,600,600,0);
        assertTrue(new ArucoTracker.Observation(1,1,p,p,corners,0,true,q).usable());
        assertFalse(new ArucoTracker.Observation(1,1,p,p,corners,0,false,q).usable());
        assertFalse(new ArucoTracker.Observation(1,1,p,p,corners,0,true,null).usable());
    }
}
