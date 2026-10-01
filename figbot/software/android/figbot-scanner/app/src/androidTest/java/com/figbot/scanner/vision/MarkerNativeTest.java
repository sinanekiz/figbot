package com.figbot.scanner.vision;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.google.ar.core.Pose;
import com.figbot.scanner.so101.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.opencv.android.OpenCVLoader;
import org.opencv.core.*;
import org.opencv.objdetect.Objdetect;
import org.opencv.imgproc.Imgproc;
import java.util.*;
import static org.junit.Assert.*;

/** Native numerical tests only: no activity, camera, USB, torque or motor access. */
@RunWith(AndroidJUnit4.class)
public class MarkerNativeTest {
    @Test public void rasterizedObliqueAndRolledMarkersRetainMetricPose(){
        ArucoTracker tracker=new ArucoTracker();int checked=0;double maxPosition=0,maxAngle=0;
        for(double tilt:new double[]{20,40,60,70})for(double roll:new double[]{0,45,90}){
            double a=Math.toRadians(tilt),b=Math.toRadians(roll);
            RigidPose facing=new RigidPose(new double[][]{{Math.cos(a),0,-Math.sin(a)},{0,-1,0},{-Math.sin(a),0,-Math.cos(a)}},new double[]{0,0,300});
            RigidPose rz=new RigidPose(new double[][]{{Math.cos(b),-Math.sin(b),0},{Math.sin(b),Math.cos(b),0},{0,0,1}},new double[3]);
            RigidPose expected=rz.compose(facing);
            Mat gray=render(expected,900);
            try{
                var seen=tracker.detectGray(gray,new float[]{900,900},new float[]{320,240},Pose.IDENTITY,100,1);
                assertNotNull("tilt="+tilt+" roll="+roll,seen);
                assertTrue(seen.quality().toString(),seen.usable());
                double mm=seen.cameraMarker().distance(expected),degrees=Math.toDegrees(seen.cameraMarker().angle(expected));
                maxPosition=Math.max(maxPosition,mm);maxAngle=Math.max(maxAngle,degrees);checked++;
                assertTrue("position "+mm+" tilt="+tilt+" roll="+roll,mm<3);
                assertTrue("angle "+degrees+" tilt="+tilt+" roll="+roll,degrees<3);
            }finally{gray.release();}
        }
        android.util.Log.i("FigbotAngleTest","raster cases="+checked+" max_mm="+maxPosition+" max_deg="+maxAngle);
    }
    private static Mat render(RigidPose camera,double focal){
        Mat marker=new Mat(),large=new Mat(),gray=new Mat();
        MatOfPoint2f source=new MatOfPoint2f(new Point(-.5,-.5),new Point(399.5,-.5),new Point(399.5,399.5),new Point(-.5,399.5));
        MatOfPoint2f target=new MatOfPoint2f();Mat homography=null;
        try{
            Objdetect.generateImageMarker(Objdetect.getPredefinedDictionary(Objdetect.DICT_4X4_50),0,400,marker,1);
            Point[] points=new Point[4];int i=0;
            for(double[] corner:new double[][]{{-18,18,0},{18,18,0},{18,-18,0},{-18,-18,0}}){
                double[] p=camera.map(corner);points[i++]=new Point(4*(focal*p[0]/p[2]+320),4*(focal*p[1]/p[2]+240));
            }
            target.fromArray(points);homography=Imgproc.getPerspectiveTransform(source,target);
            Imgproc.warpPerspective(marker,large,homography,new Size(2560,1920),Imgproc.INTER_LINEAR,Core.BORDER_CONSTANT,new Scalar(255));
            Imgproc.resize(large,gray,new Size(640,480),0,0,Imgproc.INTER_AREA);
            return gray;
        }catch(RuntimeException failure){gray.release();throw failure;}
        finally{marker.release();large.release();source.release();target.release();if(homography!=null)homography.release();}
    }
    @Test public void movedCameraWithKnownMountStillRequiresIndependentValidation(){
        RigidPose camera=pose(.3,-.4,.6,100,-200,300),mount=pose(.4,-.6,.8,30,12,-60);
        List<MarkerCalibration.Sample> samples=dataset(camera,mount);
        MarkerCalibration.Result result=MarkerCalibration.fit(samples,mount);
        assertTrue(result.baseWorld().distance(camera)<.01);
        assertTrue(result.toolMarker().distance(mount)<1e-9);
        var bad=samples.get(10);double[] t=bad.worldMarker().translation();t[0]+=35;
        samples.set(10,new MarkerCalibration.Sample(bad.baseTool(),new RigidPose(bad.worldMarker().rotation(),t)));
        assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fit(samples,mount));
    }
    @Test public void actualFoldedPoseWithPassiveRollHasObservableInwardScan(){
        ArmProfile profile=ArmProfile.unverifiedDefaults().withPassiveWristRoll();
        int[] seed={2022,767,3946,2738,1152,792};
        List<int[]> q=CalibrationScan.plan(profile,seed).poses();
        So101Kinematics kin=new So101Kinematics(profile);
        RigidPose bw=pose(.3,-.4,.6,100,-200,300),tm=pose(.4,-.6,.8,30,12,-60);
        List<MarkerCalibration.Sample> s=new ArrayList<>();
        for(int[] raw:q){RigidPose bt=RigidPose.fromMatrix(kin.forwardTransform(raw));s.add(new MarkerCalibration.Sample(bt,bw.inverse().compose(bt).compose(tm)));}
        assertTrue(MarkerCalibration.fit(s).heldMaxMm()<.01);
    }
    @Before public void load(){assertTrue(OpenCVLoader.initLocal());}
    private static RigidPose pose(double ax,double ay,double az,double x,double y,double z){
        RigidPose rx=new RigidPose(new double[][]{{1,0,0},{0,Math.cos(ax),-Math.sin(ax)},{0,Math.sin(ax),Math.cos(ax)}},new double[]{x,y,z});
        RigidPose ry=new RigidPose(new double[][]{{Math.cos(ay),0,Math.sin(ay)},{0,1,0},{-Math.sin(ay),0,Math.cos(ay)}},new double[3]);
        RigidPose rz=new RigidPose(new double[][]{{Math.cos(az),-Math.sin(az),0},{Math.sin(az),Math.cos(az),0},{0,0,1}},new double[3]);
        return rx.compose(ry).compose(rz);
    }
    private static List<MarkerCalibration.Sample> dataset(RigidPose bw,RigidPose tm){
        List<MarkerCalibration.Sample>s=new ArrayList<>();Random r=new Random(314159);
        for(int i=0;i<12;i++){
            RigidPose bt=pose(r.nextDouble(),r.nextDouble(),r.nextDouble(),r.nextDouble()*200,r.nextDouble()*200,r.nextDouble()*200);
            s.add(new MarkerCalibration.Sample(bt,bw.inverse().compose(bt).compose(tm)));
        }return s;
    }
    @Test public void solvesCameraAndUnknownToolOffsetWithIndependentValidation(){
        RigidPose bw=pose(.3,-.4,.6,100,-200,300),tm=pose(.4,-.6,.8,30,12,-60);
        MarkerCalibration.Result result=MarkerCalibration.fit(dataset(bw,tm));
        assertTrue(result.baseWorld().distance(bw)<.001);assertTrue(result.baseWorld().angle(bw)<.001);
        assertTrue(result.toolMarker().distance(tm)<.001);assertTrue(result.heldMaxMm()<.001);
    }
    @Test public void badHeldOutAndDegenerateDataCannotUnlock(){
        List<MarkerCalibration.Sample>s=dataset(RigidPose.identity(),pose(0,0,0,20,10,30));
        MarkerCalibration.Sample a=s.get(10);double[]t=a.worldMarker().translation();t[0]+=35;
        s.set(10,new MarkerCalibration.Sample(a.baseTool(),new RigidPose(a.worldMarker().rotation(),t)));
        assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fit(s));
        assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fit(Collections.nCopies(12,s.get(0))));
    }
    @Test public void printedMarkerProducesMetricPoseAndCorrectArAxes(){
        Mat marker=new Mat(),gray=new Mat(800,800,CvType.CV_8UC1,new Scalar(255));
        Mat roi=gray.submat(100,700,100,700);
        try{
            Objdetect.generateImageMarker(Objdetect.getPredefinedDictionary(Objdetect.DICT_4X4_50),0,600,marker,1);
            marker.copyTo(roi);
            ArucoTracker.Observation o=new ArucoTracker().detectGray(gray,new float[]{1000,1000},new float[]{400,400},Pose.IDENTITY,100,1);
            assertNotNull(o);assertEquals(60,o.cameraMarker().translation()[2],.5);
            assertEquals(-60,o.worldMarker().translation()[2],.5);
            assertTrue(o.reprojectionPx()<1.5);
        }finally{roi.release();marker.release();gray.release();}
    }
    @Test public void stationaryFirstFrameHasMetricScaleAtThirtyCentimetres(){
        // 36 mm marker, fx=1000 px, 120 px side => z=300 mm. No AR tracking,
        // motion history, robot encoder or camera/base fit enters the solver.
        Mat marker=new Mat(),gray=new Mat(800,800,CvType.CV_8UC1,new Scalar(255));
        Mat roi=gray.submat(340,460,340,460);
        try{
            Objdetect.generateImageMarker(Objdetect.getPredefinedDictionary(Objdetect.DICT_4X4_50),0,120,marker,1);
            marker.copyTo(roi);
            ArucoTracker.Observation o=new ArucoTracker().detectGray(gray,new float[]{1000,1000},new float[]{400,400},Pose.IDENTITY,100,1);
            assertNotNull(o);
            assertEquals(300,o.cameraMarker().translation()[2],3);
            assertEquals(300,o.cameraMarker().distance(RigidPose.identity()),3);
        }finally{roi.release();marker.release();gray.release();}
    }
    @Test public void plannedScanCanObserveBothTransforms(){
        ArmProfile profile=ArmProfile.unverifiedDefaults().withRecordedSessionValidation("native-test");
        int[] seed={2600,1800,3100,2300,3129,900};
        List<int[]>q=CalibrationScan.poses(profile,seed);So101Kinematics kin=new So101Kinematics(profile);
        RigidPose bw=pose(.3,-.4,.6,100,-200,300),tm=pose(.4,-.6,.8,30,12,-60);
        List<MarkerCalibration.Sample>s=new ArrayList<>();
        for(int[] raw:q){RigidPose bt=RigidPose.fromMatrix(kin.forwardTransform(raw));s.add(new MarkerCalibration.Sample(bt,bw.inverse().compose(bt).compose(tm)));}
        assertTrue(MarkerCalibration.fit(s).heldMaxMm()<.01);
    }
}
