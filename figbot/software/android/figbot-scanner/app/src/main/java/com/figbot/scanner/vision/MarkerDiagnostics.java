package com.figbot.scanner.vision;

import android.graphics.Bitmap;
import android.media.Image;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

/** Optional raw-image evidence, called by the image's existing owner before close().
 * Does not change the image, detector state, calibration, or motion permissions.
 * A JSON file is the completion marker for its identically named PNG.
 */
public final class MarkerDiagnostics {
    private MarkerDiagnostics() {}

    public static void save(File directory,int slot,Image image,ArucoTracker.Observation obs,
                            float[] focal,float[] principal,int[] raw) throws Exception {
        if(directory==null||image==null)throw new IllegalArgumentException("Diagnostic directory and image are required");
        if(!directory.isDirectory()&&!directory.mkdirs()&&!directory.isDirectory())
            throw new IOException("Cannot create marker diagnostic directory");
        int width=image.getWidth(),height=image.getHeight();
        if(width<=0||height<=0||image.getPlanes().length==0)throw new IllegalArgumentException("Image has no luminance plane");
        Image.Plane plane=image.getPlanes()[0];
        int[] pixels=luminanceArgb(plane.getBuffer(),width,height,plane.getRowStride(),plane.getPixelStride());
        JSONObject data=new JSONObject();
        data.put("width",width);data.put("height",height);
        data.put("capturedNs",obs==null?image.getTimestamp():obs.capturedNs());
        data.put("imageTimestampNs",image.getTimestamp());
        data.put("generation",obs==null?JSONObject.NULL:obs.generation());
        data.put("focal",array(focal));data.put("principal",array(principal));
        data.put("corners",obs==null?JSONObject.NULL:array(obs.imageCorners()));
        data.put("cameraR",obs==null?JSONObject.NULL:new JSONArray(obs.cameraMarker().rotation()));
        data.put("cameraT",obs==null?JSONObject.NULL:new JSONArray(obs.cameraMarker().translation()));
        data.put("reprojectionPx",obs==null?JSONObject.NULL:obs.reprojectionPx());
        data.put("unambiguous",obs==null?JSONObject.NULL:obs.unambiguous());
        data.put("usable",obs!=null&&obs.usable());
        if(obs!=null&&obs.quality()!=null){
            MarkerViewQuality q=obs.quality();
            data.put("incidenceDegrees",finite(q.incidenceDegrees()));
            data.put("thicknessPx",finite(q.thicknessPx()));
            data.put("positionSensitivityMm",finite(q.positionSensitivityMm()));
            data.put("rotationSensitivityDegrees",finite(q.rotationSensitivityDegrees()));
        }
        data.put("raw",raw==null?JSONObject.NULL:new JSONArray(raw.clone()));

        String name=String.format(Locale.US,"frame-%02d",Math.floorMod(slot,32));
        File png=new File(directory,name+".png"),json=new File(directory,name+".json");
        File pngPart=new File(directory,name+".png.tmp"),jsonPart=new File(directory,name+".json.tmp");
        Bitmap bitmap=null;
        try{
            bitmap=Bitmap.createBitmap(pixels,width,height,Bitmap.Config.ARGB_8888);
            try(FileOutputStream output=new FileOutputStream(pngPart)){
                if(!bitmap.compress(Bitmap.CompressFormat.PNG,100,output))throw new IOException("PNG compression failed");
            }
            try(FileOutputStream output=new FileOutputStream(jsonPart)){
                output.write(data.toString(2).getBytes(StandardCharsets.UTF_8));
            }
            // Remove the old completion marker before replacing its frame so
            // interrupted writes cannot pair a new image with old coordinates.
            remove(json);remove(png);
            if(!pngPart.renameTo(png))throw new IOException("Cannot publish diagnostic PNG");
            if(!jsonPart.renameTo(json))throw new IOException("Cannot publish diagnostic metadata");
        }finally{
            if(bitmap!=null)bitmap.recycle();
            pngPart.delete();jsonPart.delete();
        }
    }

    /** Pure Y-plane copy: input position/limit and underlying bytes are unchanged. */
    static int[] luminanceArgb(ByteBuffer buffer,int width,int height,int rowStride,int pixelStride){
        if(buffer==null||width<=0||height<=0||rowStride<=0||pixelStride<=0
                ||(long)width*height>Integer.MAX_VALUE)throw new IllegalArgumentException("Invalid luminance dimensions");
        ByteBuffer y=buffer.duplicate();int origin=y.position();
        long last=(long)origin+(long)(height-1)*rowStride+(long)(width-1)*pixelStride;
        if(last>=y.limit())throw new IllegalArgumentException("Incomplete luminance plane");
        int[] pixels=new int[width*height];
        for(int row=0;row<height;row++)for(int col=0;col<width;col++){
            int value=y.get(origin+row*rowStride+col*pixelStride)&255;
            pixels[row*width+col]=0xff000000|(value<<16)|(value<<8)|value;
        }
        return pixels;
    }

    private static Object finite(double value){return Double.isFinite(value)?value:JSONObject.NULL;}

    private static Object array(float[] values) throws Exception {
        return values==null?JSONObject.NULL:new JSONArray(values.clone());
    }
    private static void remove(File file) throws IOException {
        if(file.exists()&&!file.delete())throw new IOException("Cannot replace "+file.getName());
    }
}
