package com.figbot.scanner.vision;
import java.nio.ByteBuffer;
import org.junit.Test;
import static org.junit.Assert.*;
public class TeachingCameraServerTest {
    @Test public void copiesPaddedAndInterleavedPlanesWithoutChangingBufferPositions(){
        ByteBuffer y=ByteBuffer.wrap(new byte[]{99,1,2,3,4,88,5,6,7,8});y.position(1);
        ByteBuffer u=ByteBuffer.wrap(new byte[]{11,88,12}),v=ByteBuffer.wrap(new byte[]{21,88,22});
        byte[] result=TeachingCameraServer.pack(4,2,y,5,1,u,4,2,v,4,2);
        assertArrayEquals(new byte[]{1,2,3,4,5,6,7,8,21,11,22,12},result);
        assertEquals(1,y.position());assertEquals(0,u.position());
    }
    @Test public void incompletePlanesAndOddDimensionsCannotBecomeFrames(){
        ByteBuffer b=ByteBuffer.wrap(new byte[]{1});
        assertThrows(IllegalArgumentException.class,()->TeachingCameraServer.pack(4,2,b,4,1,b,2,1,b,2,1));
        assertThrows(IllegalArgumentException.class,()->TeachingCameraServer.pack(3,2,b,4,1,b,2,1,b,2,1));
    }
}
