package com.figbot.scanner.vision;

import android.graphics.ImageFormat;
import android.graphics.Rect;
import android.graphics.YuvImage;
import android.media.Image;
import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;

/** Explicit opt-in, loopback-only raw camera export. No robot/motor API. */
public final class TeachingCameraServer implements AutoCloseable {
    private record Frame(byte[] jpeg,long captured,int generation,int width,int height,String intrinsics) {}
    private final ServerSocket server;
    private volatile Frame latest;
    private volatile boolean closed;
    public TeachingCameraServer() throws IOException {
        server=new ServerSocket();server.bind(new InetSocketAddress("127.0.0.1",8874));
        Thread worker=new Thread(this::serve,"teaching-camera-export");worker.setDaemon(true);worker.start();
    }
    public void clear(){latest=null;}
    public void offer(Image image,long captured,int generation,float[] focal,float[] principal){
        if(closed)return;
        Image.Plane[] planes=image.getPlanes();int w=image.getWidth(),h=image.getHeight();
        byte[] nv21=pack(w,h,planes[0].getBuffer(),planes[0].getRowStride(),planes[0].getPixelStride(),
                planes[1].getBuffer(),planes[1].getRowStride(),planes[1].getPixelStride(),
                planes[2].getBuffer(),planes[2].getRowStride(),planes[2].getPixelStride());
        ByteArrayOutputStream output=new ByteArrayOutputStream();
        if(!new YuvImage(nv21,ImageFormat.NV21,w,h,null).compressToJpeg(new Rect(0,0,w,h),90,output))
            throw new IllegalStateException("Teaching JPEG encode failed");
        latest=new Frame(output.toByteArray(),captured,generation,w,h,
                focal[0]+","+focal[1]+","+principal[0]+","+principal[1]);
    }
    static byte[] pack(int w,int h,ByteBuffer y,int yr,int yp,ByteBuffer u,int ur,int up,ByteBuffer v,int vr,int vp){
        if(w<=0||h<=0||w%2!=0||h%2!=0||(long)w*h>8_000_000)throw new IllegalArgumentException("YUV dimensions");
        byte[] result=new byte[w*h*3/2];int n=0;
        for(int row=0;row<h;row++)for(int col=0;col<w;col++)result[n++]=at(y,row,col,yr,yp);
        for(int row=0;row<h/2;row++)for(int col=0;col<w/2;col++){
            result[n++]=at(v,row,col,vr,vp);result[n++]=at(u,row,col,ur,up);
        }
        return result;
    }
    private static byte at(ByteBuffer buffer,int row,int col,int stride,int pixel){
        if(stride<=0||pixel<=0)throw new IllegalArgumentException("YUV stride");
        long index=(long)buffer.position()+(long)row*stride+(long)col*pixel;
        if(index>=buffer.limit())throw new IllegalArgumentException("Incomplete YUV plane");
        return buffer.get((int)index);
    }
    private void serve(){
        while(!closed)try(Socket client=server.accept()){
            client.setSoTimeout(1000);
            BufferedReader input=new BufferedReader(new InputStreamReader(client.getInputStream(),StandardCharsets.US_ASCII));
            String request=input.readLine();Frame f=latest;long now=System.nanoTime();
            boolean valid="GET /frame HTTP/1.1".equals(request)||"GET /frame HTTP/1.0".equals(request);
            boolean fresh=f!=null&&now>=f.captured&&now-f.captured<500_000_000L;
            byte[] body=valid&&fresh?f.jpeg:new byte[0];
            String headers="HTTP/1.1 "+(!valid?"404 Not Found":fresh?"200 OK":"503 Camera Unavailable")+"\r\n"
                    +"Content-Type: image/jpeg\r\nContent-Length: "+body.length+"\r\nCache-Control: no-store\r\nConnection: close\r\n";
            if(valid&&fresh)headers+="X-Capture-Ns: "+f.captured+"\r\nX-Age-Ns: "+(now-f.captured)
                    +"\r\nX-Generation: "+f.generation+"\r\nX-Width: "+f.width+"\r\nX-Height: "+f.height
                    +"\r\nX-Intrinsics: "+f.intrinsics+"\r\n";
            OutputStream out=client.getOutputStream();out.write((headers+"\r\n").getBytes(StandardCharsets.US_ASCII));out.write(body);out.flush();
        }catch(IOException ignored){/* Closing the activity closes accept; broken clients do not stop camera capture. */}
    }
    @Override public void close(){closed=true;latest=null;try{server.close();}catch(IOException ignored){}}
}
