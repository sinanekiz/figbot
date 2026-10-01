package com.figbot.scanner.so101;

import java.util.ArrayList;
import java.util.List;

/** Independent measured tool positions, not an operator's boolean approval. */
public final class ArmValidation {
    public record Measurement(int[] raw, double[] measuredMm) {
        public Measurement { raw=raw.clone(); measuredMm=measuredMm.clone(); }
        @Override public int[] raw(){return raw.clone();}
        @Override public double[] measuredMm(){return measuredMm.clone();}
    }
    private final So101Kinematics model;
    private final List<Measurement> measurements=new ArrayList<>();
    private final double toleranceMm;
    public ArmValidation(ArmProfile profile,double toleranceMm){
        if(!Double.isFinite(toleranceMm)||toleranceMm<=0||toleranceMm>10)
            throw new IllegalArgumentException("Uç konum ölçüm toleransı 0–10 mm olmalı.");
        model=new So101Kinematics(profile);this.toleranceMm=toleranceMm;
    }
    public synchronized double add(int[] raw,double[] measuredMm){
        if(raw==null||raw.length!=6||measuredMm==null||measuredMm.length!=3)
            throw new IllegalArgumentException("Altı enkoder ve ölçülmüş XYZ gerekli.");
        for(double v:measuredMm)if(!Double.isFinite(v))throw new IllegalArgumentException("Sonlu XYZ gerekli.");
        double[] predicted=model.forward(raw);double error=distance(predicted,measuredMm);
        if(error>toleranceMm)throw new IllegalArgumentException(String.format(java.util.Locale.US,
                "Kol modeli ölçümden %.1f mm uzak. Eklem referansı düzeltilmeli.",error));
        for(Measurement m:measurements)if(distance(m.measuredMm,measuredMm)<20)
            throw new IllegalArgumentException("Farklı bir ölçüm noktası kullan; noktalar en az 20 mm ayrı olmalı.");
        measurements.add(new Measurement(raw,measuredMm));return error;
    }
    public synchronized boolean isValid(){
        if(measurements.size()<3)return false;
        double span=0,area=0;
        for(Measurement a:measurements)for(Measurement b:measurements){
            span=Math.max(span,distance(a.measuredMm,b.measuredMm));
            for(Measurement c:measurements){
                double[] u=sub(b.measuredMm,a.measuredMm),v=sub(c.measuredMm,a.measuredMm);
                area=Math.max(area,Math.sqrt(Math.pow(u[1]*v[2]-u[2]*v[1],2)+
                    Math.pow(u[2]*v[0]-u[0]*v[2],2)+Math.pow(u[0]*v[1]-u[1]*v[0],2)));
            }
        }
        return span>=80 && area>=1600;
    }
    public synchronized List<Measurement> measurements(){return List.copyOf(measurements);}
    public synchronized void clear(){measurements.clear();}
    public double toleranceMm(){return toleranceMm;}
    private static double[] sub(double[]a,double[]b){return new double[]{a[0]-b[0],a[1]-b[1],a[2]-b[2]};}
    public static double distance(double[]a,double[]b){return Math.sqrt(Math.pow(a[0]-b[0],2)+Math.pow(a[1]-b[1],2)+Math.pow(a[2]-b[2],2));}
}
