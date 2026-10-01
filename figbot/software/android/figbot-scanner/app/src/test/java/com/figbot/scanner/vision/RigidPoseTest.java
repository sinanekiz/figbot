package com.figbot.scanner.vision;

import org.junit.Test;
import static org.junit.Assert.*;
import com.figbot.scanner.so101.*;

public class RigidPoseTest {
    @Test public void inverseAndComposition(){
        RigidPose p=new RigidPose(new double[][]{{0,-1,0},{1,0,0},{0,0,1}},new double[]{20,30,40});
        assertArrayEquals(new double[]{2,3,4},p.inverse().map(p.map(new double[]{2,3,4})),1e-9);
        assertEquals(0,p.compose(p.inverse()).distance(RigidPose.identity()),1e-9);
        assertEquals(Math.PI/2,p.angle(RigidPose.identity()),1e-9);
    }
    @Test public void refusesReflectionsAndNonfinite(){
        assertThrows(IllegalArgumentException.class,()->new RigidPose(new double[][]{{-1,0,0},{0,1,0},{0,0,1}},new double[3]));
        assertThrows(IllegalArgumentException.class,()->new RigidPose(RigidPose.identity().rotation(),new double[]{0,Double.NaN,0}));
    }
    @Test public void fkPoseHasSameTipAndProperRotation(){
        ArmProfile p=ArmProfile.unverifiedDefaults();So101Kinematics k=new So101Kinematics(p);
        int[]raw=p.home();RigidPose pose=RigidPose.fromMatrix(k.forwardTransform(raw));
        assertArrayEquals(java.util.Arrays.copyOf(k.forward(raw),3),pose.translation(),1e-8);
    }
    @Test public void observationRejectsStaleFutureAndOldSession(){
        ArucoTracker.Observation o=new ArucoTracker.Observation(100,3,RigidPose.identity(),RigidPose.identity(),new float[8],0,true,null);
        assertTrue(o.fresh(200,3));assertFalse(o.fresh(99,3));assertFalse(o.fresh(200,4));assertFalse(o.fresh(400_000_100L,3));
    }
    @Test public void scanPreservesRealStartAndProbesInward(){
        ArmProfile p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] start={2022,767,3946,2738,1152,792};
        CalibrationScan.Plan plan=CalibrationScan.plan(p,start);
        assertArrayEquals(start,plan.poses().get(0));assertEquals(12,plan.poses().size());
        assertEquals(2738,plan.motionProfile().envelopes()[3][1]);
        assertEquals(2732,p.envelopes()[3][1]);
        for(int[] q:plan.poses().subList(1,12)) {
            p.validatePose(q);assertEquals(1152,q[4]);assertEquals(792,q[5]);
        }
        start[3]=2741; // nine counts outside is not a small ingress allowance
        assertThrows(IllegalArgumentException.class,()->CalibrationScan.plan(p,start));
    }
}
