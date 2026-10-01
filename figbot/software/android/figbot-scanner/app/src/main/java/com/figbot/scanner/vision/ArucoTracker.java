package com.figbot.scanner.vision;

import android.media.Image;
import com.google.ar.core.Pose;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.List;
import org.opencv.android.OpenCVLoader;
import org.opencv.calib3d.Calib3d;
import org.opencv.core.*;
import org.opencv.objdetect.*;

/** ID 0 / DICT_4X4_50 / measured 36 mm. No motor writes. Single inference-thread owner. */
public final class ArucoTracker {
    public static final double SIDE_MM=36;
    public record Observation(long capturedNs,int generation,RigidPose worldMarker,RigidPose cameraMarker,
                              float[] imageCorners,double reprojectionPx,boolean unambiguous,MarkerViewQuality quality) {
        public Observation { imageCorners=imageCorners.clone(); }
        @Override public float[] imageCorners(){return imageCorners.clone();}
        public boolean fresh(long now,int currentGeneration){return generation==currentGeneration&&now>=capturedNs&&now-capturedNs<400_000_000L;}
        public boolean usable(){return unambiguous&&quality!=null&&quality.usable();}
        public String measurementProblem(){
            if(!unambiguous)return "Etiket yönü iki anlamlı; görüş açısını biraz değiştir.";
            if(!usable())return "Etiket bu açı/uzaklıkta hassas ölçülemiyor; daha karşıdan göster.";
            return "";
        }
    }
    private final ArucoDetector detector;
    public ArucoTracker(){
        if(!OpenCVLoader.initLocal())throw new IllegalStateException("OpenCV yüklenemedi");
        DetectorParameters p=new DetectorParameters();p.set_cornerRefinementMethod(Objdetect.CORNER_REFINE_SUBPIX);
        detector=new ArucoDetector(Objdetect.getPredefinedDictionary(Objdetect.DICT_4X4_50),p);
    }
    public Observation detect(Image image,float[] focal,float[] principal,Pose cameraWorld,long captured,int generation){
        int w=image.getWidth(),h=image.getHeight();Image.Plane y=image.getPlanes()[0];
        ByteBuffer buffer=y.getBuffer().duplicate();int origin=buffer.position();byte[]packed=new byte[w*h];
        for(int row=0;row<h;row++){
            if(y.getPixelStride()==1){buffer.position(origin+row*y.getRowStride());buffer.get(packed,row*w,w);}
            else for(int col=0;col<w;col++)packed[row*w+col]=buffer.get(origin+row*y.getRowStride()+col*y.getPixelStride());
        }
        Mat gray=new Mat(h,w,CvType.CV_8UC1);gray.put(0,0,packed);
        try{return detectGray(gray,focal,principal,cameraWorld,captured,generation);}finally{gray.release();}
    }
    public Observation detectGray(Mat gray,float[] focal,float[] principal,Pose cameraWorld,long captured,int generation){
        List<Mat> corners=new ArrayList<>(),rejected=new ArrayList<>(),rv=new ArrayList<>(),tv=new ArrayList<>();
        Mat ids=new Mat(),k=Mat.eye(3,3,CvType.CV_64F);
        MatOfDouble distortion=new MatOfDouble();MatOfPoint2f imagePoints=new MatOfPoint2f();
        double h=SIDE_MM/2;
        MatOfPoint3f object=new MatOfPoint3f(new Point3(-h,h,0),new Point3(h,h,0),new Point3(h,-h,0),new Point3(-h,-h,0));
        try{
            if(focal.length!=2||principal.length!=2||!(focal[0]>0)||!(focal[1]>0))return null;
            k.put(0,0,(double)focal[0]);k.put(1,1,(double)focal[1]);k.put(0,2,(double)principal[0]);k.put(1,2,(double)principal[1]);
            detector.detectMarkers(gray,corners,ids,rejected);
            int index=-1;for(int i=0;i<ids.rows();i++)if((int)ids.get(i,0)[0]==0){if(index>=0)return null;index=i;}
            if(index<0)return null;
            Point[] pts=new Point[4];float[] pixels=new float[8];
            for(int j=0;j<4;j++){double[]p=corners.get(index).get(0,j);pts[j]=new Point(p[0],p[1]);pixels[j*2]=(float)p[0];pixels[j*2+1]=(float)p[1];}
            for(int j=0;j<4;j++)if(Math.hypot(pts[j].x-pts[(j+1)%4].x,pts[j].y-pts[(j+1)%4].y)<28)return null;
            imagePoints.fromArray(pts);
            Calib3d.solvePnPGeneric(object,imagePoints,k,distortion,rv,tv,false,Calib3d.SOLVEPNP_IPPE_SQUARE);
            RigidPose best=null,second=null;double bestError=Double.POSITIVE_INFINITY,secondError=Double.POSITIVE_INFINITY;
            for(int i=0;i<rv.size();i++){
                Mat rot=new Mat();MatOfPoint2f projected=new MatOfPoint2f();
                try{
                    // IPPE supplies an initial planar solution. Minimize actual corner
                    // reprojection error before comparing candidates and quality gates.
                    Calib3d.solvePnPRefineLM(object,imagePoints,k,distortion,rv.get(i),tv.get(i));
                    Calib3d.Rodrigues(rv.get(i),rot);RigidPose candidate=fromMats(rot,tv.get(i));
                    if(candidate.translation()[2]<=0||candidate.distance(RigidPose.identity())>2000)continue;
                    boolean front=true;for(Point3 p:object.toArray())if(candidate.map(new double[]{p.x,p.y,p.z})[2]<=0)front=false;
                    if(!front)continue;
                    Calib3d.projectPoints(object,rv.get(i),tv.get(i),k,distortion,projected);
                    double e=0;Point[] pp=projected.toArray();for(int j=0;j<4;j++)e+=Math.pow(pp[j].x-pts[j].x,2)+Math.pow(pp[j].y-pts[j].y,2);e=Math.sqrt(e/4);
                    if(e<bestError){second=best;secondError=bestError;best=candidate;bestError=e;}else if(e<secondError){second=candidate;secondError=e;}
                }finally{rot.release();projected.release();}
            }
            if(best==null||!Double.isFinite(bestError)||bestError>1.5)return null;
            boolean clear=second==null||best.angle(second)<Math.toRadians(10)||secondError-bestError>.35;
            // OpenCV camera: x right/y down/z forward. ARCore camera: x right/y up/z backward.
            float[]cm=new float[16];cameraWorld.toMatrix(cm,0);double[][]r=new double[3][3];double[]t=new double[3];
            for(int i=0;i<3;i++){t[i]=cm[12+i]*1000;for(int j=0;j<3;j++)r[i][j]=cm[j*4+i];}
            RigidPose cvToAr=new RigidPose(new double[][]{{1,0,0},{0,-1,0},{0,0,-1}},new double[3]);
            MarkerViewQuality quality=MarkerViewQuality.evaluate(best,pixels,focal[0],focal[1],bestError);
            return new Observation(captured,generation,new RigidPose(r,t).compose(cvToAr).compose(best),best,pixels,bestError,clear,quality);
        }finally{for(List<Mat> list:List.of(corners,rejected,rv,tv))for(Mat m:list)m.release();ids.release();k.release();distortion.release();imagePoints.release();object.release();}
    }
    static RigidPose fromMats(Mat r,Mat t){double[][]rr=new double[3][3];double[]tt=new double[3];for(int i=0;i<3;i++){tt[i]=t.get(i,0)[0];for(int j=0;j<3;j++)rr[i][j]=r.get(i,j)[0];}return new RigidPose(rr,tt);}
}
