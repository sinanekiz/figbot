package com.figbot.scanner;
import org.junit.Test;
import static org.junit.Assert.*;

public class ObservationTimingTest {
    @Test public void xiaomiCpuImageAheadOfFrameIsAgedNotDroppedOrFutureDated(){
        long host=5_000_000_000L,frame=2_000_000_000L;
        assertEquals(host-36_000_000L,ObservationTiming.cpuCapture(frame,frame+36_000_000L,frame,host));
        assertEquals(host-36_000_000L,ObservationTiming.cpuCapture(frame,frame-36_000_000L,frame-100_000_000L,host));
        assertEquals(0,ObservationTiming.cpuCapture(frame,frame,frame,host));
        assertEquals(0,ObservationTiming.cpuCapture(frame,frame+101_000_000L,frame,host));
        assertEquals(0,ObservationTiming.cpuCapture(frame,frame-101_000_000L,1,host));
    }
    @Test public void rejectsMissingFutureAndStaleCapture() {
        assertFalse(ObservationTiming.fresh(0, 100));
        assertFalse(ObservationTiming.fresh(101, 100));
        assertTrue(ObservationTiming.fresh(100, 750000100));
        assertFalse(ObservationTiming.fresh(100, 750000101));
    }
    @Test public void movementGateIncludesRotationAndQuaternionSign() {
        float[] p={0,0,0}, q={0,0,0,1};
        assertTrue(ObservationTiming.stationary(p,p,q,new float[]{0,0,0,-1}));
        assertFalse(ObservationTiming.stationary(p,new float[]{0.004f,0,0},q,q));
        assertFalse(ObservationTiming.stationary(p,p,q,new float[]{0,0,0.01f,0.99995f}));
        assertFalse(ObservationTiming.stationary(p,p,q,new float[4]));
    }
}
