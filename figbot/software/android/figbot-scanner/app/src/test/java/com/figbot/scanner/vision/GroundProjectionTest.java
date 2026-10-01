package com.figbot.scanner.vision;
import org.junit.Test;
import static org.junit.Assert.*;
public class GroundProjectionTest {
    private final RigidPose down=new RigidPose(new double[][]{{1,0,0},{0,-1,0},{0,0,-1}},new double[]{100,200,300});
    @Test public void contactUsesMeasuredPlaneAndCameraTransform(){
        assertArrayEquals(new double[]{160,170,0},GroundProjection.contact(down,420,290,500,500,320,240,0),1e-6);
        assertArrayEquals(new double[]{140,180,100},GroundProjection.contact(down,420,290,500,500,320,240,100),1e-6);
    }
    @Test(expected=IllegalArgumentException.class) public void upwardRayRejected(){GroundProjection.contact(RigidPose.identity(),0,0,500,500,0,0,0);}
    @Test(expected=IllegalArgumentException.class) public void planeBehindCameraRejected(){GroundProjection.contact(down,0,0,500,500,0,0,400);}
    @Test(expected=IllegalArgumentException.class) public void invalidPixelRejected(){GroundProjection.contact(down,Double.NaN,0,500,500,0,0,0);}
}
