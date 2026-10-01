package com.figbot.scanner;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

import java.util.List;

public class YoloDecoderTest {
    @Test
    public void decodesChannelsFirstAndSuppressesOverlap() {
        float[][][] output = new float[1][5][3];
        set(output, 0, 256, 256, 100, 80, 0.9f);
        set(output, 1, 258, 258, 100, 80, 0.8f);
        set(output, 2, 80, 90, 20, 30, 0.1f);

        List<FigDetection> detections = YoloDecoder.decode(output, 512, 640, 480, 0.25f, 0.45f);

        assertEquals(1, detections.size());
        assertEquals(0.9f, detections.get(0).confidence(), 0.0001f);
    }

    private static void set(float[][][] output, int index, float x, float y,
                            float width, float height, float confidence) {
        output[0][0][index] = x;
        output[0][1][index] = y;
        output[0][2][index] = width;
        output[0][3][index] = height;
        output[0][4][index] = confidence;
    }
}
