package com.figbot.scanner;

/** Detection box in the ARCore CPU image coordinate system. */
public record FigDetection(
        float left,
        float top,
        float right,
        float bottom,
        float confidence,
        int imageWidth,
        int imageHeight) {

    public float centerX() { return (left + right) * 0.5f; }
    public float centerY() { return (top + bottom) * 0.5f; }
}
