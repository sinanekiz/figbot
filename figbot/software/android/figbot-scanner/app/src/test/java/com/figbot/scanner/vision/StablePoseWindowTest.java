package com.figbot.scanner.vision;
import org.junit.Test;
import static org.junit.Assert.*;
public class StablePoseWindowTest {
    @Test public void admittedRotationsAreAveragedAcrossWrapWithoutInventingStability(){
        StablePoseWindow w=new StablePoseWindow();
        for(int i=0;i<6;i++){
            double a=Math.toRadians(i%2==0?179:-179);
            w.add(1_000_000_000L+i*100_000_000L,1,new RigidPose(
                new double[][]{{Math.cos(a),-Math.sin(a),0},{Math.sin(a),Math.cos(a),0},{0,0,1}},new double[]{0,0,300}));
        }
        RigidPose mean=w.result(1_550_000_000L,1);assertNotNull(mean);
        RigidPose expected=new RigidPose(new double[][]{{-1,0,0},{0,-1,0},{0,0,1}},new double[]{0,0,300});
        assertTrue(mean.angle(expected)<1e-7);
    }
    private static RigidPose pose(double x){return new RigidPose(RigidPose.identity().rotation(),new double[]{x,0,300});}
    @Test public void intermittentMissingFramesAndOneOutlierDoNotEraseConsensus(){
        StablePoseWindow w=new StablePoseWindow();
        for(int i=0;i<7;i++)w.add(1_000_000_000L+i*150_000_000L,1,pose(i==3?40:i%2));
        RigidPose result=w.result(1_950_000_000L,1);assertNotNull(result);assertTrue(result.translation()[0]<1);
        assertNull(w.result(2_400_000_000L,1));
    }
    @Test public void duplicateFramesSessionsAndMovementCannotCreateStability(){
        StablePoseWindow w=new StablePoseWindow();
        for(int i=0;i<8;i++)w.add(1_000_000_000L,1,pose(0));
        assertNull(w.result(1_100_000_000L,1));
        for(int i=1;i<6;i++)w.add(1_000_000_000L+i*100_000_000L,1,pose(0));
        assertNotNull(w.result(1_550_000_000L,1));
        w.add(1_600_000_000L,1,pose(30));assertNull(w.result(1_650_000_000L,1));
        assertNull(w.result(1_650_000_000L,2));assertEquals(0,w.size());
    }
    @Test public void noisyRotationCannotBeAveragedIntoFalseConfidence(){
        StablePoseWindow w=new StablePoseWindow();
        for(int i=0;i<10;i++){
            double a=i*.1;w.add(1_000_000_000L+i*100_000_000L,1,new RigidPose(
                new double[][]{{Math.cos(a),-Math.sin(a),0},{Math.sin(a),Math.cos(a),0},{0,0,1}},new double[]{0,0,300}));
        }
        assertNull(w.result(1_950_000_000L,1));
    }
}
