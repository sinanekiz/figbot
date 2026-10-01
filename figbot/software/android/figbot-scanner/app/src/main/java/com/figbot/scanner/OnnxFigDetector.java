package com.figbot.scanner;

import android.content.Context;
import android.media.Image;

import java.io.IOException;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.Collections;
import java.util.List;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtException;
import ai.onnxruntime.OrtSession;

/** Offline ONNX detector for one `fig` class. */
final class OnnxFigDetector implements AutoCloseable {
    static final int INPUT_SIZE = 640;
    static final float CONFIDENCE_THRESHOLD = 0.35f;
    private static final float IOU_THRESHOLD = 0.45f;

    private final OrtEnvironment environment;
    private final OrtSession session;
    private final String inputName;
    private final YuvTensorConverter converter=new YuvTensorConverter(INPUT_SIZE);
    private final FloatBuffer tensorBuffer=ByteBuffer.allocateDirect(INPUT_SIZE*INPUT_SIZE*3*Float.BYTES)
            .order(ByteOrder.nativeOrder()).asFloatBuffer();
    private final java.io.File diagnosticDirectory;
    private final boolean debugDiagnostics;
    private long lastDiagnosticNs;
    private int savedDiagnosticKinds;

    OnnxFigDetector(Context context) throws IOException, OrtException {
        diagnosticDirectory=context.getFilesDir();
        debugDiagnostics=(context.getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)!=0;
        byte[] model;
        try (InputStream stream = context.getAssets().open("figbot_fig_detector.onnx")) {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buffer = new byte[16 * 1024];
            int count;
            while ((count = stream.read(buffer)) != -1) {
                bytes.write(buffer, 0, count);
            }
            model = bytes.toByteArray();
        }
        environment = OrtEnvironment.getEnvironment();
        OrtSession.SessionOptions options = new OrtSession.SessionOptions();
        options.setIntraOpNumThreads(Math.max(1, Math.min(4, Runtime.getRuntime().availableProcessors() - 1)));
        options.setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT);
        session = environment.createSession(model, options);
        inputName = session.getInputNames().iterator().next();
    }

    List<FigDetection> detect(Image image) throws OrtException {
        long began=System.nanoTime();
        int width = image.getWidth();
        int height = image.getHeight();
        FloatBuffer input = imageToTensor(image, INPUT_SIZE);
        long prepared=System.nanoTime();
        long[] shape = {1, 3, INPUT_SIZE, INPUT_SIZE};
        try (OnnxTensor tensor = OnnxTensor.createTensor(environment, input, shape);
             OrtSession.Result result = session.run(Collections.singletonMap(inputName, tensor))) {
            Object value = result.get(0).getValue();
            if (!(value instanceof float[][][] output)) {
                throw new OrtException("Unexpected YOLO output type: " + value.getClass().getName());
            }
            List<FigDetection> decoded=YoloDecoder.decode(
                    output, INPUT_SIZE, width, height, CONFIDENCE_THRESHOLD, IOU_THRESHOLD);
            long finished=System.nanoTime();
            if(finished-lastDiagnosticNs>5_000_000_000L){
                lastDiagnosticNs=finished;
                List<FigDetection> candidates=YoloDecoder.decode(output,INPUT_SIZE,width,height,.05f,IOU_THRESHOLD);
                android.util.Log.i("FigbotDetector","image="+width+"x"+height
                    +" prepare_ms="+(prepared-began)/1_000_000+" infer_ms="+(finished-prepared)/1_000_000
                    +" accepted="+decoded.size()+" candidates="+candidates);
                int kind=decoded.isEmpty()?1:2;
                if(debugDiagnostics&&(savedDiagnosticKinds&kind)==0){
                    saveDiagnostic(input,decoded.isEmpty()?"detector_miss.png":"detector_hit.png");savedDiagnosticKinds|=kind;
                }
            }
            return decoded;
        }
    }

    private void saveDiagnostic(FloatBuffer input,String name){
        int n=INPUT_SIZE*INPUT_SIZE;int[] pixels=new int[n];
        for(int i=0;i<n;i++)pixels[i]=0xff000000|((int)(input.get(i)*255)<<16)
                |((int)(input.get(n+i)*255)<<8)|(int)(input.get(2*n+i)*255);
        android.graphics.Bitmap bitmap=android.graphics.Bitmap.createBitmap(pixels,INPUT_SIZE,INPUT_SIZE,android.graphics.Bitmap.Config.ARGB_8888);
        try(java.io.FileOutputStream stream=new java.io.FileOutputStream(new java.io.File(diagnosticDirectory,name))){
            bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,stream);
        }catch(IOException ignored){}finally{bitmap.recycle();}
    }

    private FloatBuffer imageToTensor(Image image, int inputSize) {
        Image.Plane[] p=image.getPlanes();
        converter.convert(image.getWidth(),image.getHeight(),
                new ByteBuffer[]{p[0].getBuffer(),p[1].getBuffer(),p[2].getBuffer()},
                new int[]{p[0].getRowStride(),p[1].getRowStride(),p[2].getRowStride()},
                new int[]{p[0].getPixelStride(),p[1].getPixelStride(),p[2].getPixelStride()},tensorBuffer);
        return tensorBuffer;
    }

    @Override
    public void close() throws OrtException {
        session.close();
    }
}
