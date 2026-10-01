package com.figbot.scanner.vision;

import java.util.ArrayList;
import java.util.List;
import org.opencv.calib3d.Calib3d;
import org.opencv.core.*;

/** Robot-model referenced eye-to-hand fit with unseen validation poses. */
public final class MarkerCalibration {
    public static final int FIT_COUNT=8, TOTAL_COUNT=12;
    public static final int KNOWN_MOUNT_FIT_COUNT=2, KNOWN_MOUNT_TOTAL_COUNT=4;
    public record Sample(RigidPose baseTool,RigidPose worldMarker) {}
    public record Result(RigidPose baseWorld,RigidPose toolMarker,double fitRmsMm,double heldRmsMm,double heldMaxMm) {
        public RigidPose observedTool(RigidPose worldMarker){return baseWorld.compose(worldMarker).compose(toolMarker.inverse());}
        public double[] robotPoint(double[] worldM){return baseWorld.map(new double[]{worldM[0]*1000,worldM[1]*1000,worldM[2]*1000});}
    }
    public static Result fit(List<Sample> samples){
        return fit(samples,null);
    }
    /** Re-estimate only the camera, preserving the previously validated rigid mount.
     * B_C = B_T * T_M * inverse(C_M) is determined by one full marker pose when
     * T_M is known. Two fit poses average noise and two unseen poses verify it;
     * the two nonparallel rotation axes needed to learn an UNKNOWN mount do not
     * apply here. Legacy seven-pose recordings retain their original 3+4 split.
     * Pure translations cannot expose every incorrect mount translation, so
     * this short fit requires a genuinely unchanged, previously learned mount.
     */
    public static Result fitKnownMount(List<Sample> samples,RigidPose toolMarker){
        if(toolMarker==null||samples==null
                ||(samples.size()!=KNOWN_MOUNT_TOTAL_COUNT&&samples.size()!=7))
            throw new IllegalArgumentException("Bilinen etiket bağlantısı ve 4 ayrı duruş gerekli (eski 7 duruşlu kayıt da desteklenir)");
        if(toolMarker.distance(RigidPose.identity())>200)
            throw new IllegalArgumentException("Etiket-uç mesafesi tutarsız");
        requireIndependentKnownMountPoses(samples);
        int fitCount=samples.size()==7?3:KNOWN_MOUNT_FIT_COUNT;
        List<Sample> train=samples.subList(0,fitCount),held=samples.subList(fitCount,samples.size());
        RigidPose initial=train.get(0).baseTool.compose(toolMarker).compose(train.get(0).worldMarker.inverse());
        RigidPose camera=HandEyeRefinement.refineCamera(train,initial,toolMarker).baseCamera();
        double[] fit=errors(train,camera,toolMarker),check=errors(held,camera,toolMarker);
        if(fit[0]>6||fit[1]>10||check[0]>8||check[1]>12)
            throw new IllegalArgumentException(String.format(java.util.Locale.US,"Kısa eşleme kontrolü: öğrenme %.1f / kontrol %.1f / en çok %.1f mm",fit[0],check[0],check[1]));
        return new Result(camera,toolMarker,fit[0],check[0],check[1]);
    }
    private static void requireIndependentKnownMountPoses(List<Sample> samples){
        for(int i=0;i<samples.size();i++){
            Sample a=samples.get(i);
            if(a==null||a.baseTool==null||a.worldMarker==null)
                throw new IllegalArgumentException("Kısa eşleme ölçümü eksik");
            for(int j=0;j<i;j++){
                Sample b=samples.get(j);
                if(a.baseTool.distance(b.baseTool)<15&&a.baseTool.angle(b.baseTool)<Math.toRadians(5))
                    throw new IllegalArgumentException("Kısa eşleme duruşları en az 15 mm veya 5° farklı olmalı");
            }
        }
    }
    /** Re-estimate the camera after a move, preserving a previously validated rigid tag mount. */
    public static Result fit(List<Sample> samples,RigidPose fixedToolMarker){
        if(samples==null||samples.size()!=TOTAL_COUNT)throw new IllegalArgumentException("12 ayrı duruş gerekli");
        List<Sample> train=samples.subList(0,FIT_COUNT),held=samples.subList(FIT_COUNT,TOTAL_COUNT);
        requireExcitation(train);requireExcitation(held);
        // Reject held-out duplicates of fit poses (different image != independent pose).
        for(Sample s:held)for(Sample f:train)if(s.baseTool.distance(f.baseTool)<15&&s.baseTool.angle(f.baseTool)<Math.toRadians(5))
            throw new IllegalArgumentException("Kontrol duruşları öğrenme duruşlarından farklı olmalı");
        List<Mat> gr=new ArrayList<>(),gt=new ArrayList<>(),cr=new ArrayList<>(),ct=new ArrayList<>();Mat r=new Mat(),t=new Mat();
        try{
            for(Sample s:train){
                // inv(B_T) * B_W * W_M = T_M, constant over all observations.
                add(s.baseTool.inverse(),gr,gt);add(s.worldMarker,cr,ct);
            }
            Calib3d.calibrateHandEye(gr,gt,cr,ct,r,t,Calib3d.CALIB_HAND_EYE_PARK);
            RigidPose bw=ArucoTracker.fromMats(r,t);
            List<RigidPose> offsets=new ArrayList<>();double[]mean=new double[3];
            for(Sample s:train){RigidPose offset=s.baseTool.inverse().compose(bw).compose(s.worldMarker);offsets.add(offset);double[]v=offset.translation();for(int i=0;i<3;i++)mean[i]+=v[i]/FIT_COUNT;}
            RigidPose tm=new RigidPose(offsets.get(0).rotation(),mean);
            HandEyeRefinement.Fit refined;
            if(fixedToolMarker==null)refined=HandEyeRefinement.refine(train,bw,tm);
            else {
                tm=fixedToolMarker;
                bw=train.get(0).baseTool.compose(tm).compose(train.get(0).worldMarker.inverse());
                refined=HandEyeRefinement.refineCamera(train,bw,tm);
            }
            bw=refined.baseCamera();tm=refined.toolMarker();
            if(tm.distance(RigidPose.identity())>200)throw new IllegalArgumentException("Etiket-uç mesafesi tutarsız");
            double[]fit=errors(train,bw,tm),validation=errors(held,bw,tm);
            if(fit[0]>6||fit[1]>10||validation[0]>8||validation[1]>12)
                throw new IllegalArgumentException(String.format(java.util.Locale.US,"Kamera-kol eşleme farkı: öğrenme %.1f / kontrol %.1f mm (en çok %.1f). Etiket mesafesi ayrı ölçümdür.",fit[0],validation[0],validation[1]));
            return new Result(bw,tm,fit[0],validation[0],validation[1]);
        }finally{for(List<Mat> list:List.of(gr,gt,cr,ct))for(Mat m:list)m.release();r.release();t.release();}
    }
    private static double[] errors(List<Sample> samples,RigidPose bw,RigidPose tm){
        double sum=0,max=0;for(Sample s:samples){RigidPose p=bw.compose(s.worldMarker).compose(tm.inverse());double e=p.distance(s.baseTool);sum+=e*e;max=Math.max(max,e);
            if(p.angle(s.baseTool)>Math.toRadians(8))throw new IllegalArgumentException("Etiket yönü ile kol modeli uyuşmuyor");}
        double rms=Math.sqrt(sum/samples.size());
        if(!Double.isFinite(rms)||!Double.isFinite(max))throw new IllegalArgumentException("Eşleme hata hesabı geçerli değil");
        return new double[]{rms,max};
    }
    private static void requireExcitation(List<Sample> samples){
        double span=0,crossMax=0;List<double[]>axes=new ArrayList<>();
        for(int i=0;i<samples.size();i++)for(int j=i+1;j<samples.size();j++){
            RigidPose a=samples.get(i).baseTool,b=samples.get(j).baseTool;span=Math.max(span,a.distance(b));
            RigidPose delta=a.inverse().compose(b);double angle=delta.angle(RigidPose.identity());
            if(angle<Math.toRadians(12)||angle>Math.toRadians(170))continue;
            double[][]m=delta.rotation();double den=2*Math.sin(angle);axes.add(new double[]{(m[2][1]-m[1][2])/den,(m[0][2]-m[2][0])/den,(m[1][0]-m[0][1])/den});
        }
        for(double[]a:axes)for(double[]b:axes){double dot=a[0]*b[0]+a[1]*b[1]+a[2]*b[2];crossMax=Math.max(crossMax,1-dot*dot);}
        if(span<45||crossMax<.15)throw new IllegalArgumentException("Duruş çeşitliliği az: taban yönünü ve bilek eğimini farklı yönlerde değiştir");
    }
    private static void add(RigidPose pose,List<Mat>rr,List<Mat>tt){
        Mat r=new Mat(3,3,CvType.CV_64F),t=new Mat(3,1,CvType.CV_64F);double[][]a=pose.rotation();for(int i=0;i<3;i++)r.put(i,0,a[i]);t.put(0,0,pose.translation());rr.add(r);tt.add(t);
    }
}
