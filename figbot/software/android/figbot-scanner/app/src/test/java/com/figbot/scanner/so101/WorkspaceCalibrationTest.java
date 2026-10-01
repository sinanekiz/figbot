package com.figbot.scanner.so101;

import static org.junit.Assert.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.Test;

public class WorkspaceCalibrationTest {
    private final WorkspaceCalibration.Limits limits = new WorkspaceCalibration.Limits(2,4,.03,80,15,.5);
    private static double[] p(double x,double y,double z){return new double[]{x,y,z};}
    private static WorkspaceCalibration.Sample sample(String id,double x,double y,double z) {
        // Right-handed world→robot: robot X=world Z, Y=world X, Z=world Y, plus translation.
        return new WorkspaceCalibration.Sample(id,p(x,y,z),p(z*1000+10,x*1000-20,y*1000+30));
    }
    private List<WorkspaceCalibration.Sample> training() {
        return Arrays.asList(sample("a",0,0,0),sample("b",.2,0,0),sample("c",0,0,.2),sample("d",.2,0,.2));
    }
    private List<WorkspaceCalibration.Sample> held() {
        return Arrays.asList(sample("v1",.02,0,.02),sample("v2",.18,0,.02),sample("v3",.02,0,.18));
    }
    private WorkspaceCalibration validated() {
        return WorkspaceCalibration.fromData(training(),held(),limits);
    }
    @Test public void fitsPlanarRightHandedRotationAndMillimetres() {
        WorkspaceCalibration c=WorkspaceCalibration.fit(training(),limits);
        assertArrayEquals(p(60,100,70),c.toRobotMm(p(.12,.04,.05)),1e-8);
        assertTrue(c.fitResiduals().rmsMm<1e-8);assertFalse(c.isValidated());
        c.validateHeldOut(held());assertTrue(c.isValidated());
    }
    @Test public void fitsFull3DRotationWithIndependentChecks() {
        List<WorkspaceCalibration.Sample> data=new ArrayList<>(training());data.add(sample("high",.1,.15,.05));
        WorkspaceCalibration c=WorkspaceCalibration.fit(data,limits);
        c.validateHeldOut(held());assertArrayEquals(p(60,100,70),c.toRobotMm(p(.12,.04,.05)),1e-8);
    }
    @Test public void rejectsCollinearOrRepeatedPoints() {
        List<WorkspaceCalibration.Sample> line=Arrays.asList(sample("a",0,0,0),sample("b",.1,0,0),sample("c",.2,0,0),sample("d",.3,0,0));
        assertThrows(IllegalArgumentException.class,()->WorkspaceCalibration.fit(line,limits));
        List<WorkspaceCalibration.Sample> repeated=new ArrayList<>(training());repeated.set(3,sample("other",0,0,0));
        assertThrows(IllegalArgumentException.class,()->WorkspaceCalibration.fit(repeated,limits));
    }
    @Test public void rejectsScaleMismatchAndNonfiniteInputs() {
        List<WorkspaceCalibration.Sample> scaled=new ArrayList<>();
        for(WorkspaceCalibration.Sample s:training()) {
            double[] robot=s.robotMm();for(int i=0;i<3;i++)robot[i]*=1.1;
            scaled.add(new WorkspaceCalibration.Sample(s.id,s.worldMetres(),robot));
        }
        assertThrows(IllegalArgumentException.class,()->WorkspaceCalibration.fit(scaled,limits));
        assertThrows(IllegalArgumentException.class,()->new WorkspaceCalibration.Sample("nan",p(Double.NaN,0,0),p(0,0,0)));
    }
    @Test public void rejectsSpatialReflection() {
        double[][] points={p(0,0,0),p(.2,0,0),p(0,.2,0),p(0,0,.2)};
        List<WorkspaceCalibration.Sample> reflected=new ArrayList<>();
        for(int i=0;i<4;i++)reflected.add(new WorkspaceCalibration.Sample("p"+i,points[i],p(-points[i][0]*1000,points[i][1]*1000,points[i][2]*1000)));
        assertThrows(IllegalArgumentException.class,()->WorkspaceCalibration.fit(reflected,limits));
    }
    @Test public void validationRequiresHeldOutLocationsAndCoverage() {
        WorkspaceCalibration c=WorkspaceCalibration.fit(training(),limits);
        assertThrows(IllegalArgumentException.class,()->c.validateHeldOut(training().subList(0,3)));
        List<WorkspaceCalibration.Sample> tiny=Arrays.asList(sample("v1",.01,0,.01),sample("v2",.02,0,.01),sample("v3",.01,0,.02));
        assertThrows(IllegalArgumentException.class,()->c.validateHeldOut(tiny));assertFalse(c.isValidated());
    }
    @Test public void failedRevalidationRemovesPriorValidation() {
        WorkspaceCalibration c=validated();
        List<WorkspaceCalibration.Sample> bad=new ArrayList<>(held());
        WorkspaceCalibration.Sample s=bad.get(0);double[] robot=s.robotMm();robot[0]+=20;
        bad.set(0,new WorkspaceCalibration.Sample(s.id,s.worldMetres(),robot));
        assertThrows(IllegalArgumentException.class,()->c.validateHeldOut(bad));assertFalse(c.isValidated());
        assertTrue(c.heldOutSamples().isEmpty());
    }
    @Test public void serializedMeasurementsAreRecheckedAndDefensivelyCopied() {
        WorkspaceCalibration c=validated();
        WorkspaceCalibration copy=WorkspaceCalibration.fromData(c.fitSamples(),c.heldOutSamples(),c.limits());
        assertTrue(copy.isValidated());double[][] rotation=copy.rotation();rotation[0][0]=999;
        assertArrayEquals(c.toRobotMm(p(.1,.1,.1)),copy.toRobotMm(p(.1,.1,.1)),1e-8);
        double[] robot=c.fitSamples().get(0).robotMm();robot[0]=999;
        assertEquals(10,c.fitSamples().get(0).robotMm()[0],0);
    }
    @Test public void measuredHullRejectsExtrapolationButAcceptsBoundary() {
        WorkspaceCalibration c=validated();
        assertTrue(c.containsWorkspace(p(110,80,50)));assertTrue(c.containsWorkspace(p(10,-20,30)));
        assertFalse(c.containsWorkspace(p(211,80,30)));assertFalse(c.containsWorkspace(p(110,181,30)));
    }
    @Test public void groundPlaneAndMeasuredHeightGateGeneratePickTarget() {
        WorkspaceCalibration c=validated();
        List<double[]> ground=Arrays.asList(p(10,-20,30),p(210,-20,30),p(10,180,30),p(210,180,30));
        c.setGroundPlane(WorkspaceCalibration.GroundPlane.fit(ground,limits,5,40,8));
        assertArrayEquals(p(110,80,38),c.toPickTargetMm(p(.1,.02,.1)),1e-8);
        assertThrows(IllegalArgumentException.class,()->c.toPickTargetMm(p(.1,.1,.1)));
        assertThrows(IllegalArgumentException.class,()->c.toPickTargetMm(p(.3,.02,.1)));
    }
    @Test public void unvalidatedCalibrationCannotGeneratePickTarget() {
        WorkspaceCalibration c=WorkspaceCalibration.fit(training(),limits);
        assertThrows(IllegalStateException.class,()->c.toPickTargetMm(p(.1,0,.1)));
    }
    @Test public void slopedPlaneFitsAndDegenerateXYIsRejected() {
        List<double[]> ground=Arrays.asList(p(0,0,5),p(100,0,15),p(0,100,25),p(100,100,35));
        WorkspaceCalibration.GroundPlane plane=WorkspaceCalibration.GroundPlane.fit(ground,limits,0,50,10);
        assertEquals(20,plane.heightAt(50,50),1e-8);
        List<double[]> vertical=Arrays.asList(p(0,0,0),p(100,0,0),p(0,0,100));
        assertThrows(IllegalArgumentException.class,()->WorkspaceCalibration.GroundPlane.fit(vertical,limits,0,50,10));
    }
}
