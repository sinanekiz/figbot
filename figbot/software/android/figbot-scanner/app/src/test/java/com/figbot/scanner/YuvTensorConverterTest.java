package com.figbot.scanner;
import java.nio.*;
import org.junit.Test;
import static org.junit.Assert.*;
public class YuvTensorConverterTest {
    @Test public void planarColorPaddingStrideAndOffsetArePreserved(){
        ByteBuffer y=ByteBuffer.wrap(new byte[]{99,10,20,90,90,30,40,90,90});y.position(1);
        ByteBuffer u=ByteBuffer.wrap(new byte[]{88,(byte)148,0});u.position(1);
        ByteBuffer v=ByteBuffer.wrap(new byte[]{77,(byte)138,0});v.position(1);
        FloatBuffer out=FloatBuffer.allocate(12);
        new YuvTensorConverter(2).convert(2,2,new ByteBuffer[]{y,u,v},new int[]{4,2,2},new int[]{1,2,2},out);
        for(int i=0;i<4;i++){
            float yy=(i+1)*10;
            assertEquals((yy+14.02f)/255f,out.get(i),1e-6);
            assertEquals(Math.max(0,yy-.344136f*20-.714136f*10)/255f,out.get(4+i),1e-6);
            assertEquals((yy+35.44f)/255f,out.get(8+i),1e-6);
        }
        assertEquals(1,y.position());assertEquals(1,u.position());
    }
    @Test public void nonSquareInputIsLetterboxedAndConverterCanBeReused(){
        YuvTensorConverter converter=new YuvTensorConverter(4);FloatBuffer out=FloatBuffer.allocate(48);
        ByteBuffer[] planes={ByteBuffer.wrap(new byte[]{10,20,30,40,50,60,70,80}),ByteBuffer.wrap(new byte[]{(byte)128,(byte)128}),ByteBuffer.wrap(new byte[]{(byte)128,(byte)128})};
        for(int repeat=0;repeat<2;repeat++){
            converter.convert(4,2,planes,new int[]{4,2,2},new int[]{1,1,1},out);
            for(int c=0;c<3;c++){
                assertEquals(114f/255,out.get(c*16),0);
                assertEquals(10f/255,out.get(c*16+4),0);
                assertEquals(80f/255,out.get(c*16+11),0);
                assertEquals(114f/255,out.get(c*16+15),0);
            }
        }
    }
}
