import unittest
import numpy as np
from ai.training.handguided_routes import simplify,smooth_segments,blended_segments,build_routes


class HandguidedRoutesTests(unittest.TestCase):
    def test_excluded_spike_is_not_used_as_route_waypoint(self):
        t=np.arange(0,10,.1);q=np.tile(np.arange(6),(len(t),1)).astype(float)
        q[:,:5]+=t[:,None]*20;q[:,5]=900;q[np.argmin(abs(t-2)),1]=9000
        c=dict(start=0,close_start=3,close_end=4,release_start=7,release_end=8,end=9)
        plan=build_routes(t,q,dict(cycles=[c],open_count=1500,exclude_intervals=[[1.9,2.1]]))
        approach=next(s for s in plan['stages'] if s['phase']=='APPROACH_OPEN')
        self.assertLess(np.array(approach['positions'])[:,1].max(),1000)
        self.assertTrue(plan['excluded_intervals_bridged_as_unverified_candidates'])

    def test_blended_route_bounds_and_endpoints(self):
        p=np.array([[0.,0],[300,150],[600,400],[800,420]])
        t,q=blended_segments(p,300,600)
        v=np.diff(q,axis=0)/np.diff(t)[:,None]
        a=np.diff(v,axis=0)/((np.diff(t)[1:]+np.diff(t)[:-1])/2)[:,None]
        self.assertLessEqual(abs(v).max(),300.1)
        self.assertLessEqual(abs(a).max(),600.1)
        np.testing.assert_allclose(q[[0,-1]],p[[0,-1]],atol=1e-8)

    def test_simplification_preserves_turn_and_endpoints(self):
        p=np.array([[0.,0],[10,0],[20,0],[20,40],[20,50]])
        result=simplify(p,1)
        np.testing.assert_array_equal(result,[[0,0],[20,0],[20,50]])

    def test_quintic_limits_and_endpoints(self):
        t,q=smooth_segments(np.array([[0.,0],[600,200],[700,0]]),300,600,.005)
        velocity=np.diff(q,axis=0)/np.diff(t)[:,None]
        acceleration=np.diff(velocity,axis=0)/((np.diff(t)[1:]+np.diff(t)[:-1])/2)[:,None]
        self.assertLessEqual(abs(velocity).max(),300.01)
        self.assertLessEqual(abs(acceleration).max(),600.1)
        np.testing.assert_allclose(q[-1],[700,0])

    def test_approach_open_and_gripper_changes_only_at_rest(self):
        t=np.arange(0,10,.1);q=np.tile(np.arange(6),(len(t),1)).astype(float)
        q[:,:5]+=t[:,None]*20;q[:,5]=900
        c=dict(start=0,close_start=3,close_end=4,release_start=7,release_end=8,end=9)
        plan=build_routes(t,q,dict(cycles=[c],open_count=1500))
        stages=plan['stages']
        self.assertEqual(stages[0]['phase'],'OPEN_BEFORE_APPROACH')
        for stage in stages:
            x=np.array(stage['positions'])
            if stage['phase']=='APPROACH_OPEN':self.assertTrue(np.all(x[:,5]==1500))
            if stage['phase'] in ['OPEN_BEFORE_APPROACH','GRASP_AT_REST','RELEASE_AT_REST']:
                np.testing.assert_allclose(x[:,:5],np.broadcast_to(x[0,:5],x[:,:5].shape))
        self.assertFalse(plan['autonomous_replay_allowed'])


if __name__=='__main__':unittest.main()
