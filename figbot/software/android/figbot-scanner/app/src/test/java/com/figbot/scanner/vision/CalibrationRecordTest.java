package com.figbot.scanner.vision;
import org.junit.Test;
import static org.junit.Assert.*;
public class CalibrationRecordTest {
    private MarkerCalibration.Result sample(){return new MarkerCalibration.Result(RigidPose.identity(),new RigidPose(RigidPose.identity().rotation(),new double[]{10,20,30}),2,3.4,7);}
    @Test public void restartRoundTripPreservesBothTransformsAndErrors()throws Exception{
        var original=sample();var restored=CalibrationRecord.decode(CalibrationRecord.encode(original,"setup"),"setup");
        assertEquals(0,original.toolMarker().distance(restored.toolMarker()),0);
        assertEquals(0,original.baseWorld().angle(restored.baseWorld()),0);
        assertEquals(3.4,restored.heldRmsMm(),0);
    }
    @Test(expected=java.io.IOException.class)public void changedEncoderMapCannotRestore()throws Exception{CalibrationRecord.decode(CalibrationRecord.encode(sample(),"old"),"new");}
    @Test(expected=java.io.IOException.class)public void truncatedRecordCannotRestore()throws Exception{CalibrationRecord.decode("AAAA","setup");}
}
