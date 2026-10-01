package com.figbot.scanner.vision;

import java.nio.ByteBuffer;
import java.util.Arrays;
import org.junit.Test;
import static org.junit.Assert.*;

public class MarkerDiagnosticsTest {
    @Test public void paddedRowsAndPixelStrideStartAtBufferPositionWithoutChangingInput(){
        byte[] bytes=new byte[20];Arrays.fill(bytes,(byte)99);
        int[] indices={3,5,7,11,13,15};int[] values={0,1,127,128,200,255};
        for(int index=0;index<indices.length;index++)bytes[indices[index]]=(byte)values[index];
        byte[] before=bytes.clone();ByteBuffer buffer=ByteBuffer.wrap(bytes);
        buffer.position(3);buffer.limit(16);buffer.mark();
        assertArrayEquals(new int[]{0xff000000,0xff010101,0xff7f7f7f,0xff808080,0xffc8c8c8,0xffffffff},
                MarkerDiagnostics.luminanceArgb(buffer,3,2,8,2));
        assertEquals(3,buffer.position());assertEquals(16,buffer.limit());
        buffer.reset();assertEquals(3,buffer.position());assertArrayEquals(before,bytes);
    }

    @Test public void tightlyPackedReadOnlyBufferUsesUnsignedLuminance(){
        ByteBuffer buffer=ByteBuffer.wrap(new byte[]{0,64,(byte)128,(byte)255}).asReadOnlyBuffer();
        assertArrayEquals(new int[]{0xff000000,0xff404040,0xff808080,0xffffffff},
                MarkerDiagnostics.luminanceArgb(buffer,2,2,2,1));
        assertEquals(0,buffer.position());assertEquals(4,buffer.limit());
    }

    @Test public void truncatedLastRowIsRejectedUsingLimitRatherThanCapacity(){
        ByteBuffer buffer=ByteBuffer.allocate(20);buffer.position(3);buffer.limit(15);
        assertThrows(IllegalArgumentException.class,()->MarkerDiagnostics.luminanceArgb(buffer,3,2,8,2));
        assertEquals(3,buffer.position());assertEquals(15,buffer.limit());
    }

    @Test public void invalidDimensionsCannotReadOrAllocateThePlane(){
        ByteBuffer buffer=ByteBuffer.allocate(4);
        assertThrows(IllegalArgumentException.class,()->MarkerDiagnostics.luminanceArgb(null,1,1,1,1));
        assertThrows(IllegalArgumentException.class,()->MarkerDiagnostics.luminanceArgb(buffer,0,1,1,1));
        assertThrows(IllegalArgumentException.class,()->MarkerDiagnostics.luminanceArgb(buffer,1,-1,1,1));
        assertThrows(IllegalArgumentException.class,()->MarkerDiagnostics.luminanceArgb(buffer,1,1,0,1));
        assertThrows(IllegalArgumentException.class,()->MarkerDiagnostics.luminanceArgb(buffer,1,1,1,0));
        assertThrows(IllegalArgumentException.class,()->MarkerDiagnostics.luminanceArgb(buffer,Integer.MAX_VALUE,2,1,1));
        assertEquals(0,buffer.position());assertEquals(4,buffer.limit());
    }
}
