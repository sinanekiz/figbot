package com.figbot.scanner.so101;

import org.junit.Test;
import java.util.List;
import static org.junit.Assert.*;

/** Adaptive follow decisions: orange 1 Hz re-aim, green precise leg, feedback arrival. */
public class FollowBrainTest {

    private static FollowBrain.Detection det(double x, double y, double z, double conf, long t) {
        return new FollowBrain.Detection(new double[]{x, y, z}, conf, t);
    }

    @Test public void orangeRetargetsAtMostOncePerSecond() {
        FollowBrain brain = FollowBrain.standard();
        brain.arm(0);
        long t = 1_000_000_000L;
        // First tick: arm holding far away, camera moving -> immediate first re-aim.
        FollowBrain.Decision first = brain.tick(t, FollowBrain.CameraState.MOVING,
                List.of(det(300, 0, 10, .8, t)), true, false, new double[]{0, 0, 0});
        assertEquals(FollowBrain.DecisionType.RETARGET, first.type());
        assertArrayEquals(new double[]{300, 0, 10}, first.targetMm(), 1e-9);
        brain.confirmPlanned(first.targetMm(), t);
        // Same second, target barely moved: no new command.
        assertEquals(FollowBrain.DecisionType.NONE, brain.tick(t + 400_000_000L,
                FollowBrain.CameraState.MOVING, List.of(det(302, 0, 10, .8, t)),
                true, true, new double[]{50, 0, 0}).type());
        // Next second, target moved 40 mm while the camera keeps moving: re-aim.
        FollowBrain.Decision again = brain.tick(t + 1_100_000_000L,
                FollowBrain.CameraState.MOVING, List.of(det(340, 0, 10, .8, t)),
                true, true, new double[]{80, 0, 0});
        assertEquals(FollowBrain.DecisionType.RETARGET, again.type());
        assertArrayEquals(new double[]{340, 0, 10}, again.targetMm(), 1e-9);
    }

    @Test public void greenPerformsSinglePreciseLegThenArrives() {
        FollowBrain brain = FollowBrain.standard();
        brain.arm(0);
        long t = 2_000_000_000L;
        FollowBrain.Decision move = brain.tick(t, FollowBrain.CameraState.STABLE,
                List.of(det(250, 60, 10, .9, t)), true, false, new double[]{100, 20, 40});
        assertEquals(FollowBrain.DecisionType.PRECISE_MOVE, move.type());
        brain.confirmPlanned(move.targetMm(), t);
        // While the leg is in flight toward the same settled target: no new commands.
        assertEquals(FollowBrain.DecisionType.NONE, brain.tick(t + 200_000_000L,
                FollowBrain.CameraState.STABLE, List.of(det(250, 60, 10, .9, t)),
                false, true, new double[]{180, 45, 25}).type());
        // Holding within 15 mm of the target: announce arrival exactly once.
        double[] gripper = {245, 62, 12};
        FollowBrain.Decision arrived = brain.tick(t + 3_000_000_000L,
                FollowBrain.CameraState.STABLE, List.of(det(250, 60, 10, .9, t)),
                true, false, gripper);
        assertEquals(FollowBrain.DecisionType.ARRIVED, arrived.type());
        assertEquals(FollowBrain.DecisionType.NONE, brain.tick(t + 3_200_000_000L,
                FollowBrain.CameraState.STABLE, List.of(det(250, 60, 10, .9, t)),
                true, false, gripper).type());
    }

    @Test public void arrivedReArmsWhenTargetMovesAgain() {
        FollowBrain brain = FollowBrain.standard();
        brain.arm(0);
        long t = 3_000_000_000L;
        double[] gripper = {250, 60, 12};
        brain.tick(t, FollowBrain.CameraState.STABLE, List.of(det(250, 60, 10, .9, t)), true, false, gripper);
        // The first green tick announces PRECISE_MOVE (far), then ARRIVED once holding nearby.
        FollowBrain.Decision far = brain.tick(t + 100_000_000L, FollowBrain.CameraState.STABLE,
                List.of(det(250, 60, 10, .9, t)), true, false, new double[]{150, 40, 30});
        assertEquals(FollowBrain.DecisionType.PRECISE_MOVE, far.type());
        brain.confirmPlanned(far.targetMm(), t);
        assertEquals(FollowBrain.DecisionType.ARRIVED, brain.tick(t + 4_000_000_000L,
                FollowBrain.CameraState.STABLE, List.of(det(250, 60, 10, .9, t)), true, false, gripper).type());
        // The fig is moved 30 mm: the brain must re-aim precisely again (arrival resets).
        FollowBrain.Decision moved = brain.tick(t + 5_000_000_000L,
                FollowBrain.CameraState.STABLE, List.of(det(280, 60, 10, .9, t)), true, false, gripper);
        assertEquals(FollowBrain.DecisionType.PRECISE_MOVE, moved.type());
        assertArrayEquals(new double[]{280, 60, 10}, moved.targetMm(), 1e-9);
    }

