package com.figbot.scanner.so101;

import org.junit.Test;
import static org.junit.Assert.*;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.net.SocketTimeoutException;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class St3215ProtocolTest {
    static final class Io implements St3215Protocol.ByteIo {
        final ArrayDeque<Byte> input = new ArrayDeque<>();
        final ArrayDeque<byte[]> responses = new ArrayDeque<>();
        final List<byte[]> writes = new ArrayList<>();
        int chunk = 256, closeCount, reads, delayMillis;
        IOException writeFailure;
        void enqueue(byte[] bytes) { for (byte b : bytes) input.add(b); }
        @Override public int read(byte[] out, int offset, int length, int timeoutMs) {
            assertTrue(timeoutMs > 0 && timeoutMs <= 1000); reads++;
            if(delayMillis>0 && !input.isEmpty() && !writes.isEmpty())try{Thread.sleep(delayMillis);}catch(InterruptedException e){Thread.currentThread().interrupt();}
            int n = Math.min(Math.min(input.size(), length), chunk);
            for (int k=0; k<n; k++) out[offset+k] = input.remove();
            return n;
        }
        @Override public void write(byte[] data) throws IOException {
            writes.add(data.clone());
            if (writeFailure != null) throw writeFailure;
            if (!responses.isEmpty()) enqueue(responses.remove());
        }
        @Override public void close() { closeCount++; }
    }
    private static byte[] reply(int id, int status, byte... payload) { return St3215Protocol.packet(id,status,payload); }
    private static byte[] concat(byte[]... chunks) {
        byte[] result = new byte[Arrays.stream(chunks).mapToInt(a->a.length).sum()]; int p=0;
        for (byte[] chunk:chunks) {System.arraycopy(chunk,0,result,p,chunk.length);p+=chunk.length;}
        return result;
    }
    @Test public void constructorsAndCloseNeverSendMotorCommands() throws Exception {
        Io io=new Io();St3215Protocol bus=new St3215Protocol(io);assertTrue(io.writes.isEmpty());
        bus.close();bus.close();assertEquals(1,io.closeCount);assertTrue(io.writes.isEmpty());
        assertThrows(IOException.class,()->bus.read(1,3,2));
    }
    @Test public void littleEndianReadWorksAcrossEveryByteBoundary() throws Exception {
        Io io=new Io();io.chunk=1;io.responses.add(reply(2,0,(byte)9,(byte)3));
        assertArrayEquals(new byte[]{9,3},new St3215Protocol(io).read(2,3,2));
        assertArrayEquals(new byte[]{-1,-1,2,4,2,3,2,(byte)242},io.writes.get(0));
    }
    @Test public void ignoresNoiseChecksumFailureWrongIdWrongLengthAndTransmitEcho() throws Exception {
        Io io=new Io();byte[] bad=reply(2,0,(byte)1,(byte)2);bad[bad.length-1]++;
        byte[] echo=St3215Protocol.packet(2,2,new byte[]{3,2});
        io.responses.add(concat(new byte[]{9,-1,0,-1,-1,2,1},bad,reply(3,0,(byte)5,(byte)6),
                reply(2,0,(byte)7),echo,reply(2,0,(byte)9,(byte)3)));
        assertArrayEquals(new byte[]{9,3},new St3215Protocol(io).read(2,3,2));assertEquals(1,io.writes.size());
    }
    @Test public void staleAckIsDiscardedAndCannotAuthorizeNewWrite() throws Exception {
        Io io=new Io();io.enqueue(reply(1,0));St3215Protocol bus=new St3215Protocol(io,5);
        assertThrows(SocketTimeoutException.class,()->bus.write(1,40,new byte[]{1}));assertEquals(1,io.writes.size());
    }
    @Test public void deviceErrorIsReportedWithoutRetry() {
        Io io=new Io();io.responses.add(reply(2,0x20));St3215Protocol bus=new St3215Protocol(io);
        IOException error=assertThrows(IOException.class,()->bus.write(2,40,new byte[]{1}));
        assertTrue(error.getMessage().contains("0x20"));assertEquals(1,io.writes.size());
    }
    @Test public void writeTimeoutDoesNotReplayPotentiallyAppliedCommand() {
        Io io=new Io();io.writeFailure=new IOException("partial USB write");St3215Protocol bus=new St3215Protocol(io);
        assertThrows(IOException.class,()->bus.syncPositions(Map.of(1,1200)));assertEquals(1,io.writes.size());
    }
    @Test public void missingReplyAndEchoOnlyHaveBoundedTimeout() {
        Io io=new Io();io.responses.add(St3215Protocol.packet(1,2,new byte[]{3,2}));
        long start=System.nanoTime();assertThrows(SocketTimeoutException.class,()->new St3215Protocol(io,5).read(1,3,2));
        assertTrue((System.nanoTime()-start)/1e6 < 500);assertEquals(1,io.writes.size());
    }
    @Test public void replyDeliveredAfterReadDeadlineIsRejected() {
        Io io=new Io();io.delayMillis=12;io.responses.add(reply(1,0,(byte)9,(byte)3));
        assertThrows(SocketTimeoutException.class,()->new St3215Protocol(io,5).read(1,3,2));assertEquals(1,io.writes.size());
    }
    @Test public void positionBroadcastPreservesAllRegistersExceptGoalPosition() throws Exception {
        Io io=new Io();new St3215Protocol(io).syncPositions(Map.of(3,3700,2,1300));
        assertArrayEquals(St3215Protocol.packet(254,0x83,new byte[]{42,2,2,20,5,3,116,14}),io.writes.get(0));
        assertEquals(1,io.reads); // drain only; broadcasts have no ACK.
    }
    @Test public void profileBroadcastHasVendorPositionSpeedAccelerationLayout() throws Exception {
        Io io=new Io();new St3215Protocol(io).syncProfiles(Map.of(2,new int[]{1300,3400,50}));
        assertArrayEquals(St3215Protocol.packet(254,0x83,new byte[]{41,7,2,50,20,5,0,0,72,13}),io.writes.get(0));
    }
    @Test public void validatesEntireGroupBeforeFirstByteIsWritten() {
        Io io=new Io();St3215Protocol bus=new St3215Protocol(io);
        Map<Integer,Integer> invalid=new LinkedHashMap<>();invalid.put(1,1200);invalid.put(6,4096);
        assertThrows(IllegalArgumentException.class,()->bus.syncPositions(invalid));
        assertThrows(IllegalArgumentException.class,()->bus.syncPositions(Map.of(7,1200)));
        assertThrows(IllegalArgumentException.class,()->bus.syncProfiles(Map.of(1,new int[]{1200,0,50})));
        assertThrows(IllegalArgumentException.class,()->bus.syncProfiles(Map.of(1,new int[]{1200,3400,0})));
        assertThrows(IllegalArgumentException.class,()->bus.read(254,3,2));
        assertThrows(IllegalArgumentException.class,()->bus.read(1,250,31));
        assertTrue(io.writes.isEmpty());
    }
    @Test public void feedbackReadsTorqueAndSignedStateInOnePacket() throws Exception {
        byte[] data=new byte[31];data[0]=1;data[16]=4;data[17]=9;data[18]=50;data[19]=(byte)128;
        data[22]=122;data[23]=39;data[26]=1;data[29]=7;data[30]=(byte)128;
        Io io=new Io();io.responses.add(reply(2,0,data));
        St3215Protocol.FeedbackState state=St3215Protocol.readFeedback(new St3215Protocol(io),2);
        assertEquals(1,state.torque());assertEquals(2308,state.position());assertEquals(-50,state.speed());
        assertEquals(12.2,state.voltage(),1e-9);assertEquals(39,state.temperature());assertEquals(-7,state.currentRaw());assertTrue(state.moving());
        assertArrayEquals(St3215Protocol.packet(2,2,new byte[]{40,31}),io.writes.get(0));
    }
    @Test public void interruptionPreventsCommandsAndNoTorqueIsDisabledByClose() {
        Io io=new Io();St3215Protocol bus=new St3215Protocol(io);
        try {Thread.currentThread().interrupt();assertThrows(InterruptedIOException.class,()->bus.syncPositions(Map.of(1,1200)));}
        finally {Thread.interrupted();}
        assertTrue(io.writes.isEmpty());
    }
}
