package com.figbot.scanner.so101;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Visual completion gate for one pick.  Motion completion alone is never a
 * successful harvest: the fruit must be seen carried away from the pickup
 * area and a new, stable object must then be seen inside the basket volume.
 */
public final class PickEvidence {
    public enum Outcome { PENDING, CONFIRMED, UNKNOWN }

    public record Basket(double x, double y, double radius, double bottom, double top) {
        public Basket {
            if (!Double.isFinite(x) || !Double.isFinite(y) || !Double.isFinite(radius)
                    || !Double.isFinite(bottom) || !Double.isFinite(top)
                    || radius <= 0 || top < bottom)
                throw new IllegalArgumentException("Geçerli sepet hacmi gerekli.");
        }
    }

    /** A pre-pick frame is deliberately explicit so one stale frame cannot become a baseline. */
    public record BaselineFrame(long capturedNs, List<double[]> objects) {
        public BaselineFrame {
            if (capturedNs < 0 || objects == null || objects.size() > 64)
                throw new IllegalArgumentException("Geçersiz ön-kavrama görüntüsü.");
            List<double[]> copy = new ArrayList<>();
            for (double[] p : objects) copy.add(point(p));
            objects = Collections.unmodifiableList(copy);
        }
        @Override public List<double[]> objects() {
            List<double[]> copy = new ArrayList<>();
            for (double[] p : objects) copy.add(p.clone());
            return Collections.unmodifiableList(copy);
        }
    }

    private static final long FRAME_MAX_AGE_NS = 750_000_000L;
    private static final long DECISION_TIMEOUT_NS = 2_000_000_000L;
    private static final double MATCH_GATE_MM = 35.0;

    private final Basket basket;
    private final double jawRadiusMm;
    private final double noveltyMm;
    private final List<double[]> baseline;
    private final boolean baselineReady;
    private long lastCapturedNs = -1;
    private long releaseNs = -1;
    private long lastCarryFrame = -1;
    private int carryFrames;
    private boolean carried;
    private int basketFrames;
    private long lastBasketFrame = -1;
    private Outcome outcome = Outcome.PENDING;

    /** Compatibility constructor. A caller supplying one snapshot gets a conservative baseline. */
    public PickEvidence(Basket basket, double jawRadiusMm, double noveltyMm, List<double[]> baseline) {
        this(basket, jawRadiusMm, noveltyMm, baseline, baseline != null && !baseline.isEmpty());
    }

    private PickEvidence(Basket basket, double jawRadiusMm, double noveltyMm,
                         List<double[]> baseline, boolean ready) {
        if (basket == null || !Double.isFinite(jawRadiusMm) || jawRadiusMm <= 0
                || !Double.isFinite(noveltyMm) || noveltyMm <= 0)
            throw new IllegalArgumentException("Kıskaç ve hareket eşikleri gerekli.");
        this.basket = basket;
        this.jawRadiusMm = jawRadiusMm;
        this.noveltyMm = noveltyMm;
        List<double[]> copy = new ArrayList<>();
        if (baseline != null) for (double[] p : baseline) copy.add(point(p));
        this.baseline = Collections.unmodifiableList(copy);
        this.baselineReady = ready;
    }

    /** Requires three separate chronological frames with the same basket count. */
    public static PickEvidence withBaseline(Basket basket, double jawRadiusMm, double noveltyMm,
                                             List<BaselineFrame> frames) {
        if (frames == null || frames.size() < 3)
            throw new IllegalArgumentException("Kavrama öncesi üç ayrı görüntü gerekli.");
        long previous = -1;
        int count = -1;
        List<double[]> last = null;
        for (BaselineFrame frame : frames) {
            if (frame.capturedNs() <= previous) throw new IllegalArgumentException("Ön görüntüler kronolojik olmalı.");
            previous = frame.capturedNs();
            if (count < 0) count = frame.objects().size();
            if (frame.objects().size() != count) throw new IllegalArgumentException("Ön görüntü nesne sayısı kararsız.");
            if (last != null && !stableMatch(last, frame.objects(), MATCH_GATE_MM))
                throw new IllegalArgumentException("Ön görüntülerde nesneler kararlı değil.");
            last = frame.objects();
        }
        return new PickEvidence(basket, jawRadiusMm, noveltyMm, last, true);
    }

    public boolean baselineReady() { return baselineReady; }
    public boolean carriedConfirmed() { return carried; }
    public Outcome outcome() { return outcome; }

