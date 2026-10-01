package com.figbot.scanner.so101;
import org.junit.Test;
import static org.junit.Assert.*;
public class PickupPlanTest {
    @Test public void raisedBaseAllowsPickupAndLiftBelowBaseWithoutChangingFkOrJointBounds(){
        var original=ArmProfile.unverifiedDefaults().withPassiveWristRoll();var p=original.withGroundZMm(-65);
        int[] start={2606,899,3697,2609,1152,790};var k=new So101Kinematics(p);
        var approach=PickupPlan.approach(p,start,new double[]{196,-139,-40},300);
        assertEquals(-40,k.forward(approach.end())[2],2);
        assertArrayEquals(new So101Kinematics(original).forward(start),k.forward(start),0);
        var close=PickupPlan.close(p,approach.end(),300);var lift=PickupPlan.lift(p,close.end(),300);
        assertEquals(k.forward(close.end())[2]+50,k.forward(lift.end())[2],2);
        for(var leg:new GoalTrajectory[]{approach,close,lift})for(double t=0;t<=leg.duration()+.019;t+=.02){
            int[] q=leg.sample(Math.min(t,leg.duration()));original.validatePose(q);
            assertTrue(k.forward(q)[2]>=p.groundZMm()+8-.01);
        }
        assertThrows(IllegalArgumentException.class,()->PickupPlan.close(original,approach.end(),300));
    }
    @Test public void raisedBaseStillRejectsInsufficientClearanceAndBelowGroundStarts(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll().withGroundZMm(-65);
        int[] above={2443,2099,3598,1795,1152,790};
        int[] near={2443,2299,3398,1795,1152,790};
        int[] below={2443,2349,3348,1795,1152,790};
        var k=new So101Kinematics(p);
        assertTrue(k.forward(near)[2]>-65&&k.forward(near)[2]<-57);
        assertTrue(k.forward(below)[2]<-65);
        assertThrows(IllegalArgumentException.class,()->PickupPlan.checked(p,above,near,300));
        assertThrows(IllegalArgumentException.class,()->PickupPlan.checked(p,below,above,300));
        var departure=PickupPlan.checked(p,near,above,300);double previous=k.forward(near)[2];
        for(double t=0;t<=departure.duration()+.019;t+=.02){
            double z=k.forward(departure.sample(Math.min(t,departure.duration())))[2];
            assertTrue(z>=k.forward(near)[2]-.01);if(previous<p.groundZMm()+8)assertTrue(z>=previous-.5);previous=z;
        }
    }
    @Test public void measuredLowHoldCanOnlyLeaveUpward(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();int[] q={2403,2230,3176,1931,1152,1151};var k=new So101Kinematics(p);
        double[] low=k.forward(q);assertTrue(low[2]>=0&&low[2]<8);
        int[] raised=k.inverse(new double[]{low[0],low[1],low[2]+25},low[3],q);raised[5]=q[5];
        var route=PickupPlan.checked(p,q,raised,180);double previous=low[2];
        for(double t=0;t<=route.duration();t+=.02){double z=k.forward(route.sample(t))[2];assertTrue(z>=low[2]-.01);if(previous<8)assertTrue(z>=previous-.5);previous=z;}
        assertThrows(IllegalArgumentException.class,()->PickupPlan.close(p,q));
    }
    @Test public void recordedTableTargetCanUseDownwardPitchWithinUnchangedLimits(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] start={2527,854,3647,2730,1152,790};double[] target={196,-139,10};
        var kin=new So101Kinematics(p);
        assertThrows(IllegalArgumentException.class,()->kin.inverse(target,0,start));
        var route=PickupPlan.approach(p,start,target,300);int[] goal=route.end();
        p.validatePose(goal);assertEquals(start[4],goal[4]);assertEquals(p.gripperOpen(),goal[5]);
        double[] actual=kin.forward(goal);for(int i=0;i<3;i++)assertEquals(target[i],actual[i],2);
        assertTrue(actual[3]<0);
        var lift=PickupPlan.lift(p,goal);assertEquals(actual[2]+50,kin.forward(lift.end())[2],2);
        for(double t=0;t<=route.duration();t+=.02)assertTrue(kin.forward(route.sample(t))[2]>=8);
    }
    @Test(expected=IllegalArgumentException.class)public void angleSearchCannotMakeDistantTargetReachable(){
        PickupPlan.approach(ArmProfile.unverifiedDefaults().withPassiveWristRoll(),new int[]{2527,854,3647,2730,1152,790},new double[]{2000,0,10},300);
    }
    private final ArmProfile profile=ArmProfile.unverifiedDefaults();
    private final int[] measured={2100,1600,3200,2200,3130,1153};
    @Test public void closureDoesNotMoveArmOrPassiveRoll(){
        GoalTrajectory route=PickupPlan.close(profile,measured);
        for(double t=0;t<=route.duration();t+=.01){
            int[] sample=route.sample(t);for(int i=0;i<5;i++)assertEquals(measured[i],sample[i]);
        }
        assertEquals(profile.gripperClosed(),route.end()[5]);
    }
    @Test public void liveSeatClosesAtMeasuredPoseWithoutBodyCorrection(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] actual={2747,1721,3722,1895,1151,1151};
        var route=PickupPlan.close(p,actual);
        for(double t=0;t<=route.duration();t+=.01)
            for(int i=0;i<5;i++)assertEquals(actual[i],route.sample(t)[i]);
        assertEquals(p.gripperClosed(),route.end()[5]);
    }
    @Test public void insertionFollowsJawsAndIsIndependentOfStartingPose(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();var k=new So101Kinematics(p);
        int[] q={2747,1721,3722,1895,1151,1151};double[] before=k.forward(q);double[][] tool=k.forwardTransform(q);
        var a=PickupPlan.seat(p,q,new int[]{2316,855,3832,2477,1151,794},10);
        var b=PickupPlan.seat(p,q,new int[]{1971,921,3946,2681,1151,791},10);
        assertArrayEquals(a.end(),b.end());double[] after=k.forward(a.end());
        double length=Math.hypot(tool[0][2],tool[1][2]);
        assertEquals(before[0]+10*tool[0][2]/length,after[0],2);
        assertEquals(before[1]+10*tool[1][2]/length,after[1],2);
        assertEquals(before[2],after[2],2);
    }
    @Test public void liftKeepsClosedJawAndRaisesTip50mm(){
        int[] closed=measured.clone();closed[5]=profile.gripperClosed();
        GoalTrajectory route=PickupPlan.lift(profile,closed);
        So101Kinematics kin=new So101Kinematics(profile);
        double[] before=kin.forward(closed),after=kin.forward(route.end());
        assertEquals(before[0],after[0],2);assertEquals(before[1],after[1],2);
        assertEquals(before[2]+50,after[2],2);
        for(double t=0;t<=route.duration();t+=.01){
            assertEquals(closed[4],route.sample(t)[4]);assertEquals(closed[5],route.sample(t)[5]);
        }
    }
    @Test public void savedClosureIsExactAndClosingSpeedRespectsSelection(){
        var custom=profile.withSavedPoses(profile.home(),profile.basket(),780,profile.gripperOpen());
        var slow=PickupPlan.close(custom,measured,300);var fast=PickupPlan.close(custom,measured,1200);
        assertEquals(780,slow.end()[5]);assertEquals(780,fast.end()[5]);
        assertTrue(slow.maxSpeed()<=300+1e-6);assertTrue(fast.maxSpeed()<=600+1e-6);
        assertTrue(fast.duration()<slow.duration());
        for(double t=0;t<=fast.duration();t+=.01)
            for(int i=0;i<5;i++)assertEquals(measured[i],fast.sample(t)[i]);
    }
    @Test public void liftPreservesContactOpeningInsteadOfForcingEmptyJawClosure(){
        int[] contact=measured.clone();contact[5]=1020;
        var route=PickupPlan.lift(profile,contact,1200);
        assertEquals(1020,route.end()[5]);
        for(double t=0;t<=route.duration();t+=.01)assertEquals(1020,route.sample(t)[5]);
    }
    @Test public void contactCapDoesNotAcceptInvalidRequestedSpeeds(){
        assertThrows(IllegalArgumentException.class,()->PickupPlan.close(profile,measured,3401));
        assertThrows(IllegalArgumentException.class,()->PickupPlan.close(profile,measured,0));
        assertThrows(IllegalArgumentException.class,()->PickupPlan.seat(profile,measured,measured,10,3401));
    }
    @Test(expected=IllegalArgumentException.class) public void belowTableGoalCannotBeDriven(){
        int[] low={2308,2871,2337,1864,3127,894};
        PickupPlan.checked(profile,measured,low,300);
    }
}
