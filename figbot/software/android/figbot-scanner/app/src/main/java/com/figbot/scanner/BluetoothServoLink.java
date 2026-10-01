package com.figbot.scanner;

import android.annotation.SuppressLint;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.os.SystemClock;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/** Foreground-only RFCOMM SPP. No auto-connect/rearm and no raw command UI. */
public final class BluetoothServoLink {
    public record State(boolean connected,boolean ready,int enabled,int active,int[] angles,boolean[] acknowledged,String message) {}
    public interface Listener {void update(State state);}
    private final Listener listener;
    private final ScheduledExecutorService io=Executors.newSingleThreadScheduledExecutor();
    private final ScheduledExecutorService timeouts=Executors.newSingleThreadScheduledExecutor();
    private final ServoProtocol protocol=new ServoProtocol();
    private final MotionQueue queue=new MotionQueue();
    private volatile BluetoothSocket socket;
    private volatile boolean connected, shutdown;
    private boolean sessionPrepared;
    private long lastRx,lastPing,lastSend,connectAt;
    private final StringBuilder input=new StringBuilder();
    private String message="HC-05 bağlı değil";
    public BluetoothServoLink(Listener listener) {
        this.listener=listener;
        io.scheduleWithFixedDelay(this::tick,0,25,TimeUnit.MILLISECONDS);
    }
    @SuppressLint("MissingPermission") // Activity obtains BLUETOOTH_CONNECT before invocation.
    public void connect(BluetoothDevice device) {
        if(socket!=null || shutdown)return;
        try {
            BluetoothSocket candidate=device.createRfcommSocketToServiceRecord(UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"));
            socket=candidate;
            io.execute(()->{message="HC-05 bağlantısı kuruluyor…";publish();});
            new Thread(()->{
                try {
                    candidate.connect();
                    io.execute(()->{
                        if(shutdown || socket!=candidate) {close(candidate);return;}
                        protocol.reset();queue.clear();input.setLength(0);sessionPrepared=false;
                        connectAt=lastRx=SystemClock.elapsedRealtime();lastPing=lastSend=0;connected=true;
                        try {write("X\nH\n");message="Bluetooth açık; UNO V5 yanıtı bekleniyor…";} catch(IOException e){fail("UART bağlantısı kurulamadı.");}
                    });
                } catch(Exception e) {
                    if(!shutdown)io.execute(()->{if(socket==candidate)fail("HC-05 bağlanamadı. Eşleştirme ve güç bağlantısını kontrol et.");});
                }
            },"hc05-connect").start();
            io.schedule(()->{if(socket==candidate&&!connected)fail("HC-05 bağlantı zaman aşımı.");},15,TimeUnit.SECONDS);
        } catch(Exception e) {io.execute(()->{message="Bluetooth izni veya eşleştirme eksik.";publish();});}
    }
    public void arm(int ch,boolean on) {if(connected)queue.arm(ch,on);}
    public void move(int ch,int angle,int speed,boolean wide) {if(connected)queue.move(ch,angle,speed,wide);}
    public void move(int ch,int angle,int speed,boolean wide,int pairMin) {if(connected)queue.move(ch,angle,speed,wide,pairMin);}
    public void stop() {queue.stop();}
    public void disconnect() {
        queue.stop();
        io.execute(()->{try{if(connected)write("X\n");}catch(IOException ignored){} fail("Bağlantı kesildi; kolu destekle.");});
        // Closing also cancels a blocked connect/write. Board watchdog is fallback.
        BluetoothSocket old=socket;
        timeouts.schedule(()->close(old),100,TimeUnit.MILLISECONDS);
    }
    public void shutdown() {
        shutdown=true;queue.stop();
        // Do not keep a heartbeat alive after leaving the foreground screen.
        BluetoothSocket old=socket;
        io.execute(()->{try{if(connected)write("X\n");}catch(Exception ignored){}fail("Motor ekranı kapandı; PWM kapanması fiziksel tutuş garantisi değildir.");});
        timeouts.schedule(()->{close(old);io.shutdownNow();timeouts.shutdown();},100,TimeUnit.MILLISECONDS);
    }
    private static void close(BluetoothSocket s) {if(s!=null)try{s.close();}catch(IOException ignored){}}
    private void write(String s) throws IOException {
        BluetoothSocket current=socket;if(current==null)throw new IOException("closed");
        java.util.concurrent.ScheduledFuture<?> deadline=timeouts.schedule(()->close(current),750,TimeUnit.MILLISECONDS);
        try {current.getOutputStream().write(s.getBytes(StandardCharsets.US_ASCII));}
        finally {deadline.cancel(false);}
    }
    private void fail(String reason) {
        close(socket);socket=null;connected=false;protocol.reset();queue.clear();input.setLength(0);message=reason;publish();
    }
    private void tick() {
        if(!connected||shutdown)return;
        try {
            long now=SystemClock.elapsedRealtime();
            int n=Math.min(socket.getInputStream().available(),512);
            for(int i=0;i<n;i++) {
                int c=socket.getInputStream().read();if(c<0)throw new IOException("EOF");
                if(c=='\n') {if(protocol.receive(input.toString().trim()))lastRx=now;input.setLength(0);}
                else if(c!='\r') {input.append((char)c);if(input.length()>128)throw new IOException("Oversize reply");}
            }
            if((protocol.ready&&now-lastRx>1200)||(!protocol.ready&&now-connectAt>6000))throw new IOException("UNO yanıtı kesildi");
            if(protocol.ready&&!sessionPrepared){queue.prepareSession();sessionPrepared=true;}
            if(queue.takeStop()) {write("X\n");protocol.enabled=protocol.active=0;}
            if(now-lastPing>=300) {write("H\n");lastPing=now;}
            // 9600baud UART: limit/coalesce slider messages; never flood HC-05.
            if(protocol.ready&&now-lastSend>=100) {
                MotionQueue.Command cmd=queue.next();
                if(cmd!=null) {
                    write(cmd.angle()==null?protocol.arm(cmd.channel(),cmd.enable()):protocol.position(cmd.channel(),cmd.angle(),cmd.speed(),cmd.wide(),cmd.pairMin()));
                    lastSend=now;
                }
            }
            message=protocol.ready?"HC-05 · UNO V5 · PCA9685 hazır":"Bluetooth açık; UNO yanıtı bekleniyor…";
            publish();
        } catch(Exception e) {
            try{write("X\n");}catch(Exception ignored){}
            fail("Durduruldu: "+e.getMessage()+". Kolu destekle; servo gücü kesilmedi.");
        }
    }
    private void publish() {listener.update(new State(connected,protocol.ready,protocol.enabled,protocol.active,protocol.angle.clone(),protocol.acknowledged.clone(),message));}
}
