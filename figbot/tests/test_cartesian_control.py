import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
import numpy as np
from tests.test_coordinated_motion import SyncBus
from software.st3215_test.arm_control import ArmControl
from software.st3215_test.cartesian import CartesianController
from software.st3215_test.motion_library import MotionLibrary
from software.st3215_test.protocol import BusError

ROOT=Path(__file__).resolve().parents[1]


class CartesianTests(unittest.TestCase):
    def setUp(self):
        self.bus=SyncBus();self.c=ArmControl(self.bus)
        positions=[2540,2200,3402,1284,3128,949]
        self.bus.f={i:replace(self.bus.f[i],position=p) for i,p in enumerate(positions,1)}
        self.c.rows={i:{'position':p} for i,p in enumerate(positions,1)}
        self.c.targets=dict(enumerate(positions,1));self.c.state='HOLDING'
        self.c.offsets[1]=4080;self.c.envelopes[1]=(721,3277)
        self.ik=CartesianController(ROOT/'references/vendor/so101/Simulation/SO101/so101_new_calib.urdf',ROOT/'software/st3215_test/cartesian_reference.json')

    def test_local_vertical_target_roundtrip_and_locked_roll(self):
        raw=[self.bus.f[i].position for i in range(1,6)]
        target=self.ik.pose(raw)[:3,3]*1000+[0,0,40]
        plan=self.ik.plan(self.c,target)
        self.assertLess(plan['model_error_mm'],2)
        self.assertNotIn('5',plan['positions'])
        self.assertFalse(plan['physical_accuracy_verified'])
        self.assertEqual(self.bus.history,[])

    def test_unreachable_and_nonfinite_targets_do_not_write(self):
        for target in ([2000,0,0],[np.nan,0,100],[0,100]):
            with self.assertRaises((BusError,ValueError)):self.ik.plan(self.c,target)
        self.assertEqual(self.bus.history,[])

    def test_offset_mismatch_refuses_plan(self):
        self.c.offsets[1]=85
        with self.assertRaises(BusError):self.ik.plan(self.c,[260,-233,120])

    def test_explicit_roll_branch_never_wraps_automatically(self):
        with self.assertRaises(BusError):self.ik.angles([2540,2200,3402,1284,112])

    def test_save_and_recall_pose_checks_calibration(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib=MotionLibrary(Path(tmp)/'poses.json')
            lib.save('baslangic',self.c)
            self.assertEqual(lib.pose('baslangic',self.c)['1'],2540)
            self.c.offsets[1]=85
            with self.assertRaises(BusError):lib.pose('baslangic',self.c)
        self.assertEqual(self.bus.history,[])

    def test_moving_pose_and_invalid_name_not_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib=MotionLibrary(Path(tmp)/'poses.json')
            with self.assertRaises(BusError):lib.save('../bad',self.c)
            self.c.state='MOVING'
            with self.assertRaises(BusError):lib.save('bad',self.c)
            self.assertFalse(lib.path.exists())

    def test_home_cycle_requires_measured_start_and_final_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib=MotionLibrary(Path(tmp)/'poses.json');lib.save('home',self.c)
            data=lib.load();data['poses']['pick']=dict(data['poses']['home'])
            data['home_cycles']={'cycle':'home'}
            data['sequences']['cycle']=[{'pose':'home'},{'pose':'pick'},{'pose':'home'}]
            lib.path.write_text(json.dumps(data),encoding='utf-8')
            plan=lib.sequence('cycle',self.c)
            self.assertEqual(plan[0]['positions'],plan[-1]['positions'])
            self.bus.f[2]=replace(self.bus.f[2],position=self.bus.f[2].position+30)
            with self.assertRaises(BusError):lib.sequence('cycle',self.c)
            self.bus.f[2]=replace(self.bus.f[2],position=self.bus.f[2].position-30)
            data['sequences']['cycle'].pop()
            lib.path.write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaises(BusError):lib.sequence('cycle',self.c)
            self.assertEqual(self.bus.history,[])

    def make_folded_cycle(self, path):
        home={1:2033,2:782,3:3946,4:2729,5:3127,6:949}
        self.bus.f={i:replace(self.bus.f[i],position=p) for i,p in home.items()}
        self.bus.t={i:1 for i in home}
        self.c.targets=dict(home)
        lib=MotionLibrary(path);lib.save('home',self.c)
        data=lib.load()
        data['poses']['transit']={'positions':{str(i):p for i,p in
            {**home,2:1300,4:2000}.items()},'offsets':data['poses']['home']['offsets']}
        data['home_cycles']={'cycle':'home'}
        data['sequences']['cycle']=[{'pose':'home'},{'pose':'transit'},{'pose':'home'}]
        lib.path.write_text(json.dumps(data),encoding='utf-8')
        return lib

    def test_folded_cycle_scopes_extension_and_returns_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib=self.make_folded_cycle(Path(tmp)/'poses.json')
            original=dict(self.c.envelopes);now=[0.];self.c.clock=lambda:now[0]
            lib.play('cycle',self.c,True)
            for _ in range(3):
                for i,p in self.c.targets.items():self.bus.f[i]=replace(self.bus.f[i],position=p)
                self.c.poll();now[0]+=.1;self.c.poll()
            self.assertEqual(self.c.state,'HOLDING')
            self.assertEqual(self.c.targets,{int(i):p for i,p in lib.pose('home',self.c).items()})
            self.assertEqual(self.c.envelopes,original)
            self.assertTrue(all(5 not in x[1] for x in self.bus.history if x[0]=='sync'))
            self.bus.history.clear()
            with self.assertRaises(BusError):self.c.move_pose({'2':1300},.25,True)
            self.assertEqual(self.bus.history,[])

    def test_folded_extension_cannot_be_used_by_interior_waypoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib=self.make_folded_cycle(Path(tmp)/'poses.json');data=lib.load()
            data['poses']['transit']['positions']['2']=800
            lib.path.write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaises(BusError):lib.play('cycle',self.c,True)
            self.assertEqual(self.bus.history,[])

    def test_folded_extension_rejects_distant_home_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib=self.make_folded_cycle(Path(tmp)/'poses.json');data=lib.load()
            data['poses']['home']['positions']['2']=500
            self.bus.f[2]=replace(self.bus.f[2],position=500);self.c.targets[2]=500
            lib.path.write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaises(BusError):lib.play('cycle',self.c,True)
            self.assertEqual(self.bus.history,[])

    def test_explicit_home_return_only_from_taught_corridor(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib=self.make_folded_cycle(Path(tmp)/'poses.json');data=lib.load()
            data['home_transits']={'home':'transit'}
            lib.path.write_text(json.dumps(data),encoding='utf-8')
            self.bus.f[2]=replace(self.bus.f[2],position=1000);self.c.targets[2]=1000
            self.bus.f[4]=replace(self.bus.f[4],position=2400);self.c.targets[4]=2400
            lib.return_home('home',self.c,True)
            self.assertEqual(self.c.targets[2],782);self.assertEqual(self.c.targets[4],2729)
            self.c.state='HOLDING';self.bus.history.clear()
            self.bus.f[1]=replace(self.bus.f[1],position=2400);self.c.targets[1]=2400
            with self.assertRaises(BusError):lib.return_home('home',self.c,True)
            self.assertEqual(self.bus.history,[])


if __name__=='__main__':unittest.main()
