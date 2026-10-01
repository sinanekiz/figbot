package com.figbot.scanner.vision;

/** Read-only multi-frame verification before reusing a persisted camera transform. */
public final class CalibrationReuse {
    public enum State { WAIT, MATCH, MISMATCH }
    private record Sample(long time, boolean matches) {}
    private final java.util.ArrayDeque<Sample> samples=new java.util.ArrayDeque<>();
    private long last=-1;
    public void reset(){last=-1;samples.clear();}
    public State observe(MarkerCalibration.Result saved,RigidPose baseTool,RigidPose cameraMarker,long captured,long now){
        if(captured<=last||now<captured||now-captured>=400_000_000L)return State.WAIT;
        if(last>=0&&captured-last>=400_000_000L)reset();
        last=captured;
        RigidPose observed=saved.observedTool(cameraMarker);
        boolean matches=observed.distance(baseTool)<=12&&observed.angle(baseTool)<=Math.toRadians(8);
        samples.addLast(new Sample(captured,matches));
        while(samples.size()>9)samples.removeFirst();
        if(samples.size()<7||captured-samples.getFirst().time()<600_000_000L)return State.WAIT;
        long good=samples.stream().filter(Sample::matches).count();
        // One bad PnP pose cannot discard a calibration, nor can one good pose
        // authorize a displaced camera. A mixed window remains undecided.
        if(good>=samples.size()-1&&matches)return State.MATCH;
        if(good<=1&&!matches)return State.MISMATCH;
        return State.WAIT;
    }
}