    /** Called at the measured release instant, before visual evidence is evaluated. */
    public void released(long releaseNs) {
        if (releaseNs < 0) throw new IllegalArgumentException("Geçersiz bırakma zamanı.");
        this.releaseNs = releaseNs;
    }

    public Outcome observe(long capturedNs, long nowNs, List<double[]> objects,
                           double[] toolMm, boolean carrying, double groundAtToolMm) {
        if (outcome != Outcome.PENDING) return outcome;
        if (nowNs < 0 || capturedNs < 0 || objects == null || capturedNs > nowNs
                || nowNs - capturedNs > FRAME_MAX_AGE_NS) return timeout(nowNs);
        if (capturedNs == lastCapturedNs) return outcome;
        if (lastCapturedNs >= 0 && capturedNs < lastCapturedNs)
            throw new IllegalArgumentException("Görüntü zamanı geriye gitti.");
        lastCapturedNs = capturedNs;
        List<double[]> frame = new ArrayList<>();
        for (double[] p : objects) frame.add(point(p));
        if (carrying && toolMm != null && validTool(toolMm, groundAtToolMm)
                && nearAny(toolMm, frame, jawRadiusMm + 25)) {
            if (lastCarryFrame != capturedNs) {
                if (lastCarryFrame >= 0 && capturedNs > lastCarryFrame) carryFrames++;
                else carryFrames = 1;
                lastCarryFrame = capturedNs;
            }
            if (carryFrames >= 2) carried = true;
        }
        if (!carried || releaseNs < 0 || capturedNs < releaseNs) return timeout(nowNs);
        if (inBasket(frame)) {
            if (lastBasketFrame >= 0 && capturedNs > lastBasketFrame
                    && hasNovelBasketObject(frame)) basketFrames++;
            else if (lastBasketFrame < 0 && hasNovelBasketObject(frame)) basketFrames = 1;
            lastBasketFrame = capturedNs;
            if (basketFrames >= 2) outcome = Outcome.CONFIRMED;
        }
        return timeout(nowNs);
    }

    private Outcome timeout(long nowNs) {
        if (releaseNs >= 0 && nowNs - releaseNs >= DECISION_TIMEOUT_NS) outcome = Outcome.UNKNOWN;
        return outcome;
    }

    private boolean hasNovelBasketObject(List<double[]> frame) {
        for (double[] p : frame) {
            boolean seen = false;
            for (double[] old : baseline) if (distance(p, old) <= MATCH_GATE_MM) { seen = true; break; }
            if (!seen) return true;
        }
        return false;
    }

    private boolean inBasket(List<double[]> frame) {
        for (double[] p : frame) {
            if (Math.hypot(p[0] - basket.x(), p[1] - basket.y()) <= basket.radius()
                    && p[2] >= basket.bottom() && p[2] <= basket.top()) return true;
        }
        return false;
    }

    private boolean validTool(double[] p, double ground) {
        return p.length == 3 && Double.isFinite(p[0]) && Double.isFinite(p[1]) && Double.isFinite(p[2])
                && Double.isFinite(ground) && p[2] >= ground + Math.max(15, jawRadiusMm * .75);
    }

    private boolean nearAny(double[] tool, List<double[]> objects, double gate) {
        for (double[] p : objects) if (distance(tool, p) <= gate) return true;
        return false;
    }

    private static boolean stableMatch(List<double[]> a, List<double[]> b, double gate) {
        if (a.size() != b.size()) return false;
        boolean[] used = new boolean[b.size()];
        for (double[] p : a) {
            int best = -1; double d = Double.POSITIVE_INFINITY;
            for (int i=0;i<b.size();i++) if (!used[i] && distance(p,b.get(i))<d) {d=distance(p,b.get(i));best=i;}
            if (best<0 || d>gate) return false; used[best]=true;
        }
        return true;
    }

    private static double[] point(double[] p) {
        if (p == null || p.length != 3) throw new IllegalArgumentException("XYZ nokta gerekli.");
        for (double v : p) if (!Double.isFinite(v)) throw new IllegalArgumentException("Sonlu XYZ gerekli.");
        return p.clone();
    }
    private static double distance(double[] a,double[] b) {
        return Math.sqrt(Math.pow(a[0]-b[0],2)+Math.pow(a[1]-b[1],2)+Math.pow(a[2]-b[2],2));
    }
}
