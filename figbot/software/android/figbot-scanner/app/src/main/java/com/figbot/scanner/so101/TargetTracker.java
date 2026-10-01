package com.figbot.scanner.so101;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Bounded, one-to-one target association in calibrated robot millimetres. */
public final class TargetTracker {
    public enum State { CANDIDATE, CONFIRMED, RESERVED, FAILED, UNKNOWN, COLLECTED }

    public static final class Config {
        public final double gateMm, minConfidence, suppressionRadiusMm;
        public final int minConfirmations;
        public final long ttlNs, failureCooldownNs;
        public Config(double gateMm, double minConfidence, int minConfirmations,
                      long ttlNs, long failureCooldownNs, double suppressionRadiusMm) {
            if (!Double.isFinite(gateMm) || gateMm <= 0 || !Double.isFinite(minConfidence)
                    || minConfidence < 0 || minConfidence > 1 || minConfirmations < 2
                    || ttlNs <= 0 || failureCooldownNs <= 0 || !Double.isFinite(suppressionRadiusMm)
                    || suppressionRadiusMm <= 0)
                throw new IllegalArgumentException("Invalid target tracking policy");
            this.gateMm=gateMm;this.minConfidence=minConfidence;this.minConfirmations=minConfirmations;
            this.ttlNs=ttlNs;this.failureCooldownNs=failureCooldownNs;this.suppressionRadiusMm=suppressionRadiusMm;
        }
    }
    public static final class Detection {
        private final double[] positionMm;
        public final double confidence;
        public final long capturedNs;
        public Detection(double[] robotMm, double confidence, long capturedNs) {
            positionMm=point(robotMm);
            if(!Double.isFinite(confidence)||confidence<0||confidence>1||capturedNs<0)
                throw new IllegalArgumentException("Invalid target observation");
            this.confidence=confidence;this.capturedNs=capturedNs;
        }
        public double[] positionMm(){return positionMm.clone();}
    }
    public static final class Target {
        public final long id, lastSeenNs;
        public final String epoch;
        public final State state;
        public final int confirmations;
        public final double confidence;
        public final boolean fresh;
        private final double[] positionMm;
        private Target(Track track,String epoch,long nowNs,long ttlNs) {
            id=track.id;this.epoch=epoch;state=track.state;lastSeenNs=track.lastSeenNs;
            confirmations=track.hits;confidence=track.confidence;positionMm=track.position.clone();
            fresh=nowNs>=lastSeenNs&&nowNs-lastSeenNs<=ttlNs;
        }
        public double[] positionMm(){return positionMm.clone();}
    }
    private static final class Track {
        final long id;
        double[] position, reservationPosition, velocity={0,0,0};
        double confidence;
        long lastSeenNs, cooldownStartedNs=-1;
        int hits=1;
        State state=State.CANDIDATE;
        Track(long id,Detection detection) {
            this.id=id;position=detection.positionMm();confidence=detection.confidence;lastSeenNs=detection.capturedNs;
        }
    }
    private static final class Suppression {
        final double[] position;
        final long startedNs;
        final boolean permanent;
        Suppression(double[] position,long startedNs,boolean permanent) {
            this.position=position.clone();this.startedNs=startedNs;this.permanent=permanent;
        }
    }
    private final Config config;
    private final Map<Long,Track> tracks=new LinkedHashMap<>();
    private final List<Suppression> suppressions=new ArrayList<>();
    private String epoch;
    private long nextId=1,lastNowNs=-1,lastFrameNs=-1,collectedCount=0,failedCount=0,unknownCount=0;

    public TargetTracker(Config config) {
        if(config==null)throw new IllegalArgumentException("Tracking policy required");
        this.config=config;
    }

    /** AR session or calibration changes require a new epoch and invalidate every old reservation. */
    public synchronized void reset(String newEpoch) {
        if(newEpoch==null||newEpoch.trim().isEmpty())throw new IllegalArgumentException("Calibration / AR epoch required");
        epoch=newEpoch;tracks.clear();suppressions.clear();lastNowNs=-1;lastFrameNs=-1;
        collectedCount=0;failedCount=0;unknownCount=0;
        // IDs are intentionally not reused: late action results from a previous epoch cannot match.
    }

