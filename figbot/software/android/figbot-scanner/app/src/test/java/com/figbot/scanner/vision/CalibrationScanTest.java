package com.figbot.scanner.vision;
import com.figbot.scanner.so101.*;
import org.junit.Test;
import static org.junit.Assert.*;
public class CalibrationScanTest {
    @Test public void bothScansUseMeasuredTableBelowBaseWithoutMovingTheCoordinateFrame(){
        var original=ArmProfile.unverifiedDefaults().withPassiveWristRoll();var p=original.withGroundZMm(-65);
        int[] start={2443,2099,3598,1795,1152,790};var k=new So101Kinematics(p);
        double initial=k.forward(start)[2];assertTrue(initial<0&&initial>p.groundZMm());
        assertThrows(IllegalArgumentException.class,()->CalibrationScan.plan(original,start));
        assertThrows(IllegalArgumentException.class,()->CalibrationScan.planKnownMount(original,start));
        for(boolean full:new boolean[]{false,true}){
            var plan=full?CalibrationScan.plan(p,start):CalibrationScan.planKnownMount(p,start);
            assertEquals(full?12:4,plan.poses().size());assertEquals(-65,plan.motionProfile().groundZMm(),0);
            int[] previous=start;
            for(int index=1;index<plan.poses().size();index++){
                int[] q=plan.poses().get(index);original.validatePose(q);
                assertTrue(k.forward(q)[2]>=p.groundZMm()+30);
                var leg=GoalTrajectory.moveTo(plan.motionProfile(),previous,q,300);
                double last=k.forward(previous)[2];
                for(double t=0;t<=leg.duration()+.019;t+=.02){
                    double z=k.forward(leg.sample(Math.min(t,leg.duration())))[2];
                    assertTrue(z>=(index==1?initial:p.groundZMm()+30)-.01);
                    if(index==1&&last<p.groundZMm()+30)assertTrue(z>=last-.5);last=z;
                }
                previous=q;
            }
        }
    }
    @Test public void knownMountUsesFourNearbyTranslationsAtLatestMeasuredFoldedPose(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();int[] start={2346,763,3877,2728,1152,870};
        var plan=CalibrationScan.planKnownMount(p,start,q->q[0]==start[0]&&q[3]==start[3]);
        assertEquals(4,plan.poses().size());assertArrayEquals(start,plan.poses().get(0));
        var k=new So101Kinematics(p);var origin=RigidPose.fromMatrix(k.forwardTransform(start));
        int[] previous=start;
        for(int[] q:plan.poses()){
            p.validatePose(q);assertEquals(start[0],q[0]);assertEquals(start[3],q[3]);
            assertEquals(start[4],q[4]);assertEquals(start[5],q[5]);
            var pose=RigidPose.fromMatrix(k.forwardTransform(q));assertEquals(0,origin.angle(pose),1e-6);assertTrue(origin.distance(pose)<=80);
            var leg=GoalTrajectory.moveTo(plan.motionProfile(),previous,q,300);
            for(double t=0;t<=leg.duration()+.019;t+=.02){
                int[] sample=leg.sample(Math.min(t,leg.duration()));assertTrue(k.forward(sample)[2]>=30);
                assertEquals(start[0],sample[0]);assertEquals(start[3],sample[3]);
            }
            previous=q;
        }
        for(int i=0;i<4;i++)for(int j=i+1;j<4;j++){
            var a=RigidPose.fromMatrix(k.forwardTransform(plan.poses().get(i)));
            var b=RigidPose.fromMatrix(k.forwardTransform(plan.poses().get(j)));
            assertTrue(a.distance(b)>=22||a.angle(b)>=Math.toRadians(7));
        }
    }
    @Test public void knownMountRejectsInvisibleConnectingPathsEvenWithVisibleEndpoints(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();int[] start={2346,763,3877,2728,1152,870};
        assertThrows(IllegalArgumentException.class,()->CalibrationScan.planKnownMount(p,start,
                q->q[0]==start[0]&&q[3]==start[3]&&(q[1]-start[1])%100==0&&(q[2]-start[2])%100==0));
    }
    @Test public void knownMountDoesNotAcceptRepeatedOrInvisibleOnlyPose(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();int[] start={2346,763,3877,2728,1152,870};
        assertThrows(IllegalArgumentException.class,()->CalibrationScan.planKnownMount(p,start,q->java.util.Arrays.equals(start,q)));
        assertThrows(IllegalArgumentException.class,()->CalibrationScan.planKnownMount(p,start,q->false));
    }
    @Test public void knownMountLowStartMayOnlyRiseAboveExistingThirtyMillimetreFloor(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();int[] start={1971,922,3944,2680,1151,792};
        var scan=CalibrationScan.planKnownMount(p,start);assertEquals(4,scan.poses().size());
        var k=new So101Kinematics(p);double initial=k.forward(start)[2],last=initial;
        var first=GoalTrajectory.moveTo(scan.motionProfile(),start,scan.poses().get(1),300);
        for(double t=0;t<=first.duration()+.019;t+=.02){
            double z=k.forward(first.sample(Math.min(t,first.duration())))[2];
            assertTrue(z>=initial-.01);if(last<30)assertTrue(z>=last-.5);last=z;
        }
        for(int index=1;index<4;index++){p.validatePose(scan.poses().get(index));assertTrue(k.forward(scan.poses().get(index))[2]>=30);}
    }
    @Test public void visibleSubsetCanReplacePatternWithHiddenWristAngles(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();int[] start={2246,2231,2983,2182,1153,897};
        var scan=CalibrationScan.plan(p,start,q->q[3]==2182);assertEquals(12,scan.poses().size());
        var k=new So101Kinematics(p);int[] prev=start;boolean yaw=false,pitch=false;
        for(var q:scan.poses()){p.validatePose(q);assertEquals(2182,q[3]);yaw|=q[0]!=start[0];pitch|=q[1]!=start[1];
            var leg=GoalTrajectory.moveTo(scan.motionProfile(),prev,q,300);
            for(double t=0;t<=leg.duration();t+=.02)assertTrue(k.forward(leg.sample(t))[2]>=Math.min(30,k.forward(start)[2])-.01);prev=q;
        }assertTrue(yaw&&pitch);
    }
    @Test public void lowExtendedPoseCanUseRaisedShoulderScanCenter(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();int[] start={2246,2219,2977,2178,1151,896};
        var scan=CalibrationScan.plan(p,start,q->q[1]<=2219);assertEquals(12,scan.poses().size());
        for(var q:scan.poses()){p.validatePose(q);assertTrue(q[1]<=2219);}
    }
    @Test public void invisibleScanRejectedBeforeAnyMotion(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        assertThrows(IllegalArgumentException.class,()->CalibrationScan.plan(p,new int[]{2372,852,3693,2731,1152,792},q->false));
    }
    @Test public void canChooseAlternativeCenterWithinVisibleRegion(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] start={2372,852,3693,2731,1152,792};
        var scan=CalibrationScan.plan(p,start,q->q[0]>=2300);
        assertEquals(12,scan.poses().size());
        int[] previous=start;
        for(int[] pose:scan.poses()){
            var leg=GoalTrajectory.moveTo(scan.motionProfile(),previous,pose,300);
            for(double t=0;t<=leg.duration();t+=.02)assertTrue(leg.sample(t)[0]>=2300);
            previous=pose;
        }
    }
    @org.junit.Test public void measuredLowHomeMayOnlyDepartUpward(){
        var profile=com.figbot.scanner.so101.ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] start={1971,922,3944,2680,1151,792};
        var plan=CalibrationScan.plan(profile,start);
        var kin=new com.figbot.scanner.so101.So101Kinematics(profile);
        double initial=kin.forward(start)[2];
        var leg=com.figbot.scanner.so101.GoalTrajectory.moveTo(plan.motionProfile(),start,plan.poses().get(1),300);
        double last=initial;
        for(double t=0;t<=leg.duration();t+=.02){
            double z=kin.forward(leg.sample(t))[2];
            org.junit.Assert.assertTrue(z>=initial-.01);
            if(last<30)org.junit.Assert.assertTrue(z>=last-.5);
            last=z;
        }
        org.junit.Assert.assertTrue(kin.forward(plan.poses().get(1))[2]>=30);
    }
    @Test public void edgeStartCannotProduceDuplicateThatStallsSampling() {
        ArmProfile p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        var poses=CalibrationScan.poses(p,new int[]{2372,852,3693,2731,1152,792});
        So101Kinematics kin=new So101Kinematics(p);assertEquals(12,poses.size());
        for(int i=0;i<poses.size();i++)for(int j=i+1;j<poses.size();j++){
            RigidPose a=RigidPose.fromMatrix(kin.forwardTransform(poses.get(i)));
            RigidPose b=RigidPose.fromMatrix(kin.forwardTransform(poses.get(j)));
            assertTrue(a.distance(b)>=15||a.angle(b)>=Math.toRadians(5));
        }
    }
}
