package com.figbot.scanner.vision;
import java.util.*;
import org.junit.Test;
import static org.junit.Assert.*;
public class HandEyeRefinementTest {
    @Test public void cameraRelocationKeepsKnownToolTransformExactly(){
        RigidPose camera=pose(.3,-.2,.7,-170,-210,175),marker=pose(-.2,.4,.1,30,5,-60);
        List<MarkerCalibration.Sample> train=new ArrayList<>();
        for(int i=0;i<8;i++){
            RigidPose base=pose(.1*i,.04*i*i,.05*i,30*i,5*i,100-i);
            train.add(new MarkerCalibration.Sample(base,camera.inverse().compose(base).compose(marker)));
        }
        var fit=HandEyeRefinement.refineCamera(train,pose(.4,-.3,.8,-150,-200,190),marker);
        assertTrue(fit.baseCamera().distance(camera)<.01);
        assertTrue(fit.baseCamera().angle(camera)<1e-4);
        assertArrayEquals(marker.translation(),fit.toolMarker().translation(),0);
        assertEquals(0,marker.angle(fit.toolMarker()),1e-7);
    }
    private static RigidPose pose(double x,double y,double z,double tx,double ty,double tz){
        double cx=Math.cos(x),sx=Math.sin(x),cy=Math.cos(y),sy=Math.sin(y),cz=Math.cos(z),sz=Math.sin(z);
        return new RigidPose(new double[][]{{cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx},{sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx},{-sy,cy*sx,cy*cx}},new double[]{tx,ty,tz});
    }
    @Test public void recoversBothTransformsAndPredictsUnseenPoses(){
        RigidPose camera=pose(.3,-.2,.7,-170,-210,175),marker=pose(-.2,.4,.1,30,5,-60);
        List<MarkerCalibration.Sample> train=new ArrayList<>();Random random=new Random(391);
        List<RigidPose> all=new ArrayList<>();
        for(int i=0;i<12;i++)all.add(pose(random.nextDouble(),random.nextDouble(),random.nextDouble(),100+100*random.nextDouble(),-100*random.nextDouble(),50+100*random.nextDouble()));
        for(var base:all.subList(0,8))train.add(new MarkerCalibration.Sample(base,camera.inverse().compose(base).compose(marker)));
        var initialCamera=pose(.32,-.22,.72,-160,-220,180);
        var initialMarker=pose(-.22,.42,.12,40,0,-50);
        var fit=HandEyeRefinement.refine(train,initialCamera,initialMarker);
        for(var base:all.subList(8,12)){
            var seen=camera.inverse().compose(base).compose(marker);
            var predicted=fit.baseCamera().compose(seen).compose(fit.toolMarker().inverse());
            assertTrue(predicted.distance(base)<.01);
            assertTrue(predicted.angle(base)<1e-4);
        }
    }
    @Test public void exactFitRemainsExact(){
        RigidPose camera=pose(.1,.2,.3,10,20,30),marker=pose(.2,.1,.4,20,0,40);
        List<MarkerCalibration.Sample> samples=new ArrayList<>();
        for(int i=0;i<8;i++){
            RigidPose base=pose(.1*i,.04*i*i,.05*i,30*i,5*i,100-i);
            samples.add(new MarkerCalibration.Sample(base,camera.inverse().compose(base).compose(marker)));
        }
        var fit=HandEyeRefinement.refine(samples,camera,marker);
        assertTrue(fit.baseCamera().distance(camera)<1e-5);
        assertTrue(fit.toolMarker().distance(marker)<1e-5);
    }
}
