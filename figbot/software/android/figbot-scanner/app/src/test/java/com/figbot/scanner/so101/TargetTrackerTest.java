package com.figbot.scanner.so101;

import static org.junit.Assert.*;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import org.junit.Test;

public class TargetTrackerTest {
    private static final long MS=1_000_000;
    private TargetTracker tracker(){TargetTracker t=new TargetTracker(new TargetTracker.Config(25,.7,2,1000*MS,2000*MS,10));t.reset("calibration-a");return t;}
    private TargetTracker.Detection d(double x,long timeMs){return new TargetTracker.Detection(new double[]{x,0,10},.9,timeMs*MS);}
    private List<TargetTracker.Target> frame(TargetTracker t,long ms,TargetTracker.Detection...ds){return t.update(Arrays.asList(ds),ms*MS,"calibration-a");}
    private long confirmed(TargetTracker t,double x){frame(t,100,d(x,100));return frame(t,200,d(x,200)).get(0).id;}
    @Test public void requiresMultipleIndependentFreshFrames() {
        TargetTracker t=tracker();frame(t,100,d(0,100));assertNull(t.reserveNext(100*MS));
        frame(t,150,d(0,100));assertNull(t.reserveNext(150*MS));
        frame(t,200,d(0,200));assertNotNull(t.reserveNext(200*MS));
    }
    @Test public void staleAndFutureDetectionsCannotCreateTargets() {
        TargetTracker t=tracker();assertTrue(frame(t,2000,d(0,100)).isEmpty());
        assertTrue(frame(t,2100,d(0,2200)).isEmpty());
        assertTrue(frame(t,2200,new TargetTracker.Detection(new double[]{0,0,0},.5,2200*MS)).isEmpty());
    }
    @Test public void ttlMakesUnreservedTargetUnavailable() {
        TargetTracker t=tracker();long id=confirmed(t,0);
        assertNull(t.get(id,1201*MS));assertNull(t.reserveNext(1201*MS));
    }
    @Test public void assignmentIsOneToOneWithNearbyTargetsAndReorderedDetections() {
        TargetTracker t=tracker();List<TargetTracker.Target> initial=frame(t,100,d(0,100),d(20,100));
        long first=initial.get(0).id,second=initial.get(1).id;
        frame(t,200,d(19,200),d(1,200));
        assertEquals(1,t.get(first,200*MS).positionMm()[0],0);
        assertEquals(19,t.get(second,200*MS).positionMm()[0],0);
        assertEquals(2,t.snapshot(200*MS).size());
    }
    @Test public void velocityPredictionKeepsIdentitiesWhenNearbyPathsCross() {
        TargetTracker t=tracker();List<TargetTracker.Target> initial=frame(t,100,d(0,100),d(30,100));
        long right=initial.get(0).id,left=initial.get(1).id;
        frame(t,200,d(10,200),d(20,200));frame(t,300,d(10,300),d(20,300));
        assertEquals(20,t.get(right,300*MS).positionMm()[0],0);
        assertEquals(10,t.get(left,300*MS).positionMm()[0],0);
    }
    @Test public void oneDetectionCannotConfirmTwoTracks() {
        TargetTracker t=tracker();frame(t,100,d(0,100),d(10,100));frame(t,200,d(4,200));
        int confirmed=0;for(TargetTracker.Target target:t.snapshot(200*MS))if(target.state==TargetTracker.State.CONFIRMED)confirmed++;
        assertEquals(1,confirmed);
    }
    @Test public void reservationCannotBeSelectedTwice() {
        TargetTracker t=tracker();long id=confirmed(t,0);t.reserve(id,200*MS);
        assertNull(t.reserveNext(200*MS));assertThrows(IllegalStateException.class,()->t.reserve(id,200*MS));
    }
    @Test public void disappearanceNeverBecomesSuccessAndReservationRemainsUnknownUntilReported() {
        TargetTracker t=tracker();long id=confirmed(t,0);t.reserve(id,200*MS);
        frame(t,300);frame(t,1400);
        TargetTracker.Target target=t.get(id,1400*MS);assertEquals(TargetTracker.State.RESERVED,target.state);assertFalse(target.fresh);
        t.markUnknown(id,1400*MS);assertEquals(TargetTracker.State.UNKNOWN,t.get(id,1400*MS).state);
        assertEquals(0,t.collectedCount());assertEquals(1,t.unknownCount());
        assertNull(t.reserveNext(1400*MS));
    }
    @Test public void failedPickBlocksReacquisitionUntilCooldownThenNeedsNewConfirmation() {
        TargetTracker t=tracker();long id=confirmed(t,0);t.reserve(id,200*MS);t.markFailed(id,300*MS);
        assertEquals(1,t.failedCount());
        frame(t,400,d(0,400));frame(t,500,d(0,500));assertNull(t.reserveNext(500*MS));
        frame(t,2300,d(0,2300));assertNull(t.reserveNext(2300*MS));
        frame(t,2400,d(0,2400));TargetTracker.Target next=t.reserveNext(2400*MS);
        assertNotNull(next);assertNotEquals(id,next.id);
    }
    @Test public void confirmedCollectionSuppressesPickupLocationUntilEpochChanges() {
        TargetTracker t=tracker();long id=confirmed(t,0);t.reserve(id,200*MS);t.markCollected(id,300*MS);
        assertEquals(1,t.collectedCount());
        frame(t,400,d(1,400));frame(t,500,d(1,500));assertNull(t.reserveNext(500*MS));
        t.update(Arrays.asList(d(0,600)),600*MS,"calibration-b");
        assertEquals(0,t.collectedCount());
        t.update(Arrays.asList(d(0,700)),700*MS,"calibration-b");TargetTracker.Target next=t.reserveNext(700*MS);
        assertNotNull(next);assertNotEquals(id,next.id);
        assertThrows(IllegalStateException.class,()->t.markCollected(id,700*MS));
    }
    @Test public void collectionSuppressionUsesReservedPickupLocationNotLastObservation() {
        TargetTracker t=tracker();long id=confirmed(t,0);t.reserve(id,200*MS);
        frame(t,300,d(20,300));t.markCollected(id,300*MS);
        frame(t,400,d(0,400),d(30,400));frame(t,500,d(0,500),d(30,500));
        TargetTracker.Target next=t.reserveNext(500*MS);assertNotNull(next);assertEquals(30,next.positionMm()[0],0);
    }
    @Test public void rejectsInvalidPointsMixedFramesAndClockReversal() {
        assertThrows(IllegalArgumentException.class,()->new TargetTracker.Detection(new double[]{Double.NaN,0,0},.9,0));
        TargetTracker t=tracker();frame(t,100,d(0,100));
        assertThrows(IllegalArgumentException.class,()->frame(t,200,d(0,100),d(20,200)));
        assertThrows(IllegalArgumentException.class,()->frame(t,150));
    }
    @Test public void unknownOutcomeDoesNotSuppressForever() {
        TargetTracker t=tracker();long id=confirmed(t,0);t.reserve(id,200*MS);t.markUnknown(id,300*MS);
        frame(t,2300,d(0,2300));frame(t,2400,d(0,2400));assertNotNull(t.reserveNext(2400*MS));
    }
}
