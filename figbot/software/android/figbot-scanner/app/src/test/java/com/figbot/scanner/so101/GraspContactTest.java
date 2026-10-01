package com.figbot.scanner.so101;
import org.junit.Test;
import static org.junit.Assert.*;
public class GraspContactTest {
    @Test public void sustainedCurrentAndStallAreBothRequired(){
        for(int[] sample:new int[][]{{1000,980,20,15},{1000,980,0,0},{1000,998,0,15}}){
            var c=new GraspContact(0);for(int i=0;i<20;i++)assertFalse(c.observe(i*20_000_000L,sample[0],sample[1],sample[2],sample[3]));
        }
        var c=new GraspContact(0);for(int i=0;i<9;i++)assertFalse(c.observe(i*20_000_000L,1000,980,0,12));
        assertTrue(c.observe(180_000_000L,1000,980,0,12));
    }
    @Test public void oneSpikeOrMissingSamplesCannotConfirmContact(){
        var c=new GraspContact(0);assertFalse(c.observe(0,1000,980,0,20));
        assertFalse(c.observe(20_000_000L,1000,980,0,0));
        assertFalse(c.observe(200_000_000L,1000,980,0,20));
        assertFalse(c.observe(500_000_000L,1000,980,0,20));
    }
    @Test public void lightGraspEvidenceCanRemainUnverified(){
        var c=new GraspContact(0);
        for(int i=0;i<30;i++)assertFalse(c.observe(i*20_000_000L,787,780,0,3));
        // False is insufficient evidence, not an empty-gripper classification.
    }
    @Test public void contactRequiresRiseAboveExistingJawCurrent(){
        var c=new GraspContact(10);
        for(int i=0;i<20;i++)assertFalse(c.observe(i*20_000_000L,1000,980,0,15));
        for(int i=20;i<29;i++)assertFalse(c.observe(i*20_000_000L,1000,980,0,16));
        assertTrue(c.observe(580_000_000L,1000,980,0,16));
    }
}
