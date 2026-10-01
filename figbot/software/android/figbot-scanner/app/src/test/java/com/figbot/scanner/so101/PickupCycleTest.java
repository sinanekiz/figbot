package com.figbot.scanner.so101;
import org.junit.Test;
import static org.junit.Assert.*;
public class PickupCycleTest {
    @Test public void completesGroundTargetsRejectedByEarlyApproachChoice(){
        for(double ground:new double[]{0,-65}){
            var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll().withGroundZMm(ground);
            int[] start={2606,899,3697,2609,1152,790};double[] target={160,-40,ground+25};
            // The actual cycle lifts after seating. Requiring a lift at the
            // approach itself used to reject these otherwise complete paths.
            if(ground==0)assertThrows(IllegalArgumentException.class,()->PickupPlan.approach(p,start,target,1200));
            else{
                var first=PickupPlan.approach(p,start,target,1200);
                for(double mm:new double[]{15,10})assertThrows(IllegalArgumentException.class,()->{
                    var seat=PickupPlan.seat(p,first.end(),start,mm,1200);
                    PickupPlan.lift(p,seat.end(),1200);
                });
            }
            var planned=PickupCycle.plan(p,start,target,1200);
            assertEquals(6,planned.legs().size());
            assertEquals(p.gripperOpen(),planned.legs().get(5).end()[5]);
        }
    }
    @Test public void choosesShortestCompleteCandidateWithPreferredInsertionAndDeterministicTies(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll().withGroundZMm(-65);
        int[] start={2606,899,3697,2609,1152,790};double[] target={196,-139,-40};
        var chosen=PickupCycle.plan(p,start,target,1200);double minimum=Double.POSITIVE_INFINITY;
        int feasible=0;
        for(int pitch:new int[]{0,-15,-30,-45,-60,-75,-85})
            for(double mm:new double[]{15,10})try{
                var candidate=PickupCycle.candidate(p,start,target,1200,pitch,mm);
                minimum=Math.min(minimum,candidate.durationSeconds());feasible++;break;
            }catch(IllegalArgumentException rejected){}
        assertTrue(feasible>1);assertEquals(minimum,chosen.durationSeconds(),1e-9);
        var again=PickupCycle.plan(p,start,target,1200);
        for(int i=0;i<6;i++){
            var leg=chosen.legs().get(i);
            assertArrayEquals(leg.end(),again.legs().get(i).end());
            if(i>0)assertArrayEquals(chosen.legs().get(i-1).end(),leg.start());
            assertTrue(leg.maxSpeed()<=PickupCycle.speedForLeg(i,1200)+1e-6);
        }
        assertArrayEquals(new int[]{2606,899,3697,2609,1152,790},start);
        assertArrayEquals(new double[]{196,-139,-40},target,0);
    }
    @Test public void rejectsInvalidRequestsAndDoesNotReturnPartialCycles(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] start={2606,899,3697,2609,1152,790};
        for(double[] target:new double[][]{{Double.NaN,0,25},{140,Double.POSITIVE_INFINITY,25},{1,2},{2000,0,25}})
            assertThrows(IllegalArgumentException.class,()->PickupCycle.plan(p,start,target,1200));
        assertThrows(IllegalArgumentException.class,()->PickupCycle.plan(p,start,new double[]{196,-139,25},0));
        assertThrows(IllegalArgumentException.class,()->new PickupCycle(java.util.List.of()));
        var cycle=PickupCycle.plan(p,start,new double[]{196,-139,25},1200);
        assertThrows(UnsupportedOperationException.class,()->cycle.legs().clear());
    }
    @Test public void raisedBaseCycleSeatsAtNegativeBaseZAndChecksEveryLegAgainstActualTable(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll().withGroundZMm(-65);
        int[] start={2606,899,3697,2609,1152,790};var k=new So101Kinematics(p);
        var cycle=PickupCycle.plan(p,start,new double[]{196,-139,-40},300);
        assertEquals(6,cycle.legs().size());
        for(int index=0;index<3;index++)assertEquals(-40,k.forward(cycle.legs().get(index).end())[2],2);
        for(var leg:cycle.legs())for(double t=0;t<=leg.duration()+.019;t+=.02){
            int[] q=leg.sample(Math.min(t,leg.duration()));p.validatePose(q);
            assertTrue(k.forward(q)[2]>=p.groundZMm()+8-.01);
        }
    }
    @Test public void frozenCycleCarriesClosedToRecordedBasketBeforeOpening(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] start={2606,899,3697,2609,1152,790};
        var cycle=PickupCycle.plan(p,start,new double[]{196,-139,10},300);
        assertEquals(6,cycle.legs().size());
        assertEquals(p.gripperOpen(),cycle.legs().get(0).end()[5]);
        assertEquals(p.gripperOpen(),cycle.legs().get(1).end()[5]);
        for(int i=2;i<=4;i++)assertEquals(p.gripperClosed(),cycle.legs().get(i).end()[5]);
        for(int i=0;i<4;i++)assertEquals(p.basket()[i],cycle.legs().get(4).end()[i]);
        assertEquals(p.gripperOpen(),cycle.legs().get(5).end()[5]);
        var k=new So101Kinematics(p);var a=k.forward(cycle.legs().get(0).end());var b=k.forward(cycle.legs().get(1).end());
        assertEquals(a[2],b[2],2);double advance=Math.hypot(b[0]-a[0],b[1]-a[1]);assertTrue(advance>=9&&advance<=17);
        for(var leg:cycle.legs())assertEquals(start[4],leg.end()[4]);
    }
    @Test public void replanningPreservesSelectedSpeedForEveryLeg(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] start={2606,899,3697,2609,1152,790};double[] target={196,-139,10};
        var slow=PickupCycle.plan(p,start,target,300);var fast=PickupCycle.plan(p,start,target,1200);
        for(int index=0;index<6;index++){
            assertEquals(300,PickupCycle.speedForLeg(index,300));
            assertEquals(index==1||index==2||index==5?600:1200,PickupCycle.speedForLeg(index,1200));
            var planned=fast.legs().get(index);
            var resumed=fast.legFromMeasured(p,index,planned.start(),p.gripperClosed(),1200);
            assertArrayEquals(planned.end(),resumed.end());
            assertEquals(planned.duration(),resumed.duration(),1e-9);
            assertTrue(resumed.maxSpeed()<=PickupCycle.speedForLeg(index,1200)+1e-6);
            assertTrue(slow.legs().get(index).maxSpeed()<=300+1e-6);
        }
        assertTrue(fast.legs().get(3).duration()<slow.legs().get(3).duration());
        assertTrue(fast.legs().get(4).duration()<slow.legs().get(4).duration());
        var carry=fast.legs().get(4);
        assertTrue(fast.legFromMeasured(p,4,carry.start(),p.gripperClosed(),1200).duration()
                <fast.legFromMeasured(p,4,carry.start(),p.gripperClosed(),300).duration());
    }
    @Test public void measuredClosingHoldsBodyAndRetainsContactJawThroughLiftAndCarry(){
        var p=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] start={2606,899,3697,2609,1152,790};
        var cycle=PickupCycle.plan(p,start,new double[]{196,-139,10},1200);
        int[] measured=cycle.legs().get(1).end();measured[0]+=2;measured[1]-=2;
        var close=cycle.legFromMeasured(p,2,measured,0,1200);
        for(double t=0;t<=close.duration();t+=.01)
            for(int i=0;i<5;i++)assertEquals(measured[i],close.sample(t)[i]);
        assertEquals(p.gripperClosed(),close.end()[5]);
        int retained=1020;measured[5]=retained;
        for(int index=3;index<=4;index++){
            var leg=cycle.legFromMeasured(p,index,measured,retained,1200);
            for(double t=0;t<=leg.duration();t+=.01)assertEquals(retained,leg.sample(t)[5]);
            measured=leg.end();
        }
        measured[0]-=2;
        var release=cycle.legFromMeasured(p,5,measured,retained,1200);
        for(double t=0;t<=release.duration();t+=.01)
            for(int i=0;i<5;i++)assertEquals(measured[i],release.sample(t)[i]);
        assertEquals(p.gripperOpen(),release.end()[5]);
    }
}
