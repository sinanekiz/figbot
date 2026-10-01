package com.figbot.scanner.so101;

import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbManager;
import com.hoho.android.usbserial.driver.UsbSerialDriver;
import com.hoho.android.usbserial.driver.UsbSerialPort;
import com.hoho.android.usbserial.driver.UsbSerialProber;
import java.io.IOException;
import java.util.Map;

/** Worker-thread USB host adapter. Permission is obtained explicitly by its caller. */
public final class UsbServoBus implements ServoBus {
    public static final int BAUD_RATE = 1_000_000;
    private static final int WRITE_TIMEOUT_MS = 180;
    private final St3215Protocol protocol;

    private UsbServoBus(St3215Protocol protocol) { this.protocol = protocol; }

    public static UsbServoBus open(UsbManager manager, UsbDevice device) throws IOException {
        if (manager == null || device == null) throw new IllegalArgumentException("USB manager and selected device required");
        if (!manager.hasPermission(device)) throw new IOException("Selected USB device has no granted permission");
        // The default 3.11.0 prober uses CDC/ACM interface descriptors (including
        // compliant CH343 devices). Never force an unrelated device to a driver.
        UsbSerialDriver driver = UsbSerialProber.getDefaultProber().probeDevice(device);
        if (driver == null || driver.getPorts().size() != 1) throw new IOException("One supported USB serial port is required");
        UsbDeviceConnection connection = manager.openDevice(device);
        if (connection == null) throw new IOException("USB device could not be opened");
        UsbSerialPort port = driver.getPorts().get(0);
        try {
            port.open(connection);
            port.setParameters(BAUD_RATE, UsbSerialPort.DATABITS_8, UsbSerialPort.STOPBITS_1, UsbSerialPort.PARITY_NONE);
            return new UsbServoBus(new St3215Protocol(new PortIo(port)));
        } catch (IOException | RuntimeException error) {
            try { port.close(); } catch (IOException | RuntimeException ignored) { connection.close(); }
            throw new IOException("USB ST3215 port initialization failed", error);
        }
    }

    private static final class PortIo implements St3215Protocol.ByteIo {
        private final UsbSerialPort port;
        private final byte[] receive = new byte[256];
        PortIo(UsbSerialPort port) { this.port = port; }
        @Override public int read(byte[] data, int offset, int length, int timeoutMs) throws IOException {
            if (timeoutMs <= 0 || offset < 0 || length < 1 || offset + length > data.length || length > receive.length)
                throw new IllegalArgumentException("Finite bounded USB read required");
            int count = port.read(receive, length, timeoutMs);
            if (count < 0 || count > length) throw new IOException("Invalid USB read count");
            System.arraycopy(receive, 0, data, offset, count);
            return count;
        }
        @Override public void write(byte[] data) throws IOException { port.write(data, WRITE_TIMEOUT_MS); }
        @Override public void close() throws IOException { port.close(); }
    }

    @Override public byte[] read(int id, int address, int length) throws IOException { return protocol.read(id, address, length); }
    @Override public void write(int id, int address, byte[] data) throws IOException { protocol.write(id, address, data); }
    @Override public void syncPositions(Map<Integer, Integer> positions) throws IOException { protocol.syncPositions(positions); }
    @Override public void syncProfiles(Map<Integer, int[]> profiles) throws IOException { protocol.syncProfiles(profiles); }
    public St3215Protocol.FeedbackState feedbackState(int id) throws IOException { return protocol.feedbackState(id); }
    @Override public void close() throws IOException { protocol.close(); }
}
