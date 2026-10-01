import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from software.st3215_test.teaching import TeachingRecorder
from software.st3215_test.arm_control import ArmControl
from software.st3215_test.protocol import BusError
from tests.test_arm_control import FakeBus


class TeachingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.now=100.;self.bus=FakeBus();self.c=ArmControl(self.bus)
        self.r=TeachingRecorder(Path(self.tmp.name),lambda:self.now)
        self.addCleanup(lambda:self.r.stop() if self.r.active else None)

    def test_manual_path_and_gripper_events_persist_without_motor_writes(self):
        self.r.start(self.c)
        self.now+=.1;self.bus.f[6]=replace(self.bus.f[6],position=900,speed=-100)
        self.r.sample(self.c.read_all());self.r.mark('kavradim',self.c)
        result=self.r.stop()
        data=[json.loads(x) for x in Path(result['path']).read_text(encoding='utf-8').splitlines()]
        self.assertEqual(data[0]['mode'],'PASSIVE_TORQUE_OFF')
        self.assertEqual(data[-2]['label'],'kavradim')
        self.assertEqual(data[-2]['positions']['6'],900)
        self.assertFalse(result['replay_validated']);self.assertEqual(self.bus.history,[])

    def test_any_enabled_motor_blocks_teaching(self):
        self.bus.t[3]=1
        with self.assertRaises(BusError):self.r.start(self.c)
        self.assertFalse(self.r.active);self.assertEqual(self.bus.history,[])

    def test_torque_change_aborts_recording_without_changing_hardware(self):
        self.r.start(self.c);self.bus.t[2]=1
        with self.assertRaises(BusError):self.r.sample(self.c.read_all())
        self.assertFalse(self.r.active);self.assertEqual(self.bus.t[2],1)
        self.assertEqual(self.r.summary['status'],'ABORTED_TORQUE_CHANGED')
        self.assertEqual(self.bus.history,[])

    def test_encoder_wrap_and_feedback_gap_flagged_for_review(self):
        self.r.start(self.c);self.now+=1
        self.bus.f[1]=replace(self.bus.f[1],position=5)
        self.r.sample(self.c.read_all())
        self.assertIn('ENCODER_JUMP_REQUIRES_REVIEW',self.r.flags)
        self.assertIn('FEEDBACK_GAP',self.r.flags)


if __name__=='__main__':unittest.main()