    /** Detections must come from one frame; old/future frames never confirm or move a target. */
    public synchronized List<Target> update(List<Detection> observations,long nowNs,String currentEpoch) {
        if(currentEpoch==null||currentEpoch.trim().isEmpty())throw new IllegalArgumentException("Epoch required");
        if(!currentEpoch.equals(epoch))reset(currentEpoch);
        checkClock(nowNs);expire(nowNs);
        if(observations==null||observations.size()>64)throw new IllegalArgumentException("At most 64 detections per frame");
        List<Detection> detections=new ArrayList<>();long frameNs=-1;
        for(Detection detection:observations) {
            if(detection==null)throw new IllegalArgumentException("Null target observation");
            if(frameNs<0)frameNs=detection.capturedNs;
            else if(frameNs!=detection.capturedNs)throw new IllegalArgumentException("Mixed camera frame timestamps");
            if(detection.capturedNs>nowNs||nowNs-detection.capturedNs>config.ttlNs
                    ||detection.capturedNs<=lastFrameNs||detection.confidence<config.minConfidence
                    ||suppressed(detection.positionMm,nowNs))continue;
            detections.add(detection);
        }
        // Replayed frames cannot erase confirmations by looking like a new empty frame.
        if(frameNs>=0&&(frameNs<=lastFrameNs||frameNs>nowNs||nowNs-frameNs>config.ttlNs))return snapshot(nowNs);
        if(frameNs>=0)lastFrameNs=frameNs;
        List<Track> active=new ArrayList<>();
        for(Track track:tracks.values()) {
            if(track.state==State.CANDIDATE||track.state==State.CONFIRMED||track.state==State.RESERVED)
                active.add(track);
        }
        Set<Integer> matchedDetections=new HashSet<>();
        if(!active.isEmpty()) {
            int n=active.size(),m=detections.size();double[][] costs=new double[n][m+n];
            double dummy=config.gateMm*config.gateMm+1;
            for(int i=0;i<n;i++) {
                Track track=active.get(i);
                for(int j=0;j<m;j++) {
                    Detection d=detections.get(j);
                    double dt=(d.capturedNs-track.lastSeenNs)/1e9;
                    double[] predicted=track.position.clone();
                    if(dt>0&&track.state!=State.RESERVED)for(int axis=0;axis<3;axis++)predicted[axis]+=track.velocity[axis]*dt;
                    double distance=distance(predicted,d.positionMm);
                    // Both prediction and last measured point must remain within a bounded association gate.
                    boolean allowed=dt>0&&distance<=config.gateMm
                            &&distance(track.position,d.positionMm)<=2*config.gateMm;
                    costs[i][j]=allowed?distance*distance:1e12;
                }
                for(int j=m;j<m+n;j++)costs[i][j]=dummy;
            }
            int[] assignment=assign(costs);
            for(int i=0;i<n;i++) {
                Track track=active.get(i);int assigned=assignment[i];
                if(assigned>=0&&assigned<m&&costs[i][assigned]<dummy) {
                    Detection d=detections.get(assigned);matchedDetections.add(assigned);
                    double dt=(d.capturedNs-track.lastSeenNs)/1e9;
                    for(int axis=0;axis<3;axis++)track.velocity[axis]=(d.positionMm[axis]-track.position[axis])/dt;
                    track.position=d.positionMm();track.confidence=d.confidence;track.lastSeenNs=d.capturedNs;
                    track.hits++;
                    if(track.state!=State.RESERVED&&track.hits>=config.minConfirmations)track.state=State.CONFIRMED;
                } else if(track.state!=State.RESERVED) {
                    track.hits=0;track.velocity=new double[3];track.state=State.CANDIDATE;
                }
            }
        }
        for(int j=0;j<detections.size();j++)if(!matchedDetections.contains(j)&&tracks.size()<64) {
            Track track=new Track(nextId++,detections.get(j));tracks.put(track.id,track);
        }
        return snapshot(nowNs);
    }

