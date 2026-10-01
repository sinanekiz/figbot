package com.figbot.scanner.so101;

/** Supervised bench pickup legs. No torque enabling, no claim of grasp success. */
public final class PickupPlan {
    private PickupPlan() {}
    /** Ground pickup may need a downward tool angle; horizontal-only IK falsely
     * rejects reachable targets. Check the approach and subsequent lift together. */
    public static GoalTrajectory approach(ArmProfile profile,int[] measured,double[] target,int speed) {
        IllegalArgumentException last=null;
        for(int degrees:new int[]{0,-15,-30,-45,-60,-75,-85})try{
            GoalTrajectory route=approachAtPitch(profile,measured,target,speed,degrees);
            lift(profile,route.end(),speed); // Do not arrive at a pose from which the planned lift is impossible.
            return route;
        }catch(IllegalArgumentException unavailable){last=unavailable;}
        throw new IllegalArgumentException("Hedef için sınırlar içinde yaklaşma ve kaldırma açısı bulunamadı",last);
    }
    /** One bounded candidate. The caller must validate all remaining task stages. */
    static GoalTrajectory approachAtPitch(ArmProfile profile,int[] measured,double[] target,int speed,int degrees){
        int[] goal=new So101Kinematics(profile).inverse(target,Math.toRadians(degrees),measured);
        goal[5]=profile.gripperOpen();
        return checked(profile,measured,goal,speed);
    }
    public static GoalTrajectory close(ArmProfile profile,int[] measured) {
        return close(profile,measured,profile.speedLimit());
    }
    public static GoalTrajectory close(ArmProfile profile,int[] measured,int speed) {
        int[] goal=measured.clone();goal[5]=profile.gripperClosed();
        return checked(profile,measured,goal,contactSpeed(speed));
    }
    /** Horizontal seating only; never continue the downward tool axis into the table. */
    public static GoalTrajectory seat(ArmProfile profile,int[] approach,int[] original,double mm){
        return seat(profile,approach,original,mm,profile.speedLimit());
    }
    public static GoalTrajectory seat(ArmProfile profile,int[] approach,int[] original,double mm,int speed){
        int seatSpeed=contactSpeed(speed);
        So101Kinematics k=new So101Kinematics(profile);double[] p=k.forward(approach);
        // Insertion follows the jaw's forward axis, not the line from a folded
        // starting pose. That line can point backward relative to the fingers.
        double[][] tool=k.forwardTransform(approach);
        double dx=tool[0][2],dy=tool[1][2],length=Math.hypot(dx,dy);
        if(length<.08)throw new IllegalArgumentException("Seating direction unavailable");
        int[] goal=k.inverse(new double[]{p[0]+mm*dx/length,p[1]+mm*dy/length,p[2]},p[3],approach);
        goal[5]=profile.gripperOpen();return checked(profile,approach,goal,seatSpeed);
    }
    public static GoalTrajectory lift(ArmProfile profile,int[] measured) {
        return lift(profile,measured,profile.speedLimit());
    }
    public static GoalTrajectory lift(ArmProfile profile,int[] measured,int speed) {
        So101Kinematics kin=new So101Kinematics(profile);
        double[] pose=kin.forward(measured);
        int[] goal=kin.inverse(new double[]{pose[0],pose[1],pose[2]+50},pose[3],measured);
        // A contact hold can stop short of the configured empty-jaw closure.
        // Keep that measured opening instead of squeezing back to a nominal value.
        goal[5]=measured[5];
        return checked(profile,measured,goal,speed);
    }
    /** Explicit conservative cap for jaw motion and final seating, never a fixed speed. */
    static int contactSpeed(int selected){
        if(selected<1||selected>3400)throw new IllegalArgumentException("Finite speed must be 1..3400");
        return Math.min(selected,600);
    }
    public static GoalTrajectory checked(ArmProfile profile,int[] start,int[] goal,int speed) {
        GoalTrajectory route=GoalTrajectory.moveTo(profile,start,goal,speed);
        So101Kinematics kin=new So101Kinematics(profile);
        // FK remains in the robot base frame. Clearance alone is relative to
        // the measured tabletop, which can sit below a raised robot base.
        // Sampled tip clearance does not certify jaws, links or obstacles.
        double ground=profile.groundZMm();
        double initial=kin.forward(start)[2]-ground,previous=initial;
        if(initial<0||kin.forward(goal)[2]-ground<8)throw new IllegalArgumentException("Planlanan uç yolu masa yüzeyine fazla yakın.");
        for(double t=0;t<=route.duration()+.02;t+=.02){
            double z=kin.forward(route.sample(Math.min(t,route.duration())))[2]-ground;
            // An already low measured hold may only depart upward, never dip
            // farther down. Once clear, the ordinary 8 mm floor applies.
            if(z<(initial<8?initial:8)-.01||previous<8&&z<previous-.5)
                throw new IllegalArgumentException("Planlanan uç yolu masa yüzeyine fazla yakın.");
            if(z>=8)initial=8;previous=z;
        }
        return route;
    }
}
