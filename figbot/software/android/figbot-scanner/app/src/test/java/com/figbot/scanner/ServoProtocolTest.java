package com.figbot.scanner;
import org.junit.Test;
import static org.junit.Assert.*;

public class ServoProtocolTest {
    @Test public void liveDragReplacesOldTargetsBeforeEachSendAndStopClearsTail(){
        MotionQueue q=new MotionQueue();q.arm(1,true);q.next();
        ServoProtocol p=ready(4095,4095);
        for(int sample=0;sample<=180;sample++){
            q.move(1,sample,360,false,500);
            assertEquals(1,q.size());
            if(sample%10==0){
                MotionQueue.Command c=q.next();
                assertEquals("S1,"+sample+",360,500,2500\n",p.position(c.channel(),c.angle(),c.speed(),c.wide(),c.pairMin()));
            }
        }
        assertEquals(0,q.size());
        q.move(1,80,360,false,500);q.move(3,100,360,true,500);q.move(1,70,360,false,500);
        assertEquals(2,q.size());assertEquals(3,q.next().channel());assertEquals(Integer.valueOf(70),q.next().angle());
        q.move(1,60,360,false,500);q.stop();q.move(1,50,360,false,500);
        assertEquals(0,q.size());assertTrue(q.takeStop());
        q.move(1,40,360,false,500);assertNull(q.next());
    }
    @Test public void defaultRangeAndSpeedProduceWideCommandsForEveryJoint(){
        ServoProtocol p=ready(4095,4095);
        MotionQueue q=new MotionQueue();q.prepareSession();
        while(q.size()>0)q.next();
        for(int ch:new int[]{0,1,3,4,5,6,7,9,10,11}){
            q.move(ch,90,ServoProtocol.DEFAULT_COMMAND_SPEED,!ServoProtocol.paired(ch)&&ServoProtocol.DEFAULT_WIDE_RANGE,ServoProtocol.DEFAULT_PAIR_MIN_US);
            MotionQueue.Command c=q.next();
            assertEquals((ServoProtocol.paired(ch)?"S":"P")+ch+",90,360,500,2500\n",p.position(c.channel(),c.angle(),c.speed(),c.wide(),c.pairMin()));
        }
        p=ready(4095,0);
        ServoProtocol fresh=p;
        assertThrows(IllegalStateException.class,()->fresh.position(1,0,ServoProtocol.DEFAULT_COMMAND_SPEED,false,ServoProtocol.DEFAULT_PAIR_MIN_US));
    }
    @Test public void sessionPreparationOnlyArmsAndStopWins(){
        MotionQueue q=new MotionQueue();q.prepareSession();assertEquals(10,q.size());
        int mask=0;
        while(q.size()>0){MotionQueue.Command c=q.next();assertNull(c.angle());assertTrue(c.enable());mask|=ServoProtocol.mask(c.channel());}
        assertEquals(4095,mask);
        q.stop();q.prepareSession();assertEquals(0,q.size());assertTrue(q.takeStop());
    }
    @Test public void calibrationRangeTravelsWithCoalescedTarget(){
        MotionQueue q=new MotionQueue();q.arm(1,true);q.move(1,90,360,false,1000);q.move(1,90,360,false,900);
        assertEquals(2,q.size());q.next();assertEquals(900,q.next().pairMin());
        ServoProtocol p=ready(390,0);
        for(int ch:new int[]{1,7})for(int lo=500;lo<=1000;lo+=100){
            assertEquals("S"+ch+",90,360,"+lo+","+(3000-lo)+"\n",p.position(ch,90,360,false,lo));
            assertTrue(p.receive("PAIR "+ch+",90,360,"+lo+","+(3000-lo)));
        }
        assertThrows(IllegalArgumentException.class,()->p.position(1,90,360,false,750));
        assertThrows(IllegalArgumentException.class,()->p.receive("PAIR 1,90,360,900,2000"));
        assertThrows(RuntimeException.class,()->p.receive("STATUS4 0,0"));
        assertThrows(RuntimeException.class,()->p.receive("FIGBOT_PCA9685_V4"));
    }
    @Test public void maximumSpeedCommandsAndAcknowledgementsAcrossBothArms(){
        ServoProtocol p=ready(4095,4095);
        for(int ch:new int[]{1,7}) {
            assertEquals("S"+ch+",120,360,1000,2000\n",p.position(ch,120,360,false));
            assertTrue(p.receive("PAIR "+ch+",120,360,1000,2000"));
            assertEquals(120,p.angle[ch]);assertEquals(60,p.angle[ch+1]);
            assertThrows(IllegalArgumentException.class,()->p.position(ch,120,361,false));
        }
        for(int ch:new int[]{0,3,4,5,6,9,10,11}) {
            assertEquals("P"+ch+",120,360,1000,2000\n",p.position(ch,120,360,false));
            assertTrue(p.receive("ACK "+ch+",120,360,1000,2000"));
            assertThrows(IllegalArgumentException.class,()->p.position(ch,120,361,false));
        }
        assertThrows(IllegalArgumentException.class,()->p.receive("ACK 0,120,361,1000,2000"));
    }
    private ServoProtocol ready(int en,int active){ServoProtocol p=new ServoProtocol();p.receive("STATUS5 "+en+","+active);return p;}
    @Test public void connectAndArmDoNotMove(){
        ServoProtocol p=ready(0,0);assertEquals("E1\n",p.arm(1,true));assertEquals(0,p.active);
        assertThrows(IllegalStateException.class,()->p.position(1,90,30,false));
    }
    @Test public void bothPairsRequireCentreAndRejectIndividualOrWide(){
        ServoProtocol p=ready(390,0);
        for(int ch:new int[]{1,7}) {
            assertThrows(IllegalStateException.class,()->p.position(ch,95,30,false));
            assertEquals("S"+ch+",90,180,1000,2000\n",p.position(ch,90,180,false));
            assertThrows(IllegalArgumentException.class,()->p.position(ch+1,90,30,false));
            assertThrows(IllegalArgumentException.class,()->p.position(ch,90,30,true));
            assertThrows(IllegalArgumentException.class,()->p.position(ch,90,361,false));
        }
    }
    @Test public void acknowledgementIsComplementaryButNotFeedback(){
        ServoProtocol p=ready(390,390);p.receive("PAIR 7,120,180,1000,2000");
        assertEquals(120,p.angle[7]);assertEquals(60,p.angle[8]);assertTrue(p.acknowledged[8]);
        p.receive("OFF WATCHDOG");assertEquals(0,p.enabled);assertEquals(0,p.active);
    }
    @Test public void malformedOrOldDataCannotAuthorizeMotion(){
        ServoProtocol p=new ServoProtocol();
        for(String line:new String[]{"STATUS2 0,0","STATUS3 0,0","FIGBOT_PCA9685_V3","FIGBOT_PCA9685_V2","STATUS5 2,2","STATUS5 0,1","STATUS5 4096,0","STATUS5 -1,0","PAIR 1,180,361,1000,2000","ACK 2,90,30,1000,2000","ACK 0,90,30,0,9999"})
            assertThrows(RuntimeException.class,()->p.receive(line));
        assertFalse(p.ready);assertFalse(p.receive("random bytes"));
    }
    @Test public void individualChannelsAndBounds(){
        ServoProtocol p=ready(4095,4095);
        assertEquals("P0,180,180,500,2500\n",p.position(0,180,180,true));
        assertEquals("P11,0,10,1000,2000\n",p.position(11,0,10,false));
        assertThrows(IllegalArgumentException.class,()->p.position(12,90,30,false));
        assertThrows(IllegalArgumentException.class,()->p.position(0,181,30,false));
        assertThrows(IllegalArgumentException.class,()->p.position(0,90,0,false));
    }
    @Test public void stopFlushesMotionAndNeverAutomaticallyRearms(){
        MotionQueue q=new MotionQueue();q.move(0,90,30,false);assertEquals(0,q.size());
        q.arm(0,true);q.move(0,91,30,false);q.move(0,92,30,false);assertEquals(2,q.size());
        q.stop();q.move(0,180,180,false);q.arm(0,true);assertEquals(0,q.size());
        assertTrue(q.takeStop());q.move(0,180,180,false);assertEquals(0,q.size());
        q.arm(0,true);assertEquals(1,q.size());q.clear();assertEquals(0,q.size());
    }
    @Test public void disableDropsPendingMovesForChannel(){
        MotionQueue q=new MotionQueue();q.arm(1,true);q.move(1,120,180,false);q.arm(1,false);
        assertEquals(1,q.size());assertFalse(q.next().enable());
    }
}
