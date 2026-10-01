package com.figbot.scanner.so101;

import java.util.ArrayList;
import java.util.List;

/**
 * Conservative, conditional visual evidence, not proof of physical grasp.
 * The caller must supply depth observations and tool/phase sampled at capturedNs (within
 * its bounded history tolerance). The basket must remain visible during the baseline and
 * verification frames. Occlusion, detector errors and objects entering from outside the
 * observed scene remain physical-validation limitations; disappearance never means success.
 */
public final class PickEvidence {
    public enum Outcome { PENDING, CONFIRMED, UNKNOWN }
    public record Basket(double x,double y,double radius,double bottom,double top) {
        public Basket {
            for(double v:new double[]{x,y,radius,bottom,top})if(!Double.isFinite(v))throw new IllegalArgumentException("Finite basket measurements required");
            if(radius<=0||top<=bottom)throw new IllegalArgumentException("Invalid measured basket volume");
        }
        public boolean contains(double[] p) {
            return valid(p)&&Math.hypot(p[0]-x,p[1]-y)<=radius&&p[2]>=bottom&&p[2]<=top;
        }
    }
    public record BaselineFrame(long capturedNs,List<double[]> objects) {
        public BaselineFrame {
            if(capturedNs<=0||objects==null||objects.size()>64)throw new IllegalArgumentException("Timestamped baseline depth frame required");
            List<double[]> copy=new ArrayList<>();
            for(double[] p:objects){if(!valid(p))throw new IllegalArgumentException("Finite baseline XYZ required");copy.add(p.clone());}
            objects=List.copyOf(copy);
        }
        @Override public List<double[]> objects(){List<double[]> copy=new ArrayList<>();for(double[]p:objects)copy.add(p.clone());return List.copyOf(copy);}
    }
    private static final long MAX_AGE_NS=750_000_000L, BASELINE_MAX_SPAN_NS=2_000_000_000L;
    private final Basket basket;
    private final double jawRadiusMm,noveltyMm;
    private final List<double[]> baselineUnion=new ArrayList<>();
    private int baselineCount=-1,carryFrames,basketFrames;
    private long baselineLastNs=-1,lastFrame=-1,releaseNs=-1,lastNowNs=-1;
    private boolean baselineReady,carried;
    private double[] carryAnchorFig,carryAnchorTool,previousFig,previousTool,arrival;
    private Outcome outcome=Outcome.PENDING;

    /** Legacy single snapshot is useful for display only and cannot confirm a deposit. */
    public PickEvidence(Basket basket,double jawRadiusMm,double noveltyMm,List<double[]> initialBasket) {
        if(basket==null||!Double.isFinite(jawRadiusMm)||jawRadiusMm<=0||!Double.isFinite(noveltyMm)||noveltyMm<=0)
            throw new IllegalArgumentException("Measured jaw/basket tolerances required");
        this.basket=basket;this.jawRadiusMm=jawRadiusMm;this.noveltyMm=noveltyMm;
        if(initialBasket==null)throw new IllegalArgumentException("Basket observations required");
        for(double[]p:initialBasket)if(valid(p)&&basket.contains(p))baselineUnion.add(p.clone());
    }

