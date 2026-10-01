package com.figbot.scanner;

import java.nio.ByteBuffer;
import java.nio.FloatBuffer;

/** Reusable single-pass YUV420 -> letterboxed RGB/CHW, matching detector preprocessing. */
final class YuvTensorConverter {
    private final int size, pixels;
    private final float[] rgb;
    private final byte[][] planeBytes=new byte[3][];
    private final int[] columns,rows;
    private int previousWidth,previousHeight;
    YuvTensorConverter(int size){
        this.size=size;pixels=size*size;rgb=new float[pixels*3];columns=new int[size];rows=new int[size];
    }
    void convert(int width,int height,ByteBuffer[] planes,int[] rowStride,int[] pixelStride,FloatBuffer output){
        if(width!=previousWidth||height!=previousHeight){
            float scale=Math.min((float)size/width,(float)size/height);
            float padX=(size-width*scale)*.5f,padY=(size-height*scale)*.5f;
            for(int i=0;i<size;i++){
                float x=(i-padX)/scale,y=(i-padY)/scale;
                columns[i]=x<0||x>=width?-1:(int)x;
                rows[i]=y<0||y>=height?-1:(int)y;
            }
            previousWidth=width;previousHeight=height;
        }
        for(int i=0;i<3;i++){
            ByteBuffer source=planes[i].duplicate();int length=source.remaining();
            if(planeBytes[i]==null||planeBytes[i].length<length)planeBytes[i]=new byte[length];
            source.get(planeBytes[i],0,length);
        }
        for(int y=0;y<size;y++)for(int x=0;x<size;x++){
            int at=y*size+x,sx=columns[x],sy=rows[y];
            if(sx<0||sy<0){rgb[at]=rgb[pixels+at]=rgb[2*pixels+at]=114f/255f;continue;}
            int yy=planeBytes[0][sy*rowStride[0]+sx*pixelStride[0]]&255;
            int u=(planeBytes[1][sy/2*rowStride[1]+sx/2*pixelStride[1]]&255)-128;
            int v=(planeBytes[2][sy/2*rowStride[2]+sx/2*pixelStride[2]]&255)-128;
            rgb[at]=clamp(yy+1.402f*v);
            rgb[pixels+at]=clamp(yy-.344136f*u-.714136f*v);
            rgb[2*pixels+at]=clamp(yy+1.772f*u);
        }
        output.clear();output.put(rgb);output.rewind();
    }
    private static float clamp(float value){return Math.max(0f,Math.min(255f,value))/255f;}
}
