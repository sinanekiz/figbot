package com.figbot.scanner.so101;
import org.junit.Test;
import java.util.List;
import static org.junit.Assert.*;
public class PickEvidenceTest {
    final PickEvidence.Basket basket=new PickEvidence.Basket(200,0,40,40,100);
    @Test public void disappearingFigIsUnknownNotSuccess(){
        PickEvidence p=new PickEvidence(basket,20,15,List.of());p.released(1_000_000_000L);
        assertEquals(PickEvidence.Outcome.UNKNOWN,p.observe(3_100_000_000L,3_100_000_000L,List.of(),new double[]{200,0,80},false,0));
    }
    @Test public void carryAndNewBasketObjectOnDistinctFramesAreRequired(){
        PickEvidence p=new PickEvidence(basket,20,15,List.of());double[]tip={100,0,60};
        p.observe(100,100,List.of(tip),tip,true,0);p.observe(100,101,List.of(tip),tip,true,0);
        assertFalse(p.carriedConfirmed());p.observe(200,200,List.of(tip),tip,true,0);assertTrue(p.carriedConfirmed());p.released(300);
        assertEquals(PickEvidence.Outcome.PENDING,p.observe(400,400,List.of(new double[]{200,0,70}),tip,false,0));
        assertEquals(PickEvidence.Outcome.CONFIRMED,p.observe(500,500,List.of(new double[]{200,0,70}),tip,false,0));
    }
    @Test public void ExistingBasketFruitDoesNotCountAsNewDeposit(){
        double[]old={200,0,70},tip={100,0,60};PickEvidence p=new PickEvidence(basket,20,15,List.of(old));
        p.observe(100,100,List.of(tip),tip,true,0);p.observe(200,200,List.of(tip),tip,true,0);p.released(300);
        p.observe(400,400,List.of(old),tip,false,0);assertEquals(PickEvidence.Outcome.PENDING,p.observe(500,500,List.of(old),tip,false,0));
    }
    @Test public void staleOrGroundLevelFruitCannotConfirmCarry(){
        double[]tip={100,0,10};PickEvidence p=new PickEvidence(basket,20,15,List.of());
        p.observe(1,1_000_000_000L,List.of(tip),tip,true,0);p.observe(2_000_000_000L,2_000_000_000L,List.of(tip),tip,true,0);
        assertFalse(p.carriedConfirmed());
    }
}
