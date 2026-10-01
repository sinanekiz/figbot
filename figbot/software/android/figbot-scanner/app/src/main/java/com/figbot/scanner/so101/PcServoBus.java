package com.figbot.scanner.so101;

import java.io.*;
import java.net.*;

/** Same checked ST3215 protocol, through adb reverse and the single PC serial owner. */
public final class PcServoBus {
    public static final int PORT = 8873;
    private PcServoBus() {}
    public static ServoBus open() throws IOException {
        return open("127.0.0.1", PORT);
    }
    static ServoBus open(String host, int port) throws IOException {
        Socket socket = new Socket();
        try {
            socket.connect(new InetSocketAddress(host, port), 1500);
            socket.setTcpNoDelay(true);
            SocketIo io = new SocketIo(socket);
            // PC opens the serial device after accept. Warm up with one read-only
            // identity request; keep normal motion transactions at 180 ms afterward.
            new St3215Protocol(io, 1000).read(1, 3, 2);
            return new St3215Protocol(io);
        } catch (IOException e) { socket.close(); throw e; }
    }
    static final class SocketIo implements St3215Protocol.ByteIo {
        private final Socket socket;
        private final InputStream input;
        private final OutputStream output;
        SocketIo(Socket socket) throws IOException {
            this.socket=socket; input=socket.getInputStream(); output=socket.getOutputStream();
        }
        public int read(byte[] data,int offset,int length,int timeoutMs) throws IOException {
            socket.setSoTimeout(timeoutMs);
            try { int n=input.read(data,offset,length); if(n<0)throw new EOFException("PC köprüsü kapandı."); return n; }
            catch(SocketTimeoutException e){return 0;}
        }
        public void write(byte[] data) throws IOException {output.write(data);output.flush();}
        public void close() throws IOException {socket.close();}
    }
}
