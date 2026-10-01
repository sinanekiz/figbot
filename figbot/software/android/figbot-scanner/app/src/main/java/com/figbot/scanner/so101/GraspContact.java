package com.figbot.scanner.so101;

/** Current rise plus jaw stall: contact evidence, never proof of a fig or force in N. */
public final class GraspContact {
    private static final int MIN_CURRENT_RAW=8;
    private static final int CURRENT_RISE_RAW=6;
    private static final int MIN_POSITION_GAP_COUNTS=12;
    private static final int MAX_STALL_SPEED=5;
    private static final int POSITION_STABILITY_COUNTS=3;
    private static final long MAX_SAMPLE_GAP_NS=100_000_000L;
    private static final long MIN_CONTACT_INTERVAL_NS=180_000_000L;
    private static final int MIN_CONTACT_SAMPLES=3;
    private final int baseline;
    private long since=-1,last=-1;
    private int anchor,count;
    public GraspContact(int idleCurrentRaw){baseline=Math.abs(idleCurrentRaw);}
    public boolean observe(long now,int position,int commanded,int speed,int currentRaw){
        // Conservative contact evidence only. A historically observed light grasp
        // at currentRaw=3 and a 7-count gap remains unverified, not proven empty.
        // These raw current thresholds are not a force calibration.
        boolean possible=position-commanded>=MIN_POSITION_GAP_COUNTS
                &&Math.abs(speed)<=MAX_STALL_SPEED
                &&Math.abs(currentRaw)>=Math.max(MIN_CURRENT_RAW,baseline+CURRENT_RISE_RAW);
        if(!possible||last>=0&&(now<=last||now-last>MAX_SAMPLE_GAP_NS)){since=-1;count=0;}
        last=now;
        if(!possible)return false;
        if(since<0||Math.abs(position-anchor)>POSITION_STABILITY_COUNTS){since=now;anchor=position;count=0;}
        return ++count>=MIN_CONTACT_SAMPLES&&now-since>=MIN_CONTACT_INTERVAL_NS;
    }
}
