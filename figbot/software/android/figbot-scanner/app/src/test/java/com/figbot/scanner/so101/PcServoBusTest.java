package com.figbot.scanner.so101;

import java.net.*;
import java.io.*;
import java.util.concurrent.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class PcServoBusTest {
    @Test public void coldSerialOpenGetsReadOnlyGraceButTravelTimeoutStaysShort() throws Exception {
        ExecutorService worker=Executors.newSingleThreadExecutor();
        try(ServerSocket server=new ServerSocket(0,1,InetAddress.getLoopbackAddress())) {
            Future<?> peer=worker.submit(()->{
                try(Socket s=server.accept()) {
                    byte[] first=s.getInputStream().readNBytes(8);
                    assertArrayEquals(St3215Protocol.packet(1,2,new byte[]{3,2}),first);
                    Thread.sleep(300);
                    s.getOutputStream().write(St3215Protocol.packet(1,0,new byte[]{9,3}));
                    byte[] second=s.getInputStream().readNBytes(8);
                    assertArrayEquals(St3215Protocol.packet(2,2,new byte[]{3,2}),second);
                    Thread.sleep(400); // normal read must time out, not inherit the warm-up grace
                } catch(Exception e){throw new RuntimeException(e);}
            });
            try(ServoBus bus=PcServoBus.open("127.0.0.1",server.getLocalPort())) {
                assertThrows(IOException.class,()->bus.read(2,3,2));
            }
            peer.get(3,TimeUnit.SECONDS);
        } finally {worker.shutdownNow();}
    }
}
