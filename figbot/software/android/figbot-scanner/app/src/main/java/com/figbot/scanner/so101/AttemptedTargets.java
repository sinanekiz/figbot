package com.figbot.scanner.so101;
import java.util.ArrayList;
import java.util.List;

/** Table-plane identity memory; attempted does not mean grasped. Explicit batch reset only. */
public final class AttemptedTargets {
    public static final double RADIUS_MM=35;
    private final List<double[]> points=new ArrayList<>();
    public synchronized boolean contains(double[] p){
        for(double[] old:points)if(Math.hypot(old[0]-p[0],old[1]-p[1])<=RADIUS_MM)return true;
        return false;
    }
    public synchronized void add(double[] p){
        if(p==null||p.length<2||!Double.isFinite(p[0])||!Double.isFinite(p[1]))throw new IllegalArgumentException("Finite target required");
        if(!contains(p))points.add(new double[]{p[0],p[1]});
    }
    public synchronized List<double[]> snapshot(){List<double[]> copy=new ArrayList<>();for(double[] p:points)copy.add(p.clone());return copy;}
    public synchronized void clear(){points.clear();}
}
