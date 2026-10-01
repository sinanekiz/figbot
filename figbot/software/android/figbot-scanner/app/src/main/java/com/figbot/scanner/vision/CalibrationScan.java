package com.figbot.scanner.vision;

import com.figbot.scanner.so101.*;
import java.util.ArrayList;
import java.util.List;

/** Bounded, slow joint-space probe around the current supported pose. No bus operations. */
public final class CalibrationScan {
    public record Plan(ArmProfile motionProfile, List<int[]> poses) {}
    public static List<int[]> poses(ArmProfile profile,int[] start){
        return plan(profile,start).poses();
    }
    public static Plan plan(ArmProfile profile,int[] start){
        return plan(profile,start,q->true);
    }
    public static Plan planKnownMount(ArmProfile profile,int[] start){
        return planKnownMount(profile,start,q->true);
    }
    /** The tool-to-marker mount is already known: four independent nearby poses
     * suffice for two fitting samples and two held-out checks. No hand-eye
     * rotation excitation is required. Every proposed path still passes the
     * same visibility, encoder and sampled table-clearance checks. */
    public static Plan planKnownMount(ArmProfile profile,int[] start,java.util.function.Predicate<int[]> visible){
        ArmProfile motionProfile=profile.calibrationIngress(start);
        So101Kinematics kin=new So101Kinematics(profile);
        double startZ=heightAboveGround(profile,kin,start);
        if(startZ<0)throw new IllegalArgumentException("Başlangıçta model uç masa düzleminin altında; taban/masa yüksekliğini doğrula.");
        if(!visible.test(start))throw new IllegalArgumentException("Kısa doğrulama için mevcut etiket duruşu kamerada görünmeli.");
        int[] center=start.clone();int[][] limits=profile.envelopes();
        for(int axis=0;axis<4;axis++)center[axis]=Math.max(limits[axis][0],Math.min(limits[axis][1],center[axis]));
        // Opposing shoulder/elbow changes translate the tool while preserving
        // its orientation, the wrist position, jaw opening and passive roll.
        for(int step:new int[]{130,-130,140,-140,150,-150}){
            List<int[]> chosen=new ArrayList<>();chosen.add(start.clone());
            for(int n=1;n<4;n++){
                int[] q=center.clone();q[1]+=n*step;q[2]-=n*step;
                if(!addKnownPose(profile,motionProfile,kin,chosen,q,visible))break;
            }
            if(chosen.size()==4)return new Plan(motionProfile,List.copyOf(chosen));
        }
        // A clipped camera view or a joint boundary may reject one straight
        // sequence. Search a bounded local set, preferring fixed-wrist poses
        // and little orientation change rather than the full twelve-pose scan.
        List<int[]> candidates=new ArrayList<>();
        for(int wrist:new int[]{0,-60,60})for(int base:new int[]{0,-90,90,-150,150})
            for(int shoulder:new int[]{0,-150,150,-300,300,-450,450})for(int pitch:new int[]{0,-90,90}){
                int[] q=center.clone();q[0]+=base;q[1]+=shoulder;q[2]+=-shoulder+pitch;q[3]+=wrist;
                try{profile.validatePose(q);}catch(IllegalArgumentException outside){continue;}
                RigidPose origin=RigidPose.fromMatrix(kin.forwardTransform(start));
                RigidPose pose=RigidPose.fromMatrix(kin.forwardTransform(q));
                if(pose.distance(origin)>80||pose.angle(origin)>Math.toRadians(15)||heightAboveGround(profile,kin,q)<30||!visible.test(q))continue;
                candidates.add(q);
            }
        List<int[]> chosen=new ArrayList<>();chosen.add(start.clone());
        while(chosen.size()<4){
            int[] previous=chosen.get(chosen.size()-1);
            RigidPose previousPose=RigidPose.fromMatrix(kin.forwardTransform(previous));
            candidates.sort(java.util.Comparator.comparingDouble(q->{
                RigidPose pose=RigidPose.fromMatrix(kin.forwardTransform(q));
                return pose.distance(previousPose)+200*pose.angle(previousPose)+(q[3]==start[3]?0:100);
            }));
            boolean added=false;
            for(int[] q:candidates)if(addKnownPose(profile,motionProfile,kin,chosen,q,visible)){added=true;break;}
            if(!added)break;
        }
        if(chosen.size()==4)return new Plan(motionProfile,List.copyOf(chosen));
        throw new IllegalArgumentException("Bu duruşta kamerada görünen dört farklı kısa doğrulama konumu bulunamadı; mevcut kayıt değiştirilmedi.");
    }
    private static boolean addKnownPose(ArmProfile profile,ArmProfile motionProfile,So101Kinematics kin,
            List<int[]> chosen,int[] q,java.util.function.Predicate<int[]> visible){
        try{profile.validatePose(q);}catch(IllegalArgumentException outside){return false;}
        if(heightAboveGround(profile,kin,q)<30||!visible.test(q))return false;
        RigidPose pose=RigidPose.fromMatrix(kin.forwardTransform(q));
        if(pose.distance(RigidPose.fromMatrix(kin.forwardTransform(chosen.get(0))))>80)return false;
        for(int[] old:chosen){
            RigidPose previousPose=RigidPose.fromMatrix(kin.forwardTransform(old));
            // Leave room for endpoint settling. Actual sample admission remains
            // 15 mm or 5 degrees; planning right at that threshold can stall it.
            if(previousPose.distance(pose)<22&&previousPose.angle(pose)<Math.toRadians(7))return false;
        }
        int[] previous=chosen.get(chosen.size()-1);GoalTrajectory leg;
        try{leg=GoalTrajectory.moveTo(motionProfile,previous,q,300);}catch(IllegalArgumentException invalid){return false;}
        double startZ=heightAboveGround(profile,kin,previous),lastZ=startZ;
        boolean rising=chosen.size()==1&&startZ<30;
        for(double t=0;t<=leg.duration()+.019;t+=.02){
            int[] sample=leg.sample(Math.min(t,leg.duration()));double z=heightAboveGround(profile,kin,sample);
            if(!visible.test(sample)||z<(rising?startZ:30)-.01||rising&&lastZ<30&&z<lastZ-.5)return false;
            lastZ=z;
        }
        chosen.add(q.clone());return true;
    }
    /** Only clearances use tabletop height; FK poses stay in the original base frame. */
    private static double heightAboveGround(ArmProfile profile,So101Kinematics kin,int[] q){
        return kin.forward(q)[2]-profile.groundZMm();
    }
    public static Plan plan(ArmProfile profile,int[] start,java.util.function.Predicate<int[]> visible){
        ArmProfile motionProfile=profile.calibrationIngress(start);
        int[][]pattern={{0,0,0,0},{1,0,0,0},{0,0,0,1},{-1,0,0,0},
                {0,-1,1,-1},{1,1,-1,1},{-1,-1,1,1},{1,-1,0,-1},
                {-1,1,-1,-1},{0,1,0,1},{1,0,1,0},{-1,0,-1,1}};
        int[][]limits=profile.envelopes();int[]step={170,100,100,180};
        // Shift the probe centre inward near a recorded edge. Preserve the actual initial
        // pose as sample zero; no goal outside the original range is ever generated.
        int[] center=start.clone();
        for(int i=0;i<4;i++){
            if(limits[i][1]-limits[i][0]<2*step[i])throw new IllegalArgumentException("Tarama için eklem aralığı yetersiz");
            center[i]=Math.max(limits[i][0]+step[i],Math.min(limits[i][1]-step[i],start[i]));
        }
        So101Kinematics kin=new So101Kinematics(profile);
        double startZ=heightAboveGround(profile,kin,start);
        if(startZ<0)throw new IllegalArgumentException("Başlangıçta model uç masa düzleminin altında; taban/masa yüksekliğini doğrula.");
        // Try a small inward elbow shift if the folded pose makes a probe dip low.
        for(int shoulderShift:new int[]{0,-100,-200,100,200})for(int wristShift:new int[]{0,-180,180})for(int baseShift:new int[]{0,170,-170})for(int elbowShift:new int[]{0,-100,-200,100,200}) {
            int[] candidate=center.clone();
            candidate[0]=Math.max(limits[0][0]+step[0],Math.min(limits[0][1]-step[0],center[0]+baseShift));
            candidate[1]=Math.max(limits[1][0]+step[1],Math.min(limits[1][1]-step[1],center[1]+shoulderShift));
            candidate[3]=Math.max(limits[3][0]+step[3],Math.min(limits[3][1]-step[3],center[3]+wristShift));
            candidate[2]=Math.max(limits[2][0]+step[2],Math.min(limits[2][1]-step[2],center[2]+elbowShift));
            List<int[]> result=new ArrayList<>();result.add(start.clone());int[]prev=start;
            boolean clear=true;
            for(int n=1;n<pattern.length && clear;n++) {
                int[]q=candidate.clone();for(int i=0;i<4;i++)q[i]+=pattern[n][i]*step[i];profile.validatePose(q);
                if(!visible.test(q)){clear=false;break;}
                RigidPose proposed=RigidPose.fromMatrix(kin.forwardTransform(q));
                for(int[] old:result){
                    RigidPose previous=RigidPose.fromMatrix(kin.forwardTransform(old));
                    if(previous.distance(proposed)<15&&previous.angle(proposed)<Math.toRadians(5)){clear=false;break;}
                }
                if(!clear)break;
                GoalTrajectory leg=GoalTrajectory.moveTo(motionProfile,prev,q,300);
                double previousZ=startZ;
                for(double t=0;t<=leg.duration()+.019;t+=.02) {
                    int[] sample=leg.sample(Math.min(t,leg.duration()));
                    double z=heightAboveGround(profile,kin,sample);
                    if(!visible.test(sample)){clear=false;break;}
                    // Below 30 mm above the tabletop only the first, rising departure is allowed. Encoder
                    // quantization can change model height by fractions of a mm.
                    boolean lifting=n==1 && startZ<30;
                    if(z<(lifting?startZ:30)-.01 || lifting && previousZ<30 && z<previousZ-.5){clear=false;break;}
                    previousZ=z;
                }
                if(heightAboveGround(profile,kin,q)<30)clear=false;
                result.add(q);prev=q;
            }
            if(clear)return new Plan(motionProfile,List.copyOf(result));
        }
        // A fixed twelve-pose pattern can fail because one orientation hides the
        // label even when many other informative poses are visible. Select a
        // bounded subset and validate every connecting path with the same gates.
        List<int[]> chosen=new ArrayList<>();chosen.add(start.clone());
        int[] previous=start;
        for(int shoulder:new int[]{-100,-200,0,100})for(int wrist:new int[]{0,-100,100,-180,180})
            for(int elbow:new int[]{0,-60,60,-100,100})for(int base:new int[]{0,100,-100,170,-170}){
            int[] q=start.clone();q[0]+=base;q[1]+=shoulder;q[2]+=elbow;q[3]+=wrist;
            try{profile.validatePose(q);}catch(IllegalArgumentException outside){continue;}
            if(!visible.test(q)||heightAboveGround(profile,kin,q)<30)continue;
            RigidPose pose=RigidPose.fromMatrix(kin.forwardTransform(q));boolean distinct=true;
            for(int[] old:chosen){var oldPose=RigidPose.fromMatrix(kin.forwardTransform(old));
                if(oldPose.distance(pose)<15&&oldPose.angle(pose)<Math.toRadians(5)){distinct=false;break;}}
            if(!distinct)continue;
            var leg=GoalTrajectory.moveTo(motionProfile,previous,q,300);boolean clear=true;
            double lastZ=heightAboveGround(profile,kin,previous);boolean rising=chosen.size()==1&&startZ<30;
            for(double t=0;t<=leg.duration()+.019;t+=.02){
                int[] sample=leg.sample(Math.min(t,leg.duration()));double z=heightAboveGround(profile,kin,sample);
                if(!visible.test(sample)||z<(rising?startZ:30)-.01||rising&&lastZ<30&&z<lastZ-.5){clear=false;break;}lastZ=z;
            }
            if(!clear)continue;
            chosen.add(q);previous=q;if(chosen.size()==12)return new Plan(motionProfile,List.copyOf(chosen));
        }
        throw new IllegalArgumentException("Bu duruşta masa üzerinde ve kamera görüşünde kalan tarama bulunamadı. Etiketi kadrajın ortasına al veya Elle ölçüm seç.");

    }
}