    /** Requires three distinct, recent-in-relation-to-each-other, stable pre-pick frames. */
    public static PickEvidence withBaseline(Basket basket,double jawRadiusMm,double noveltyMm,List<BaselineFrame> frames) {
        PickEvidence result=new PickEvidence(basket,jawRadiusMm,noveltyMm,List.of());
        result.acceptBaseline(frames);return result;
    }
    private void acceptBaseline(List<BaselineFrame> frames) {
        if(frames==null||frames.size()<3||frames.size()>16)return;
        long previousNs=-1,firstNs=frames.get(0).capturedNs;
        List<double[]> previous=null;
        boolean stable=true;
        for(BaselineFrame frame:frames) {
            if(frame==null||frame.capturedNs<=previousNs||frame.capturedNs-firstNs>BASELINE_MAX_SPAN_NS){stable=false;break;}
            previousNs=frame.capturedNs;
            List<double[]> current=basketPoints(frame.objects);
            if(previous==null)baselineCount=current.size();
            else if(current.size()!=baselineCount||!oneToOneNearby(previous,current,noveltyMm))stable=false;
            for(double[]p:current)baselineUnion.add(p.clone());
            previous=current;
        }
        baselineLastNs=previousNs;baselineReady=stable;
    }
    public void released(long releaseNs) {
        if(releaseNs<=0)throw new IllegalArgumentException("Actual positive release timestamp required");
        if(this.releaseNs<0)this.releaseNs=releaseNs;
    }
    public Outcome observe(long capturedNs,long nowNs,List<double[]> figs,double[] toolMm,
                           boolean carrying,double groundAtToolMm) {
        if(nowNs<0||nowNs<lastNowNs)throw new IllegalArgumentException("Monotonic evidence clock required");
        lastNowNs=nowNs;
        if(outcome!=Outcome.PENDING)return outcome;
        if(releaseNs>0&&nowNs>=releaseNs&&nowNs-releaseNs>2_000_000_000L){outcome=Outcome.UNKNOWN;return outcome;}
        if(capturedNs<=lastFrame||capturedNs<=0||capturedNs>nowNs||nowNs-capturedNs>MAX_AGE_NS)return outcome;
        lastFrame=capturedNs;
        if(figs==null)return outcome;
        if(carrying&&releaseNs<0) {
            // A basket fruit near the moving tool must not be mistaken for a carried source fruit.
            if(valid(toolMm)&&Double.isFinite(groundAtToolMm)&&toolMm[2]-groundAtToolMm>jawRadiusMm&&!basket.contains(toolMm)) {
                double[] match=carryMatch(figs,toolMm);
                if(match!=null)acceptCarry(match,toolMm);else resetCarrySequence();
            }else resetCarrySequence();
        }
        if(releaseNs>0&&capturedNs>=releaseNs&&carried&&baselineReady&&baselineLastNs<releaseNs) {
            List<double[]> current=basketPoints(figs);
            double[] novel=null;
            if(current.size()==baselineCount+1)for(double[]p:current) {
                boolean old=false;for(double[]b:baselineUnion)if(distance(b,p)<noveltyMm){old=true;break;}
                if(!old){if(novel!=null){novel=null;break;}novel=p;}
            }
            if(novel!=null) {
                if(arrival!=null&&distance(arrival,novel)<=noveltyMm)basketFrames++;
                else basketFrames=1;
                arrival=novel.clone();
            }else {basketFrames=0;arrival=null;}
            if(basketFrames>=3)outcome=Outcome.CONFIRMED;
        }
        return outcome;
    }
    private double[] carryMatch(List<double[]> figs,double[] tool) {
        double[] predicted=tool;
        if(previousFig!=null){predicted=new double[3];for(int i=0;i<3;i++)predicted[i]=previousFig[i]+tool[i]-previousTool[i];}
        double[] best=null;double error=Double.POSITIVE_INFINITY;
        for(double[]p:figs)if(valid(p)&&!basket.contains(p)&&distance(p,tool)<=jawRadiusMm) {
            double d=distance(p,predicted);
            if(d<=Math.min(jawRadiusMm,noveltyMm)&&d<error){best=p;error=d;}
        }
        return best;
    }
    private void acceptCarry(double[] fig,double[] tool) {
        if(carryAnchorFig==null){carryAnchorFig=fig.clone();carryAnchorTool=tool.clone();carryFrames=1;}
        else {
            carryFrames++;
            double[] expected=new double[3];for(int i=0;i<3;i++)expected[i]=carryAnchorFig[i]+tool[i]-carryAnchorTool[i];
            if(carryFrames>=2&&distance(tool,carryAnchorTool)>=noveltyMm
                    &&distance(fig,carryAnchorFig)>=noveltyMm&&distance(fig,expected)<=Math.min(jawRadiusMm,noveltyMm))carried=true;
        }
        previousFig=fig.clone();previousTool=tool.clone();
    }
    private void resetCarrySequence(){carryAnchorFig=carryAnchorTool=previousFig=previousTool=null;carryFrames=0;}
    private List<double[]> basketPoints(List<double[]> objects) {
        List<double[]> result=new ArrayList<>();
        for(double[]p:objects)if(valid(p)&&basket.contains(p)) {
            boolean duplicate=false;for(double[]existing:result)if(distance(existing,p)<noveltyMm){duplicate=true;break;}
            if(!duplicate)result.add(p);
        }
        return result;
    }
    private static boolean oneToOneNearby(List<double[]> a,List<double[]> b,double tolerance) {
        int[] matched=new int[b.size()];java.util.Arrays.fill(matched,-1);
        for(int i=0;i<a.size();i++)if(!augment(i,a,b,tolerance,new boolean[b.size()],matched))return false;
        return true;
    }
    private static boolean augment(int i,List<double[]>a,List<double[]>b,double tolerance,boolean[]visited,int[]matched) {
        for(int j=0;j<b.size();j++)if(!visited[j]&&distance(a.get(i),b.get(j))<=tolerance) {
            visited[j]=true;if(matched[j]<0||augment(matched[j],a,b,tolerance,visited,matched)){matched[j]=i;return true;}
        }
        return false;
    }
    public Outcome outcome(){return outcome;}
    public boolean carriedConfirmed(){return carried;}
    public boolean baselineReady(){return baselineReady;}
    private static boolean valid(double[]p){return p!=null&&p.length>=3&&Double.isFinite(p[0])&&Double.isFinite(p[1])&&Double.isFinite(p[2]);}
    private static double distance(double[]a,double[]b){return Math.hypot(Math.hypot(a[0]-b[0],a[1]-b[1]),a[2]-b[2]);}
}
