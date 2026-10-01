package com.figbot.scanner.vision;

import java.util.ArrayList;
import java.util.List;

/** Consensus of independent, already quality-checked frames. Single worker owner. */
public final class StablePoseWindow {
    private record Entry(long captured, RigidPose pose) {}
    private final List<Entry> entries=new ArrayList<>();
    private int generation=-1;
    private long lastCapture=-1;
    public void clear(){entries.clear();lastCapture=-1;}
    public void add(long captured,int session,RigidPose pose) {
        if(session!=generation){clear();generation=session;}
        if(captured<=lastCapture)return;
        lastCapture=captured;entries.add(new Entry(captured,pose));
        while(entries.size()>12)entries.remove(0);
    }
    public RigidPose result(long now,int session) {
        if(session!=generation){clear();generation=session;return null;}
        entries.removeIf(e->now<e.captured || now-e.captured>1_500_000_000L);
        if(entries.size()<5)return null;
        Entry latest=entries.get(entries.size()-1);
        if(now-latest.captured>=400_000_000L)return null;
        List<Entry> best=List.of();Entry center=null;double bestCost=Double.POSITIVE_INFINITY;
        for(Entry a:entries) {
            List<Entry> inliers=new ArrayList<>();double cost=0;
            for(Entry b:entries)if(a.pose.distance(b.pose)<=3 && a.pose.angle(b.pose)<=Math.toRadians(3)){
                inliers.add(b);cost+=a.pose.distance(b.pose)+10*a.pose.angle(b.pose);
            }
            if(!inliers.contains(latest))continue;
            if(inliers.size()>best.size() || inliers.size()==best.size() && cost<bestCost){best=inliers;center=a;bestCost=cost;}
        }
        if(best.size()<5 || latest.captured-best.get(0).captured<300_000_000L)return null;
        double[] mean=new double[3];
        for(Entry e:best){double[] t=e.pose.translation();for(int i=0;i<3;i++)mean[i]+=t[i]/best.size();}
        // Average only the already admitted tight rotation cluster on SO(3).
        // A single medoid's orientation used to pass straight into hand-eye fit.
        double[] tangent=new double[3];
        for(Entry e:best){
            RigidPose delta=center.pose.inverse().compose(e.pose);double[][] r=delta.rotation();
            double angle=delta.angle(RigidPose.identity());double scale=angle<1e-8?.5:angle/(2*Math.sin(angle));
            tangent[0]+=scale*(r[2][1]-r[1][2])/best.size();
            tangent[1]+=scale*(r[0][2]-r[2][0])/best.size();
            tangent[2]+=scale*(r[1][0]-r[0][1])/best.size();
        }
        double a=Math.sqrt(tangent[0]*tangent[0]+tangent[1]*tangent[1]+tangent[2]*tangent[2]);
        double s=a<1e-8?1:Math.sin(a)/a,c=a<1e-8?.5:(1-Math.cos(a))/(a*a);
        double[][] k={{0,-tangent[2],tangent[1]},{tangent[2],0,-tangent[0]},{-tangent[1],tangent[0],0}};
        double[][] rotation=RigidPose.identity().rotation();
        for(int i=0;i<3;i++)for(int j=0;j<3;j++){
            rotation[i][j]+=s*k[i][j];for(int n=0;n<3;n++)rotation[i][j]+=c*k[i][n]*k[n][j];
        }
        return new RigidPose(center.pose.compose(new RigidPose(rotation,new double[3])).rotation(),mean);
    }
    public int size(){return entries.size();}
}
