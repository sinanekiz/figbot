package com.figbot.scanner.vision;
import org.junit.Test;
import static org.junit.Assert.*;
public class FixedMountReferenceTest {
    @Test public void callbackAfterMotorTickTimestampDoesNotInvalidateLiveReference(){
        java.util.concurrent.atomic.AtomicLong clock=new java.util.concurrent.atomic.AtomicLong(1_000_000_000L);
        FixedMountReference live=new FixedMountReference(clock::get);
        float[] q={1,0,0,0};
        live.rotation(q,clock.get());live.acceleration(0,0,0,clock.get());live.armNow();
        long motorTickStarted=clock.get();
        clock.addAndGet(2_000_000L);
        live.rotation(q,clock.get());live.acceleration(0,0,0,clock.get());
        assertFalse(live.valid(motorTickStarted)); // Reproduces the stale-clock caller bug.
        assertTrue(live.readyNow());assertTrue(live.validNow());live.armNow();
        clock.addAndGet(600_000_000L);
        assertFalse(live.validNow()); // Actual missing samples still stop motion.
    }
    private final FixedMountReference ref=new FixedMountReference();
    private void sample(long ms,float angle,float acceleration){
        ref.rotation(new float[]{(float)Math.cos(angle/2),0,0,(float)Math.sin(angle/2)},ms*1_000_000L);
        ref.acceleration(acceleration,0,0,ms*1_000_000L);
    }
    @Test public void fixedMountRemainsValidWithoutArWorldInput(){
        sample(1000,0,0);ref.arm(1000_000_000L);
        for(int i=1010;i<60000;i+=20){sample(i,.001f,.02f);assertTrue(ref.valid(i*1_000_000L));}
    }
    @Test public void RotationLatchesEvenAfterReturn(){
        sample(1000,0,0);ref.arm(1000_000_000L);
        sample(1100,.04f,0);assertFalse(ref.valid(1100_000_000L));
        sample(1200,0,0);assertFalse(ref.valid(1200_000_000L));
        ref.arm(1200_000_000L);assertTrue(ref.valid(1200_000_000L));
    }
    @Test public void accelerationDisturbanceAndSensorLossFailClosed(){
        sample(1000,0,0);ref.arm(1000_000_000L);
        sample(1100,0,1);sample(1300,0,1);sample(1400,0,0);
        assertFalse(ref.valid(1400_000_000L));ref.arm(1400_000_000L);
        assertFalse(ref.valid(2000_000_000L));ref.clear();assertFalse(ref.ready(2000_000_000L));
    }
    @Test public void missingSensorsCannotArm(){assertThrows(IllegalStateException.class,()->ref.arm(1000_000_000L));}
    @Test public void rigMustSettleBeforeMarkerRevalidation(){
        for(int i=0;i<10;i++){sample(1000+i*100,i*.01f,0);assertFalse(ref.settled((1000+i*100)*1_000_000L));}
        for(int i=0;i<7;i++)sample(2000+i*100,.09f,0);
        assertTrue(ref.settled(2600_000_000L));
        sample(2700,.09f,1);assertFalse(ref.settled(2700_000_000L));
    }
    @Test public void sensorGapCannotCountAsSettledTime(){
        sample(1000,0,0);sample(3000,0,0);
        assertFalse(ref.settled(3000_000_000L));
    }
}
