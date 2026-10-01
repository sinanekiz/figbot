package com.figbot.scanner.vision;
import org.junit.Test;
import static org.junit.Assert.*;
public class DisplayMemoryTest {
    @Test public void missesDoNotBlinkButCannotRefreshStaleObservations(){
        DisplayMemory<String> m=new DisplayMemory<>();m.offer("fig",1_000_000_000L,1);
        m.offer(null,1_200_000_000L,1);assertEquals("fig",m.get(1_300_000_000L,1));
        assertEquals("fig",m.get(1_700_000_000L,1));assertNull(m.get(1_800_000_001L,1));
    }
    @Test public void oldSessionsAndOutOfOrderFramesAreNotShown(){
        DisplayMemory<String> m=new DisplayMemory<>();m.offer("new",1000,1);m.offer("old",999,1);
        assertEquals("new",m.get(1001,1));assertNull(m.get(1001,2));
    }
}
