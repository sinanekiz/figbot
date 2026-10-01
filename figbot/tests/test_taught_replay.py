import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from software.st3215_test.teaching import TeachingRecorder
from software.st3215_test.taught_replay import prepare_replay
from software.st3215_test.arm_control import ArmControl
from software.st3215_test.protocol import BusError
from tests.test_arm_control import FakeBus


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.bus=FakeBus();self.c=ArmControl(self.bus);rec=TeachingRecorder(self.tmp.name)
        rec.start(self.c);self.bus.f[2]=replace(self.bus.f[2],position=1300)
        rec.sample(self.c.read_all());rec.stop()
        self.record=rec.path;self.path=Path(self.tmp.name)/'replay_plan.json'
        self.plan=dict(recording=rec.path.name,recording_sha256=hashlib.sha256(rec.path.read_bytes()).hexdigest(),start_sample=1,
            waypoints=[{'sample':0,'stream_seconds':.4},{'sample':1,'stream_seconds':.4}])
        self.write()

    def write(self):self.path.write_text(json.dumps(self.plan),encoding='utf-8')

    def test_recorded_path_local_ranges_and_passive_roll(self):
        way,env=prepare_replay(self.path,self.c)
        self.assertEqual(way[0]['positions']['2'],1064)
        self.assertEqual(env[2],(1044,1320))
        self.assertEqual(way[1]['positions']['5'],self.bus.f[5].position)
        self.assertEqual(self.bus.history,[])

    def test_tampered_file_rejected(self):
        self.record.write_text(self.record.read_text()+'\n')
        with self.assertRaises(BusError):prepare_replay(self.path,self.c)

    def test_gripper_overlay_must_reference_a_real_recorded_sample(self):
        self.plan['waypoints'][0]['gripper_sample']=1;self.write()
        way,_=prepare_replay(self.path,self.c)
        self.assertEqual(way[0]['positions']['6'],self.bus.f[6].position)
        self.plan['waypoints'][0]['gripper_sample']=99999;self.write()
        with self.assertRaises(BusError):prepare_replay(self.path,self.c)
        self.assertEqual(self.bus.history,[])

    def test_explicit_recovery_requires_nearby_record_and_enabled_hold(self):
        self.plan['recovery_start']={str(i):r.position for i,r in self.bus.f.items()}
        self.plan['waypoints']=[{'sample':1,'stream_seconds':.5}];self.write()
        with self.assertRaises(BusError):prepare_replay(self.path,self.c)
        self.bus.t={i:1 for i in self.bus.t}
        prepare_replay(self.path,self.c)
        self.plan['waypoints'][0]['sample']=0;self.write()
        with self.assertRaises(BusError):prepare_replay(self.path,self.c)
        self.assertEqual(self.bus.history,[])

    def test_clearance_blend_is_bounded_and_cannot_change_release(self):
        self.plan['waypoints'][0].update(blend_toward_sample=1,blend_max_counts=32);self.write()
        way,_=prepare_replay(self.path,self.c)
        self.assertEqual(way[0]['positions']['2'],1064+32)
        self.assertEqual(way[0]['positions']['6'],self.bus.f[6].position)
        self.plan['waypoints'][0]['release_gate']=True;self.write()
        with self.assertRaises(BusError):prepare_replay(self.path,self.c)
        self.plan['waypoints'][0].update(release_gate=False,blend_max_counts=65);self.write()
        with self.assertRaises(BusError):prepare_replay(self.path,self.c)
        self.assertEqual(self.bus.history,[])

    def test_wrong_start_or_offsets_rejected_before_hardware_writes(self):
        self.bus.f[2]=replace(self.bus.f[2],position=1500)
        with self.assertRaises(BusError):prepare_replay(self.path,self.c)
        self.bus.f[2]=replace(self.bus.f[2],position=1300);self.c.offsets[2]=0
        with self.assertRaises(BusError):prepare_replay(self.path,self.c)
        self.assertEqual(self.bus.history,[])

    def test_invalidated_record_and_path_escape_rejected(self):
        f=self.record.with_suffix('.summary.json');summary=json.loads(f.read_text());summary['status']='INVALIDATED_BY_USER_RESTART';f.write_text(json.dumps(summary))
        with self.assertRaises(BusError):prepare_replay(self.path,self.c)
        self.plan['recording']='../bad.jsonl';self.write()
        with self.assertRaises(BusError):prepare_replay(self.path,self.c)
