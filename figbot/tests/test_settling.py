import unittest
from software.st3215_test.settling import settle_joint
from software.st3215_test.protocol import BusError


class Fake:
    def __init__(self,stuck=False):
        self.state='HOLDING';self.active=None;self.t=0.;self.stuck=stuck;self.writes=[]
        self.positions={i:1000 for i in range(1,7)};self.positions[2]=2434
        self.targets=self.positions.copy()
    def read_all(self):
        return {i:dict(position=p,torque=1,speed=0,moving=False) for i,p in self.positions.items()}
    def validate_rows(self,rows):pass
    def goal_verified(self,joint,target,**kw):
        self.writes.append((joint,target))
        if not self.stuck:self.positions[joint]=target+23
    def pause(self,*args,**kw):
        self.state='FAULT_HOLD' if kw.get('fault') else 'PAUSED_HOLD'
        if not kw.get('fault'):self.positions[2]+=6
        self.targets=self.positions.copy();return True
    def poll(self,fresh):return self.read_all()
    def resume_existing_hold(self,fresh):self.state='HOLDING'
    def sleep(self,seconds):self.t+=seconds


class SettlingTests(unittest.TestCase):
    def test_compensates_bias_then_verifies_original_physical_target(self):
        f=Fake();r=settle_joint(f,2,2405,(700,3200),lambda:True,clock=lambda:f.t,sleep=f.sleep)
        self.assertLessEqual(abs(r['actual']-2405),20)
        self.assertEqual(f.writes,[(2,2405),(2,2393),(2,2382)])
        self.assertEqual(f.state,'HOLDING')
    def test_stuck_joint_stops_without_unbounded_trim(self):
        f=Fake(True)
        with self.assertRaisesRegex(BusError,'did not converge'):
            settle_joint(f,2,2405,(700,3200),lambda:True,clock=lambda:f.t,sleep=f.sleep)
        self.assertEqual(len(f.writes),4);self.assertEqual(f.state,'FAULT_HOLD')
        self.assertTrue(all(abs(p-2405)<=36 for _,p in f.writes))
    def test_stale_camera_and_distant_target_prevent_writes(self):
        for target,fresh in [(2405,False),(2000,True)]:
            f=Fake()
            with self.assertRaises(BusError):
                settle_joint(f,2,target,(700,3200),lambda:fresh,clock=lambda:f.t,sleep=f.sleep)
            self.assertFalse(f.writes)
    def test_stop_mid_correction_latches_hold(self):
        f=Fake()
        with self.assertRaises(BusError):
            settle_joint(f,2,2405,(700,3200),lambda:True,stopped=lambda:f.t>.1,
                         clock=lambda:f.t,sleep=f.sleep)
        self.assertEqual(f.state,'FAULT_HOLD');self.assertEqual(len(f.writes),1)
    def test_other_joint_drift_stops_correction(self):
        f=Fake();original=f.goal_verified
        def displaced(*args,**kwargs):
            original(*args,**kwargs);f.positions[3]+=20
        f.goal_verified=displaced
        with self.assertRaisesRegex(BusError,'Another held joint'):
            settle_joint(f,2,2405,(700,3200),lambda:True,clock=lambda:f.t,sleep=f.sleep)
        self.assertEqual(f.state,'FAULT_HOLD');self.assertEqual(len(f.writes),1)
    def test_current_hold_cannot_escape_original_target_tolerance(self):
        f=Fake();original=f.pause
        def displaced(*args,**kwargs):
            result=original(*args,**kwargs)
            if not kwargs.get('fault'):f.positions[2]+=30
            return result
        f.pause=displaced
        with self.assertRaisesRegex(BusError,'original arrival tolerance'):
            settle_joint(f,2,2405,(700,3200),lambda:True,clock=lambda:f.t,sleep=f.sleep)
        self.assertEqual(f.state,'FAULT_HOLD')


if __name__=='__main__':unittest.main()
