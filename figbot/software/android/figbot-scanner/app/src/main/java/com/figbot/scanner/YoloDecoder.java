package com.figbot.scanner;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/** Decodes a one-class Ultralytics YOLO detection tensor and applies NMS. */
final class YoloDecoder {
    private YoloDecoder() {}

    static List<FigDetection> decode(
            float[][][] output,
            int inputSize,
            int sourceWidth,
            int sourceHeight,
            float confidenceThreshold,
            float iouThreshold) {
        if (output.length != 1 || output[0].length == 0) return List.of();
        boolean channelsFirst = output[0].length <= 128;
        int candidates = channelsFirst ? output[0][0].length : output[0].length;
        int channels = channelsFirst ? output[0].length : output[0][0].length;
        if (channels < 5) return List.of();

        float scale = Math.min((float) inputSize / sourceWidth, (float) inputSize / sourceHeight);
        float padX = (inputSize - sourceWidth * scale) * 0.5f;
        float padY = (inputSize - sourceHeight * scale) * 0.5f;
        List<FigDetection> decoded = new ArrayList<>();
        for (int index = 0; index < candidates; index++) {
            float confidence = value(output, channelsFirst, 4, index);
            if (!Float.isFinite(confidence) || confidence < confidenceThreshold) continue;
            float centerX = value(output, channelsFirst, 0, index);
            float centerY = value(output, channelsFirst, 1, index);
            float width = value(output, channelsFirst, 2, index);
            float height = value(output, channelsFirst, 3, index);
            float left = clamp((centerX - width * 0.5f - padX) / scale, 0, sourceWidth - 1);
            float top = clamp((centerY - height * 0.5f - padY) / scale, 0, sourceHeight - 1);
            float right = clamp((centerX + width * 0.5f - padX) / scale, 0, sourceWidth - 1);
            float bottom = clamp((centerY + height * 0.5f - padY) / scale, 0, sourceHeight - 1);
            if (right - left < 2 || bottom - top < 2) continue;
            decoded.add(new FigDetection(
                    left, top, right, bottom, confidence, sourceWidth, sourceHeight));
        }
        decoded.sort(Comparator.comparing(FigDetection::confidence).reversed());
        List<FigDetection> kept = new ArrayList<>();
        for (FigDetection candidate : decoded) {
            boolean overlaps = kept.stream().anyMatch(existing -> iou(candidate, existing) > iouThreshold);
            if (!overlaps) kept.add(candidate);
            if (kept.size() == 25) break;
        }
        return List.copyOf(kept);
    }

    private static float value(float[][][] output, boolean channelsFirst, int channel, int candidate) {
        return channelsFirst ? output[0][channel][candidate] : output[0][candidate][channel];
    }

    private static float clamp(float value, float minimum, float maximum) {
        return Math.max(minimum, Math.min(maximum, value));
    }

    private static float iou(FigDetection first, FigDetection second) {
        float intersectionWidth = Math.max(0, Math.min(first.right(), second.right())
                - Math.max(first.left(), second.left()));
        float intersectionHeight = Math.max(0, Math.min(first.bottom(), second.bottom())
                - Math.max(first.top(), second.top()));
        float intersection = intersectionWidth * intersectionHeight;
        float firstArea = (first.right() - first.left()) * (first.bottom() - first.top());
        float secondArea = (second.right() - second.left()) * (second.bottom() - second.top());
        return intersection / Math.max(1.0e-6f, firstArea + secondArea - intersection);
    }
}
