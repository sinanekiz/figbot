import unittest
from software.st3215_test.supervised_grasp import close_jaw
from software.st3215_test.protocol import BusError


class Fake:
    def __init__(self, contact=None):
        self.state='HOLDING'; self.t=0.; self.targets={}; self.writes=[]; self.contact=contact
        self.positions={i:1500 for i in range(1,7)}; self.positions[6]=1556
    def read_all(self):
        self.rows={i:dict(position=p,torque=1,speed=0,moving=False,current_raw=0)
                   for i,p in self.positions.items()}; return self.rows
    def validate_rows(self,rows): pass
    def goal_verified(self,i,p,**kw):
        self.writes.append((i,p)); self.positions[i]=max(p,self.contact or p)
    def pause(self,*args,**kw):
        self.state='FAULT_HOLD' if kw.get('fault') else 'PAUSED_HOLD'; return True
    def poll(self,fresh): return self.read_all()
    def resume_existing_hold(self,fresh): self.state='HOLDING'
    def sleep(self,s): self.t+=s


class Tests(unittest.TestCase):
    def run_close(self,f,**kw):
        return close_jaw(f,935,lambda:True,clock=lambda:f.t,sleep=f.sleep,**kw)
    def test_free_closure_never_passes_demonstrated_floor(self):
        f=Fake(); r=self.run_close(f)
        self.assertEqual(r['jaw'],935); self.assertTrue(all(i==6 and p>=935 for i,p in f.writes))
    def test_obstruction_stops_without_squeezing_to_floor(self):
        f=Fake(contact=1300); r=self.run_close(f)
        self.assertEqual(r['reason'],'RESIDUAL_CONTACT_CANDIDATE')
        self.assertGreater(min(p for _,p in f.writes),935)
    def test_stop_latches_hold(self):
        f=Fake()
        with self.assertRaises(BusError): self.run_close(f,stopped=lambda:f.t>.1)
        self.assertEqual(f.state,'FAULT_HOLD'); self.assertEqual(len(f.writes),1)
    def test_stale_camera_does_not_write(self):
        f=Fake()
        with self.assertRaises(BusError): close_jaw(f,935,lambda:False)
        self.assertFalse(f.writes)
    def test_arm_drift_aborts(self):
        f=Fake(); original=f.goal_verified
        def moved(*args,**kw): original(*args,**kw); f.positions[2]+=20
        f.goal_verified=moved
        with self.assertRaisesRegex(BusError,'Arm moved'): self.run_close(f)
        self.assertEqual(f.state,'FAULT_HOLD')
    def test_small_servo_residual_does_not_exhaust_steps_early(self):
        f=Fake(); original=f.goal_verified
        def biased(i,p,**kw): original(i,p,**kw); f.positions[i]+=4
        f.goal_verified=biased
        r=self.run_close(f)
        self.assertLessEqual(r['jaw'],943)
    def test_current_rise_stops_at_first_step(self):
        f=Fake(); original=f.read_all
        def loaded():
            rows=original()
            if f.writes: rows[6]['current_raw']=5
            return rows
        f.read_all=loaded
        r=self.run_close(f)
        self.assertEqual(r['reason'],'CURRENT_RISE_CONTACT_CANDIDATE')
        self.assertEqual(len(f.writes),1)
    def test_other_demonstrated_floors_and_unknown_floor(self):
        for floor in (975,1010):
            f=Fake();r=close_jaw(f,floor,lambda:True,clock=lambda:f.t,sleep=f.sleep)
            self.assertLessEqual(r['jaw'],floor+8)
            self.assertTrue(all(p>=floor for _,p in f.writes))
        f=Fake()
        with self.assertRaises(BusError):close_jaw(f,900,lambda:True)
        self.assertFalse(f.writes)

if __name__=='__main__': unittest.main()
