package com.figbot.scanner.so101;
import org.junit.Test;
import static org.junit.Assert.*;
public class AttemptedTargetsTest {
    @Test public void failedAttemptStillSuppressesSameLocationAndJitter(){
        var memory=new AttemptedTargets();memory.add(new double[]{200,-140,10});
        assertTrue(memory.contains(new double[]{205,-145,10}));
        assertFalse(memory.contains(new double[]{245,-69,10}));
        var restored=new AttemptedTargets();for(var p:memory.snapshot())restored.add(p);
        assertTrue(restored.contains(new double[]{200,-140,10}));
        restored.clear();assertFalse(restored.contains(new double[]{200,-140,10}));
    }
    @Test public void snapshotsCannotModifyMemory(){var m=new AttemptedTargets();m.add(new double[]{1,2});m.snapshot().get(0)[0]=1000;assertTrue(m.contains(new double[]{1,2}));}
}
