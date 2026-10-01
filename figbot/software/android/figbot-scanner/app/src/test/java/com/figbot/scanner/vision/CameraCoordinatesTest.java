package com.figbot.scanner.vision;
import org.junit.Test;
import static org.junit.Assert.*;
public class CameraCoordinatesTest {
    @Test public void worldRebaseCancelsForSameFramePointAndCamera(){
        RigidPose camera=new RigidPose(new double[][]{{1,0,0},{0,1,0},{0,0,1}},new double[]{100,200,300});
        double[] arPoint={30,-40,-600};double[] world=camera.map(arPoint);
        assertArrayEquals(new double[]{30,40,600},CameraCoordinates.fromWorld(camera,world),1e-8);
        RigidPose jump=new RigidPose(new double[][]{{0,-1,0},{1,0,0},{0,0,1}},new double[]{-800,450,20});
        assertArrayEquals(new double[]{30,40,600},CameraCoordinates.fromWorld(jump.compose(camera),jump.map(world)),1e-8);
    }
    @Test public void axesAreOpenCvRightDownForward(){
        assertArrayEquals(new double[]{2,3,4},CameraCoordinates.fromWorld(RigidPose.identity(),new double[]{2,-3,-4}),0);
    }
}
