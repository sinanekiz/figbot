package com.figbot.scanner.vision;
import org.junit.Test;
import static org.junit.Assert.*;
public class CalibrationReuseTest {
    private final CalibrationReuse check=new CalibrationReuse();
    private final MarkerCalibration.Result saved=new MarkerCalibration.Result(RigidPose.identity(),RigidPose.identity(),1,2,3);
    private CalibrationReuse.State sample(long ms,double shift){return check.observe(saved,RigidPose.identity(),new RigidPose(RigidPose.identity().rotation(),new double[]{shift,0,0}),ms*1_000_000L,ms*1_000_000L+20_000_000L);}
    @Test public void unchangedSetupNeedsSeveralFreshFrames(){
        assertEquals(CalibrationReuse.State.WAIT,sample(1000,0));
        assertEquals(CalibrationReuse.State.WAIT,sample(1200,0));
        assertEquals(CalibrationReuse.State.WAIT,sample(1400,0));
        assertEquals(CalibrationReuse.State.WAIT,sample(1600,0));
        sample(1700,0);sample(1800,0);
        assertEquals(CalibrationReuse.State.MATCH,sample(1900,0));
    }
    @Test public void movedPhoneRejectedWithoutRewritingSavedTransform(){
        sample(1000,30);sample(1100,30);sample(1200,30);
        assertEquals(CalibrationReuse.State.WAIT,sample(1300,30));
        sample(1400,30);sample(1500,30);
        assertEquals(CalibrationReuse.State.MISMATCH,sample(1600,30));
    }
    @Test public void repeatedImageCannotValidate(){
        for(int i=0;i<10;i++)assertEquals(CalibrationReuse.State.WAIT,sample(1000,0));
    }
    @Test public void gapRestartsEvidenceWindow(){
        sample(1000,0);sample(1200,0);sample(1400,0);
        assertEquals(CalibrationReuse.State.WAIT,sample(2000,0));
    }
    @Test public void singleOutlierDoesNotRejectSmallResiduals(){
        for(int i=0;i<6;i++)assertEquals(CalibrationReuse.State.WAIT,sample(1000+i*100,i==3?60:8));
        assertEquals(CalibrationReuse.State.MATCH,sample(1600,8));
    }
    @Test public void aSingleGoodImageCannotHidePersistentDisplacement(){
        for(int i=0;i<6;i++)sample(1000+i*100,i==3?0:40);
        assertEquals(CalibrationReuse.State.MISMATCH,sample(1600,40));
    }
    @Test public void returningToSavedMountRecoversWithoutCalibrationOrReset(){
        for(int i=0;i<9;i++)sample(1000+i*100,40);
        CalibrationReuse.State result=null;
        for(int i=0;i<9;i++)result=sample(2000+i*100,4);
        assertEquals(CalibrationReuse.State.MATCH,result);
    }
    @Test public void uncertainMixedWindowWaits(){
        for(int i=0;i<12;i++)assertEquals(CalibrationReuse.State.WAIT,sample(1000+i*100,i%2==0?0:35));
    }
    @Test public void commonWorldMotionLeavesRelativeCalibrationUnchanged(){
        RigidPose worldBase=new RigidPose(new double[][]{{0,-1,0},{1,0,0},{0,0,1}},new double[]{800,400,30});
        RigidPose baseCamera=new RigidPose(RigidPose.identity().rotation(),new double[]{100,20,300});
        RigidPose baseTool=new RigidPose(RigidPose.identity().rotation(),new double[]{250,60,80});
        MarkerCalibration.Result calibration=new MarkerCalibration.Result(baseCamera,RigidPose.identity(),1,2,3);
        RigidPose cameraMarker=worldBase.compose(baseCamera).inverse().compose(worldBase.compose(baseTool));
        CalibrationReuse.State result=null;
        for(int i=0;i<9;i++){long t=(1000+i*100)*1_000_000L;result=check.observe(calibration,baseTool,cameraMarker,t,t+20_000_000L);}
        assertEquals(CalibrationReuse.State.MATCH,result);
    }
}