    /** Selects by confidence then stable ID; callers may use reserve(id) for their own travel cost. */
    public synchronized Target reserveNext(long nowNs) {
        checkClock(nowNs);expire(nowNs);
        Track best=null;
        for(Track track:tracks.values())if(selectable(track,nowNs)) {
            if(best==null||track.confidence>best.confidence||(track.confidence==best.confidence&&track.id<best.id))best=track;
        }
        if(best==null)return null;
        best.state=State.RESERVED;best.reservationPosition=best.position.clone();
        return new Target(best,epoch,nowNs,config.ttlNs);
    }
    public synchronized Target reserve(long id,long nowNs) {
        checkClock(nowNs);expire(nowNs);Track track=tracks.get(id);
        if(track==null||!selectable(track,nowNs))throw new IllegalStateException("Target is stale, unconfirmed or unavailable");
        track.state=State.RESERVED;track.reservationPosition=track.position.clone();
        return new Target(track,epoch,nowNs,config.ttlNs);
    }
    /** Explicit external evidence is required. Mere disappearance/occlusion must use markUnknown. */
    public synchronized void markCollected(long id,long nowNs) {
        checkClock(nowNs);Track track=reserved(id);track.state=State.COLLECTED;
        collectedCount++;
        suppressions.add(new Suppression(track.reservationPosition,nowNs,true));
    }
    public synchronized void markFailed(long id,long nowNs) { finishUncertain(id,nowNs,State.FAILED); }
    public synchronized void markUnknown(long id,long nowNs) { finishUncertain(id,nowNs,State.UNKNOWN); }
    private void finishUncertain(long id,long nowNs,State state) {
        checkClock(nowNs);Track track=reserved(id);track.state=state;track.cooldownStartedNs=nowNs;
        if(state==State.FAILED)failedCount++;else unknownCount++;
        track.hits=0;track.velocity=new double[3];
        suppressions.add(new Suppression(track.reservationPosition,nowNs,false));
    }
    public synchronized Target get(long id,long nowNs) {
        checkClock(nowNs);expire(nowNs);Track track=tracks.get(id);
        return track==null?null:new Target(track,epoch,nowNs,config.ttlNs);
    }
    public synchronized List<Target> snapshot(long nowNs) {
        checkClock(nowNs);expire(nowNs);List<Target> result=new ArrayList<>();
        for(Track track:tracks.values())result.add(new Target(track,epoch,nowNs,config.ttlNs));
        return Collections.unmodifiableList(result);
    }
    public synchronized long collectedCount() { return collectedCount; }
    public synchronized long failedCount() { return failedCount; }
    public synchronized long unknownCount() { return unknownCount; }
    public synchronized int availableCount(long nowNs) {
        checkClock(nowNs);expire(nowNs);int count=0;
        for(Track track:tracks.values())if(selectable(track,nowNs))count++;
        return count;
    }
    private Track reserved(long id) {
        Track track=tracks.get(id);
        if(track==null||track.state!=State.RESERVED)throw new IllegalStateException("No current reservation for target " + id);
        return track;
    }
    private boolean selectable(Track track,long nowNs) {
        return track.state==State.CONFIRMED&&nowNs-track.lastSeenNs<=config.ttlNs
                &&!suppressed(track.position,nowNs);
    }
    private boolean suppressed(double[] point,long nowNs) {
        for(Suppression s:suppressions)if((s.permanent||nowNs-s.startedNs<config.failureCooldownNs)
                &&distance(point,s.position)<=config.suppressionRadiusMm)return true;
        return false;
    }
    private void expire(long nowNs) {
        suppressions.removeIf(s->!s.permanent&&nowNs-s.startedNs>=config.failureCooldownNs);
        Iterator<Track> iterator=tracks.values().iterator();
        while(iterator.hasNext()) {
            Track track=iterator.next();
            if(track.state==State.RESERVED)continue; // Occlusion never reports a successful harvest.
            if((track.state==State.FAILED||track.state==State.UNKNOWN)
                    &&nowNs-track.cooldownStartedNs<config.failureCooldownNs)continue;
            if(track.state==State.FAILED||track.state==State.UNKNOWN||track.state==State.COLLECTED
                    ||nowNs-track.lastSeenNs>config.ttlNs)iterator.remove();
        }
    }
    private void checkClock(long nowNs) {
        if(epoch==null)throw new IllegalStateException("Set calibration / AR epoch before tracking");
        if(nowNs<0||nowNs<lastNowNs)throw new IllegalArgumentException("Monotonic observation clock required");
        lastNowNs=nowNs;
    }

    /** Rectangular Hungarian assignment, including one unmatched dummy column per track. */
    private static int[] assign(double[][] cost) {
        int n=cost.length,m=cost[0].length;double[] u=new double[n+1],v=new double[m+1];
        int[] p=new int[m+1],way=new int[m+1];
        for(int i=1;i<=n;i++) {
            p[0]=i;int j0=0;double[] min=new double[m+1];java.util.Arrays.fill(min,Double.POSITIVE_INFINITY);
            boolean[] used=new boolean[m+1];
            do {
                used[j0]=true;int i0=p[j0],j1=0;double delta=Double.POSITIVE_INFINITY;
                for(int j=1;j<=m;j++)if(!used[j]) {
                    double current=cost[i0-1][j-1]-u[i0]-v[j];
                    if(current<min[j]){min[j]=current;way[j]=j0;}
                    if(min[j]<delta){delta=min[j];j1=j;}
                }
                for(int j=0;j<=m;j++)if(used[j]){u[p[j]]+=delta;v[j]-=delta;}else min[j]-=delta;
                j0=j1;
            }while(p[j0]!=0);
            do {int j1=way[j0];p[j0]=p[j1];j0=j1;}while(j0!=0);
        }
        int[] result=new int[n];java.util.Arrays.fill(result,-1);
        for(int j=1;j<=m;j++)if(p[j]!=0)result[p[j]-1]=j-1;
        return result;
    }
    private static double[] point(double[] point) {
        if(point==null||point.length!=3)throw new IllegalArgumentException("Robot XYZ millimetres required");
        for(double v:point)if(!Double.isFinite(v))throw new IllegalArgumentException("Nonfinite target");
        return point.clone();
    }
    private static double distance(double[] a,double[] b) {
        return Math.hypot(Math.hypot(a[0]-b[0],a[1]-b[1]),a[2]-b[2]);
    }
}
