package com.figbot.scanner.so101;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.net.SocketTimeoutException;
import java.util.Arrays;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

/** STS little-endian packets; no connect-time writes, retries, or torque enabling. */
public final class St3215Protocol implements ServoBus {
    public interface ByteIo extends AutoCloseable {
        /** Return 0 on timeout; timeoutMs must be positive and finite. */
        int read(byte[] data, int offset, int length, int timeoutMs) throws IOException;
        /** Write the entire packet, or throw. An exception is never retried. */
        void write(byte[] data) throws IOException;
        @Override void close() throws IOException;
    }

    public record FeedbackState(int torque, int position, int speed, double voltage,
                                int temperature, int currentRaw, boolean moving) {}

    private static final int BROADCAST = 254;
    private static final int MAX_RESPONSE_LENGTH = 64;
    private final ByteIo io;
    private final int timeoutMs;
    private volatile boolean closed;

    public St3215Protocol(ByteIo io) { this(io, 180); }
    public St3215Protocol(ByteIo io, int timeoutMs) {
        this.io = Objects.requireNonNull(io, "Byte I/O required");
        if (timeoutMs < 1 || timeoutMs > 1000) throw new IllegalArgumentException("Timeout must be 1..1000 ms");
        this.timeoutMs = timeoutMs;
    }

    @Override public synchronized byte[] read(int id, int address, int length) throws IOException {
        requireId(id);
        if (address < 0 || address > 255 || length < 1 || length > 62 || address + length > 256)
            throw new IllegalArgumentException("Invalid register read");
        return transact(id, 2, new byte[]{(byte) address, (byte) length}, length);
    }

    @Override public synchronized void write(int id, int address, byte[] data) throws IOException {
        requireId(id);
        if (data == null || data.length < 1 || data.length > 61 || address < 0 || address + data.length > 256)
            throw new IllegalArgumentException("Invalid register write");
        byte[] parameters = new byte[data.length + 1];
        parameters[0] = (byte) address;
        System.arraycopy(data, 0, parameters, 1, data.length);
        transact(id, 3, parameters, 0);
    }

    @Override public synchronized void syncPositions(Map<Integer, Integer> positions) throws IOException {
        requireGroup(positions);
        byte[] data = new byte[2 + positions.size() * 3];
        data[0] = 42; data[1] = 2;
        int offset = 2;
        for (Map.Entry<Integer, Integer> entry : new TreeMap<>(positions).entrySet()) {
            Integer position = entry.getValue();
            if (position == null || position < 0 || position > 4095) throw new IllegalArgumentException("Position must be 0..4095");
            data[offset++] = entry.getKey().byteValue();
            data[offset++] = (byte) (int) position;
            data[offset++] = (byte) (position >> 8);
        }
        // RAM Goal_Position only: factory offsets and finite profiles stay intact.
        transact(BROADCAST, 0x83, data, 0);
    }

    @Override public synchronized void syncProfiles(Map<Integer, int[]> profiles) throws IOException {
        requireGroup(profiles);
        byte[] data = new byte[2 + profiles.size() * 8];
        data[0] = 41; data[1] = 7;
        int offset = 2;
        for (Map.Entry<Integer, int[]> entry : new TreeMap<>(profiles).entrySet()) {
            int[] p = entry.getValue();
            if (p == null || p.length != 3 || p[0] < 0 || p[0] > 4095 || p[1] < 1 || p[1] > 3400 || p[2] < 1 || p[2] > 150)
                throw new IllegalArgumentException("Invalid finite ST3215 profile");
            data[offset++] = entry.getKey().byteValue();
            data[offset++] = (byte) p[2];
            data[offset++] = (byte) p[0]; data[offset++] = (byte) (p[0] >> 8);
            data[offset++] = 0; data[offset++] = 0;
            data[offset++] = (byte) p[1]; data[offset++] = (byte) (p[1] >> 8);
        }
        transact(BROADCAST, 0x83, data, 0);
    }

    public synchronized FeedbackState feedbackState(int id) throws IOException {
        return readFeedback(this, id);
    }

    public static FeedbackState readFeedback(ServoBus bus, int id) throws IOException {
        return decodeFeedbackState(bus.read(id, 40, 31));
    }

    public static FeedbackState decodeFeedbackState(byte[] data) {
        if (data == null || data.length != 31) throw new IllegalArgumentException("Feedback requires registers 40..70");
        return new FeedbackState(data[0] & 255, signedMagnitude(word(data, 16)),
                signedMagnitude(word(data, 18)), (data[22] & 255) / 10.0,
                data[23] & 255, signedMagnitude(word(data, 29)), data[26] != 0);
    }

