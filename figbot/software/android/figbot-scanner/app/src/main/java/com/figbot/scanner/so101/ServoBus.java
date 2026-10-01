package com.figbot.scanner.so101;

import java.io.Closeable;
import java.io.IOException;
import java.util.Map;

/** One owned ST3215 bus; callers serialize their trajectory and feedback work. */
public interface ServoBus extends Closeable {
    byte[] read(int id, int address, int length) throws IOException;
    void write(int id, int address, byte[] data) throws IOException;
    void syncPositions(Map<Integer, Integer> positions) throws IOException;
    /** Each value is {position, speed, acceleration}, using finite nonzero limits. */
    void syncProfiles(Map<Integer, int[]> profiles) throws IOException;
    @Override void close() throws IOException;
}