    @Test public void associationKeepsSameFigAndReacquiresWhenLost() {
        FollowBrain brain = FollowBrain.standard();
        brain.arm(0);
        long t = 4_000_000_000L;
        // Nothing followed yet: the highest-confidence detection starts the track.
        FollowBrain.Decision first = brain.tick(t, FollowBrain.CameraState.MOVING,
                List.of(det(300, 20, 10, .6, t), det(500, 200, 10, .95, t)),
                true, false, new double[]{0, 0, 0});
        assertArrayEquals(new double[]{500, 200, 10}, first.targetMm(), 1e-9);
        brain.confirmPlanned(first.targetMm(), t);
        // The followed fig drifts (520,215) while a far, higher-confidence second fig
        // appears: association must keep the same fig, not jump to the new one.
        FollowBrain.Decision keep = brain.tick(t + 1_100_000_000L, FollowBrain.CameraState.MOVING,
                List.of(det(520, 215, 10, .6, t), det(300, 20, 10, .95, t)),
                true, true, new double[]{100, 60, 30});
        assertEquals(FollowBrain.DecisionType.RETARGET, keep.type());
        assertArrayEquals(new double[]{520, 215, 10}, keep.targetMm(), 1e-9);
        // Detections vanish entirely: report the loss, then reacquire on return.
        assertEquals(FollowBrain.DecisionType.LOST_TARGET, brain.tick(t + 2_000_000_000L,
                FollowBrain.CameraState.MOVING, List.of(), true, true, new double[]{100, 60, 30}).type());
        FollowBrain.Decision back = brain.tick(t + 3_000_000_000L, FollowBrain.CameraState.STABLE,
                List.of(det(250, 80, 10, .7, t)), true, false, new double[]{100, 60, 30});
        assertEquals(FollowBrain.DecisionType.LOST_TARGET, back.type());
        // Only explicit re-arm may pick a different fig.
        brain.arm(t+4_000_000_000L);
        assertEquals(FollowBrain.DecisionType.PRECISE_MOVE,brain.tick(t+4_000_000_000L,FollowBrain.CameraState.STABLE,
                List.of(det(250,80,10,.7,t)),true,false,new double[]{100,60,30}).type());
    }

    @Test public void occludedFigCannotJumpToVisibleNeighbor(){
        FollowBrain brain=FollowBrain.standard();brain.arm(0);
        brain.tick(1,FollowBrain.CameraState.STABLE,List.of(det(200,-140,10,.9,1)),true,false,new double[]{0,0,100});
        var decision=brain.tick(2,FollowBrain.CameraState.STABLE,List.of(det(245,-69,10,.99,2)),false,true,new double[]{190,-140,25});
        assertEquals(FollowBrain.DecisionType.LOST_TARGET,decision.type());
        assertArrayEquals(new double[]{200,-140,10},brain.followTarget(),0);
    }
    @Test public void nearestAssociationBeatsHigherConfidenceNeighbor(){
        FollowBrain brain=FollowBrain.standard();brain.arm(0);
        brain.tick(1,FollowBrain.CameraState.STABLE,List.of(det(200,-140,10,.9,1)),true,false,new double[]{0,0,100});
        brain.tick(2,FollowBrain.CameraState.STABLE,List.of(det(201,-140,10,.8,2),det(240,-140,10,.99,2)),true,false,new double[]{0,0,100});
        assertArrayEquals(new double[]{201,-140,10},brain.followTarget(),0);
    }

    @Test public void disarmedBrainStaysSilent() {
        FollowBrain brain = FollowBrain.standard();
        brain.arm(0);
        brain.disarm();
        assertEquals(FollowBrain.DecisionType.NONE, brain.tick(1_000_000_000L,
                FollowBrain.CameraState.STABLE, List.of(det(250, 60, 10, .9, 0)),
                true, false, new double[]{0, 0, 0}).type());
        assertFalse(brain.isFollowing());
    }
}
