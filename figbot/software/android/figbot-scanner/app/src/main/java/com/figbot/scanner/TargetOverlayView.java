package com.figbot.scanner;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.View;

import java.util.List;

/** Draws tracked 3D observations after the renderer projects them into screen coordinates. */
public final class TargetOverlayView extends View {
    public enum MarkerType { TARGET, ORIGIN, POSITIVE_X }

    public record Marker(float x, float y, String label, MarkerType type) {}
    public record DetectionBox(float left, float top, float right, float bottom, String label) {}

    /** A fig seen by the camera: orange while the camera moves, green when stable. */
    public record FigMarker(float x, float y, String label, boolean stable, boolean tracked) {}

    private final Paint ringPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint labelPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private volatile List<Marker> markers = List.of();
    private volatile List<DetectionBox> detectionBoxes = List.of();
    private volatile List<FigMarker> figMarkers = List.of();
    private volatile float[] toolCorners;
    public void setToolCorners(float[] corners){toolCorners=corners==null?null:corners.clone();invalidate();}

    public TargetOverlayView(Context context, AttributeSet attrs) {
        super(context, attrs);
        setWillNotDraw(false);
        setClickable(false);
        ringPaint.setStyle(Paint.Style.STROKE);
        ringPaint.setStrokeWidth(5f);
        fillPaint.setStyle(Paint.Style.FILL);
        textPaint.setTextSize(34f);
        textPaint.setColor(Color.WHITE);
        textPaint.setShadowLayer(5f, 1f, 1f, Color.BLACK);
        labelPaint.setTextSize(30f);
        labelPaint.setColor(Color.WHITE);
        labelPaint.setShadowLayer(6f, 1f, 1f, Color.BLACK);
    }

    public void setMarkers(List<Marker> value) {
        markers = List.copyOf(value);
        invalidate();
    }

    public void setDetectionBoxes(List<DetectionBox> value) {
        detectionBoxes = List.copyOf(value);
        invalidate();
    }

    public void setFigMarkers(List<FigMarker> value, boolean stable) {
        figMarkers = List.copyOf(value);
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float[] tool=toolCorners;
        if(tool!=null&&tool.length==8){
            ringPaint.setColor(Color.CYAN);ringPaint.setStrokeWidth(5);
            for(int i=0;i<4;i++){int j=(i+1)%4;canvas.drawLine(tool[2*i],tool[2*i+1],tool[2*j],tool[2*j+1],ringPaint);}
        }
        // Follow screen: camera-moving figs orange, stable figs green, target ringed.
        for (FigMarker fig : figMarkers) {
            int color = fig.stable() ? Color.rgb(50, 235, 90) : Color.rgb(255, 154, 0);
            fillPaint.setColor(Color.argb(52, Color.red(color), Color.green(color), Color.blue(color)));
            ringPaint.setColor(color);
            ringPaint.setStrokeWidth(fig.tracked() ? 9f : 5f);
            float radius = fig.tracked() ? 52f : 40f;
            canvas.drawCircle(fig.x(), fig.y(), radius, fillPaint);
            canvas.drawCircle(fig.x(), fig.y(), radius, ringPaint);
            labelPaint.setColor(Color.WHITE);
            canvas.drawText(fig.label(), fig.x() + radius + 12f, fig.y() - 10f, labelPaint);
        }
        ringPaint.setStrokeWidth(5f);
        int detectionColor = Color.rgb(50, 235, 90);
        ringPaint.setColor(detectionColor);
        ringPaint.setStrokeWidth(6f);
        fillPaint.setColor(Color.argb(42, 50, 235, 90));
        for (DetectionBox box : detectionBoxes) {
            canvas.drawRect(box.left(), box.top(), box.right(), box.bottom(), fillPaint);
            canvas.drawRect(box.left(), box.top(), box.right(), box.bottom(), ringPaint);
            float labelTop = Math.max(38f, box.top() - 12f);
            canvas.drawText(box.label(), box.left() + 8f, labelTop, textPaint);
        }
        ringPaint.setStrokeWidth(5f);
        for (Marker marker : markers) {
            int color = switch (marker.type()) {
                case TARGET -> Color.rgb(168, 217, 108);
                case ORIGIN -> Color.rgb(255, 191, 71);
                case POSITIVE_X -> Color.rgb(92, 190, 255);
            };
            fillPaint.setColor(Color.argb(70, Color.red(color), Color.green(color), Color.blue(color)));
            ringPaint.setColor(color);
            canvas.drawCircle(marker.x(), marker.y(), 34f, fillPaint);
            canvas.drawCircle(marker.x(), marker.y(), 34f, ringPaint);
            canvas.drawLine(marker.x() - 46f, marker.y(), marker.x() + 46f, marker.y(), ringPaint);
            canvas.drawLine(marker.x(), marker.y() - 46f, marker.x(), marker.y() + 46f, ringPaint);
            canvas.drawText(marker.label(), marker.x() + 44f, marker.y() - 38f, textPaint);
        }
    }
}
