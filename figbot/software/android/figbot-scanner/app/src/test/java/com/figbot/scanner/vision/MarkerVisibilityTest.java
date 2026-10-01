package com.figbot.scanner.vision;
import org.junit.Test;
import static org.junit.Assert.*;
public class MarkerVisibilityTest {
    @Test public void provenDetectionMaySupportSmallerEdgeWithoutPermittingClipping(){
        double edge=MarkerVisibility.supportedEdge(new float[]{0,0,35,0,35,35,0,35});assertEquals(28,edge,.01);
        assertFalse(camera.contains(facing(0,720)));assertTrue(camera.contains(facing(0,720),edge));
        assertFalse(camera.contains(facing(145,300),edge));assertFalse(camera.contains(facing(0,1500),edge));
        assertEquals(28,MarkerVisibility.supportedEdge(new float[8]),.01);
    }
    private final MarkerVisibility camera=new MarkerVisibility(600,600,320,240,640,480);
    private RigidPose facing(double x,double z){return new RigidPose(new double[][]{{1,0,0},{0,-1,0},{0,0,-1}},new double[]{x,0,z});}
    @Test public void centeredMarkerVisibleButClippedAndTinyMarkersRejected(){
        assertTrue(camera.contains(facing(0,300)));
        assertFalse(camera.contains(facing(145,300)));
        assertFalse(camera.contains(facing(0,1500)));
    }
    @Test public void BackFaceAndBehindCameraRejected(){
        assertFalse(camera.contains(new RigidPose(RigidPose.identity().rotation(),new double[]{0,0,300})));
        assertFalse(camera.contains(facing(0,-300)));
    }
}