    public static int signedMagnitude(int word) {
        if (word < 0 || word > 65535) throw new IllegalArgumentException("Unsigned word required");
        return (word & 0x8000) != 0 ? -(word & 0x7fff) : word;
    }

    public static int word(byte[] data, int offset) {
        if (data == null || offset < 0 || offset + 1 >= data.length) throw new IllegalArgumentException("Two little-endian bytes required");
        return (data[offset] & 255) | ((data[offset + 1] & 255) << 8);
    }

    public static byte[] leWord(int value) {
        if (value < 0 || value > 65535) throw new IllegalArgumentException("Unsigned word required");
        return new byte[]{(byte) value, (byte) (value >> 8)};
    }

    private static void requireId(int id) {
        if (id < 1 || id > 253) throw new IllegalArgumentException("Unicast ID must be 1..253");
    }

    private static void requireGroup(Map<Integer, ?> group) {
        if (group == null || group.isEmpty() || group.size() > 6) throw new IllegalArgumentException("1..6 motor targets required");
        for (Integer id : group.keySet())
            if (id == null || id < 1 || id > 6) throw new IllegalArgumentException("SO101 group IDs must be 1..6");
    }

    static byte[] packet(int id, int instruction, byte[] data) {
        byte[] result = new byte[data.length + 6];
        result[0] = (byte) 255; result[1] = (byte) 255;
        result[2] = (byte) id; result[3] = (byte) (data.length + 2); result[4] = (byte) instruction;
        System.arraycopy(data, 0, result, 5, data.length);
        int sum = 0;
        for (int k = 2; k < result.length - 1; k++) sum += result[k] & 255;
        result[result.length - 1] = (byte) ~sum;
        return result;
    }

    private void requireOpen() throws IOException {
        if (closed) throw new IOException("ST3215 bus is closed");
        if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("Servo worker interrupted");
    }

    /** A delayed ACK from the previous exchange must not authorize this write. */
    private void discardPendingInput() throws IOException {
        byte[] discard = new byte[128];
        long deadline = System.nanoTime() + 20_000_000L;
        int total = 0;
        while (System.nanoTime() < deadline && total <= 1024) {
            requireOpen();
            int n = io.read(discard, 0, discard.length, 1);
            if (n < 0 || n > discard.length) throw new IOException("Invalid USB read count");
            if (n == 0) return;
            total += n;
        }
        throw new IOException("Servo input did not become idle; command not sent");
    }

    private byte[] transact(int id, int instruction, byte[] data, int responseSize) throws IOException {
        requireOpen();
        discardPendingInput();
        byte[] command = packet(id, instruction, data);
        io.write(command); // Never replay an ambiguous write.
        if (id == BROADCAST) return new byte[0]; // Broadcasts have no acknowledgement.
        long deadline = System.nanoTime() + timeoutMs * 1_000_000L;
        byte[] buffer = new byte[256];
        int count = 0;
        while (true) {
            requireOpen();
            long remaining = deadline - System.nanoTime();
            if (remaining <= 0) throw new SocketTimeoutException("ST3215 ID " + id + " response timed out");
            int wait = (int) Math.max(1, (remaining + 999_999L) / 1_000_000L);
            int received = io.read(buffer, count, buffer.length - count, wait);
            if (System.nanoTime() > deadline) throw new SocketTimeoutException("ST3215 ID " + id + " response arrived after deadline");
            if (received < 0 || received > buffer.length - count) throw new IOException("Invalid USB read count");
            count += received;
            while (count >= 4) {
                if ((buffer[0] & 255) != 255 || (buffer[1] & 255) != 255 ||
                        (buffer[3] & 255) < 2 || (buffer[3] & 255) > MAX_RESPONSE_LENGTH) {
                    System.arraycopy(buffer, 1, buffer, 0, --count);
                    continue;
                }
                int length = (buffer[3] & 255) + 4;
                if (count < length) break;
                int checksum = 0;
                for (int k = 2; k < length; k++) checksum += buffer[k] & 255;
                if ((checksum & 255) != 255) {
                    System.arraycopy(buffer, 1, buffer, 0, --count);
                    continue;
                }
                byte[] frame = Arrays.copyOf(buffer, length);
                System.arraycopy(buffer, length, buffer, 0, count -= length);
                if ((frame[2] & 255) != id || Arrays.equals(frame, command)) continue;
                if ((frame[4] & 255) != 0) throw new IOException("ST3215 ID " + id + " status error 0x" + Integer.toHexString(frame[4] & 255));
                if (length - 6 != responseSize) continue;
                return Arrays.copyOfRange(frame, 5, length - 1);
            }
        }
    }

    /** Closing can interrupt a USB read; it deliberately does not change torque. */
    @Override public void close() throws IOException {
        if (!closed) { closed = true; io.close(); }
    }
}
