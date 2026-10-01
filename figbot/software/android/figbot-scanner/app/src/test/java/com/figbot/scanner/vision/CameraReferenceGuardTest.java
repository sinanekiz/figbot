package com.figbot.scanner.vision;

import org.junit.Test;
import static org.junit.Assert.*;
import static com.figbot.scanner.vision.CameraReferenceGuard.State.*;

public class CameraReferenceGuardTest {
    @Test public void frameArrivingAfterTickStartUsesFreshEvaluationClock(){
        CameraReferenceGuard live=new CameraReferenceGuard(()->1_002_000_000L);
        assertEquals(WAIT,guard.update(1_000_000_000L,1_001_000_000L,true,true));
        assertEquals(READY,live.updateNow(1_001_000_000L,true,true));
        assertEquals(WAIT,live.updateNow(500_000_000L,true,true));
    }
    private final CameraReferenceGuard guard = new CameraReferenceGuard();
    private CameraReferenceGuard.State frame(long ms, boolean reference, boolean marker) {
        return guard.update(ms*1_000_000L,ms*1_000_000L,reference,marker);
    }
    @Test public void singlePoseSpikeWaitsThenRecoversWithoutInvalidating() {
        assertEquals(READY,frame(1000,true,true));
        assertEquals(WAIT,frame(1020,false,true));
        assertEquals(WAIT,frame(1040,true,true));
        assertEquals(WAIT,frame(1289,true,true));
        assertEquals(READY,frame(1290,true,true));
        assertEquals(1020_000_000L,guard.acceptAfterNs());
    }
    @Test public void trackingLossNeedsNewFramesAndFreshMarkerBeforeResume() {
        assertEquals(WAIT,frame(1000,false,false));
        assertEquals(WAIT,frame(1100,true,false));
        assertEquals(WAIT,frame(1200,true,true));
        assertEquals(WAIT,guard.update(1450_000_000L,1200_000_000L,true,true));
        assertEquals(READY,frame(1450,true,true));
    }
    @Test public void sustainedDisplacementLatchesInvalidEvenIfItReturnsLater() {
        assertEquals(WAIT,frame(1000,false,true));
        assertEquals(WAIT,frame(2499,false,true));
        assertEquals(INVALID,frame(2500,false,true));
        assertEquals(INVALID,frame(3000,true,true));
        guard.reset();assertEquals(READY,frame(3100,true,true));
    }
    @Test public void intermittentGoodFramesDoNotConcealPersistentDrift() {
        frame(1000,false,true);frame(1500,true,true);frame(1700,false,true);
        frame(2000,true,true);frame(2200,false,true);
        assertEquals(INVALID,frame(2500,true,true));
    }
    @Test public void markerLossAloneDoesNotInvalidateCameraReference() {
        assertEquals(WAIT,frame(1000,true,false));
        assertEquals(WAIT,frame(6000,true,false));
        assertEquals(WAIT,frame(6100,true,true));
        assertEquals(READY,frame(6350,true,true));
    }
    @Test public void cameraRecoversWhileObjectStillMissing() {
        assertEquals(WAIT,frame(1000,false,false));
        assertEquals(WAIT,frame(1100,true,false));
        assertEquals(WAIT,frame(1350,true,false));
        assertEquals(WAIT,frame(4000,true,false));
        assertEquals(WAIT,frame(4100,true,true));
        assertEquals(READY,frame(4350,true,true));
    }
    @Test public void StaleAndFutureCameraFramesCannotAuthorizeMotion() {
        assertEquals(WAIT,guard.update(2000_000_000L,1000_000_000L,true,true));
        assertEquals(WAIT,guard.update(2050_000_000L,2100_000_000L,true,true));
        assertEquals(INVALID,guard.update(3500_000_000L,1000_000_000L,true,true));
    }
}
