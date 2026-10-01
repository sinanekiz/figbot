package com.figbot.scanner.so101;

import org.junit.Test;
import static org.junit.Assert.*;

public class GraspAlignmentTest {
    @Test public void correctionBelowRaisedBaseStillKeepsActualTableClearance(){
        var base=ArmProfile.unverifiedDefaults().withPassiveWristRoll();var p=base.withGroundZMm(-65);
        int[] actual={2443,2099,3598,1795,1152,790},desired=actual.clone();desired[1]-=15;
        var route=GraspAlignment.correction(p,actual,desired,180);var k=new So101Kinematics(p);
        assertTrue(k.forward(route.end())[2]<0);
        for(double t=0;t<=route.duration()+.019;t+=.02){
            int[] q=route.sample(Math.min(t,route.duration()));base.validatePose(q);
            assertTrue(k.forward(q)[2]>=p.groundZMm()+8-.01);
        }
        assertThrows(IllegalArgumentException.class,()->GraspAlignment.correction(base,actual,desired,180));
    }
    private final ArmProfile profile = ArmProfile.unverifiedDefaults().withPassiveWristRoll();
    // Measured bench pose. Offset targets below are mathematical fixtures,
    // not measured evidence of the real fruit's position or TCP accuracy.
    private final int[] measured = {2747,1721,3722,1895,1151,1151};

    @Test public void twentyCountsPerJointDoesNotMeanCartesianArrival() {
        int[] desired = {2727,1701,3702,1875,1151,1151};
        for (int axis=0;axis<4;axis++) assertEquals(20,Math.abs(desired[axis]-measured[axis]));
        var residual = GraspAlignment.evaluate(profile, measured, desired);
        assertEquals(21.4552,residual.positionMm(),.001);
        assertFalse(residual.aligned());
        assertThrows(IllegalArgumentException.class,
                () -> GraspAlignment.correction(profile,measured,desired,180));
    }

    @Test public void nearPoseNeedsNoExtraMovementAndJawDoesNotAffectAlignment() {
        int[] desired = measured.clone();desired[0]+=2;desired[5]=profile.gripperClosed();
        var residual = GraspAlignment.evaluate(profile,measured,desired);
        assertTrue(residual.positionMm()<1);
        assertTrue(residual.aligned());
        assertThrows(IllegalArgumentException.class,
                () -> GraspAlignment.correction(profile,measured,desired,180));
    }

    @Test public void smallModelLagGetsOneUnclippedCompensationWithMeasuredJawAndRoll() {
        int[] desired=measured.clone();desired[1]-=15;desired[4]+=2;desired[5]=870;
        var residual=GraspAlignment.evaluate(profile,measured,desired);
        assertTrue(residual.positionMm()>4&&residual.positionMm()<5);
        assertFalse(residual.aligned());
        var route=GraspAlignment.correction(profile,measured,desired,180);
        int[] end=route.end();
        for(int axis=0;axis<4;axis++)assertEquals(2*desired[axis]-measured[axis],end[axis]);
        assertEquals(measured[4],end[4]);assertEquals(measured[5],end[5]);
        var k=new So101Kinematics(profile);
        // The command compensates upward for a below-goal measurement;
        // it is not treated as a newly inferred fruit location.
        assertTrue(k.forward(measured)[2]<k.forward(desired)[2]);
        assertTrue(k.forward(desired)[2]<k.forward(end)[2]);
        for(double t=0;t<=route.duration();t+=.01){
            int[] sample=route.sample(t);
            assertEquals(measured[4],sample[4]);assertEquals(measured[5],sample[5]);
            assertTrue(k.forward(sample)[2]>=8);
        }
        assertArrayEquals(new int[]{2747,1721,3722,1895,1151,1151},measured);
    }

    @Test public void correctionCannotReplaceRollAdjustment() {
        int[] desired=measured.clone();desired[4]+=4;
        assertFalse(GraspAlignment.evaluate(profile,measured,desired).aligned());
        assertThrows(IllegalArgumentException.class,
                () -> GraspAlignment.correction(profile,measured,desired,180));
    }

    @Test public void passiveRollWrapHasSameSmallAngleWithoutDrivingRoll() {
        int[] actual=measured.clone(),desired=measured.clone();actual[4]=4095;desired[4]=1;
        assertTrue(GraspAlignment.evaluate(profile,actual,desired).aligned());
    }

    @Test public void plausibleCartesianErrorCannotHideLargeSingleJointCorrection() {
        int[] desired=measured.clone();desired[3]+=25;
        var residual=GraspAlignment.evaluate(profile,measured,desired);
        assertTrue(residual.positionMm()>4&&residual.positionMm()<8);
        assertThrows(IllegalArgumentException.class,
                () -> GraspAlignment.correction(profile,measured,desired,180));
    }

    @Test public void compensationAtEnvelopeEdgeIsRejectedNotClipped() {
        int[] actual=measured.clone(),desired=measured.clone();actual[0]=3370;desired[0]=3385;
        profile.validatePose(actual);profile.validatePose(desired);
        var residual=GraspAlignment.evaluate(profile,actual,desired);
        assertTrue(residual.positionMm()>4&&residual.positionMm()<8);
        assertThrows(IllegalArgumentException.class,
                () -> GraspAlignment.correction(profile,actual,desired,180));
    }

    @Test public void compensationStillObeysTheExistingTableClearance() {
        int[] actual=measured.clone(),desired=measured.clone();actual[1]+=25;desired[1]+=40;
        var residual=GraspAlignment.evaluate(profile,actual,desired);
        var k=new So101Kinematics(profile);
        assertTrue(residual.positionMm()>4&&residual.positionMm()<8);
        assertTrue(k.forward(actual)[2]>=8);assertTrue(k.forward(desired)[2]>=8);
        assertThrows(IllegalArgumentException.class,
                () -> GraspAlignment.correction(profile,actual,desired,180));
    }

    @Test public void invalidRawOrProfileCannotBecomeAligned() {
        assertThrows(IllegalArgumentException.class,()->GraspAlignment.evaluate(null,measured,measured));
        assertThrows(IllegalArgumentException.class,()->GraspAlignment.evaluate(profile,new int[5],measured));
        int[] invalid=measured.clone();invalid[0]=4096;
        assertThrows(IllegalArgumentException.class,()->GraspAlignment.evaluate(profile,invalid,measured));
        invalid[0]=1800;
        assertThrows(IllegalArgumentException.class,()->GraspAlignment.evaluate(profile,invalid,measured));
    }
}
