package com.figbot.scanner.so101;
import java.util.List;

/** Frozen approach, seating, close, lift, basket and release. No detection-dependent retargets. */
public record PickupCycle(List<GoalTrajectory> legs) {
    public PickupCycle {
        legs=List.copyOf(legs);
        if(legs.size()!=6)throw new IllegalArgumentException("A pickup cycle requires six legs");
    }
    public static PickupCycle plan(ArmProfile profile,int[] measured,double[] target,int speed){
        speedForLeg(0,speed);
        if(profile==null||target==null||target.length!=3)
            throw new IllegalArgumentException("Arm profile and three target coordinates required");
        for(double coordinate:target)if(!Double.isFinite(coordinate))
            throw new IllegalArgumentException("Target coordinates must be finite");
        profile.validatePose(measured);
        PickupCycle best=null;IllegalArgumentException last=null;
        // Search complete task solutions, not merely the first reachable approach.
        // Existing pitch set, insertion preference and motor limits are unchanged.
        for(int degrees:new int[]{0,-15,-30,-45,-60,-75,-85}){
            for(double mm:new double[]{15,10})try{
                PickupCycle candidate=candidate(profile,measured,target,speed,degrees,mm);
                if(best==null||candidate.durationSeconds()<best.durationSeconds()-1e-9)best=candidate;
                break; // Prefer 15 mm seating; 10 mm is a feasibility fallback, not a speed shortcut.
            }catch(IllegalArgumentException unavailable){last=unavailable;}
        }
        if(best==null)throw new IllegalArgumentException("Hedef için tüm alma ve sepet yolu sınırlar içinde bulunamadı",last);
        return best;
    }

    /** Offline candidate construction: no IO, torque, retries or grasp-success claim. */
    static PickupCycle candidate(ArmProfile profile,int[] measured,double[] target,int speed,int degrees,double mm){
        GoalTrajectory approach=PickupPlan.approachAtPitch(profile,measured,target,speedForLeg(0,speed),degrees);
        GoalTrajectory seat=PickupPlan.seat(profile,approach.end(),measured,mm,speedForLeg(1,speed));
        GoalTrajectory close=PickupPlan.close(profile,seat.end(),speedForLeg(2,speed));
        GoalTrajectory lift=PickupPlan.lift(profile,close.end(),speedForLeg(3,speed));
        int[] basket=profile.basket();basket[4]=measured[4];basket[5]=profile.gripperClosed();
        GoalTrajectory carry=PickupPlan.checked(profile,lift.end(),basket,speedForLeg(4,speed));
        int[] released=basket.clone();released[5]=profile.gripperOpen();
        GoalTrajectory release=PickupPlan.checked(profile,basket,released,speedForLeg(5,speed));
        return new PickupCycle(List.of(approach,seat,close,lift,carry,release));
    }

    /** Nominal trajectory time only; excludes planning, IO, settling and visual verification. */
    public double durationSeconds(){return legs.stream().mapToDouble(GoalTrajectory::duration).sum();}

    /** Rebuild only the next committed leg from feedback, preserving its speed policy. */
    public GoalTrajectory legFromMeasured(ArmProfile profile,int index,int[] measured,int retainedJaw,int speed){
        int legSpeed=speedForLeg(index,speed);
        if(legs.size()!=6)throw new IllegalStateException("A pickup cycle requires six legs");
        // Settling leaves small differences from the planned body pose. Closing
        // or opening the jaws must not correct the other five axes at the same time.
        if(index==2)return PickupPlan.close(profile,measured,legSpeed);
        int[] goal=index==5?measured.clone():legs.get(index).end();
        if(index==3||index==4)goal[5]=retainedJaw;
        if(index==5)goal[5]=profile.gripperOpen();
        return PickupPlan.checked(profile,measured,goal,legSpeed);
    }

    /** Selected speed applies throughout; contact phases are explicitly capped at 600 counts/s. */
    public static int speedForLeg(int index,int speed){
        if(index<0||index>=6)throw new IllegalArgumentException("Pickup leg must be 0..5");
        if(speed<1||speed>3400)throw new IllegalArgumentException("Finite speed must be 1..3400");
        return index==1||index==2||index==5?PickupPlan.contactSpeed(speed):speed;
    }
}
