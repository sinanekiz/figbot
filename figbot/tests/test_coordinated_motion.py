import unittest
from dataclasses import replace
from software.st3215_test.protocol import Bus, BusError
from software.st3215_test.arm_control import ArmControl, IDS
from software.st3215_test.coordinated import profiles_for
from tests.test_arm_control import FakeBus
from tests.test_st3215_test import SerialFake


class SyncBus(FakeBus):
    def sync_goal(self, profiles):
        self.history.append(('sync', dict(profiles)))
        for i,(p,v,a) in profiles.items():
            self.g[i]=p;self.profile[i]=(p,v,a)


class ConcurrentTests(unittest.TestCase):
    def setUp(self):
        self.bus=SyncBus();self.now=0;self.c=ArmControl(self.bus,lambda:self.now)
        self.c.arm(True);self.now=1;self.c.poll();self.bus.history.clear()

    def arrive(self):
        for i,p in self.c.targets.items():self.bus.f[i]=replace(self.bus.f[i],position=p)
        self.c.poll();self.now+=.1;self.c.poll()

    def test_multiple_joints_receive_one_broadcast(self):
        self.c.move_pose({'2':1300,'3':3700},1.5,True)
        self.assertEqual(len(self.bus.history),1)
        self.assertEqual(set(self.bus.history[0][1]),{2,3})
        self.assertEqual(self.c.state,'MOVING')
        self.arrive();self.assertEqual(self.c.state,'HOLDING')

    def test_future_invalid_waypoint_rejected_before_any_write(self):
        with self.assertRaises(BusError):
            self.c.play_sequence([{'positions':{'2':1300}}, {'positions':{'3':4095}}],True)
        self.assertEqual(self.bus.history,[])

    def test_sequence_advances_without_external_commands(self):
        self.c.play_sequence([{'positions':{'2':1300,'3':3700}}, {'positions':{'2':1400,'3':3500}}],True)
        self.arrive();self.assertEqual(self.c.active['index'],2)
        self.arrive();self.assertEqual(self.c.state,'HOLDING')
        self.assertEqual(sum(x[0]=='sync' for x in self.bus.history),2)

    def test_stop_discards_the_remaining_sequence(self):
        self.c.play_sequence([{'positions':{'2':1300}}, {'positions':{'2':1400}}],True)
        self.c.pause();self.now+=1;self.c.poll()
        self.assertIsNone(self.c.active)
        self.assertEqual(sum(x[0]=='sync' for x in self.bus.history),1)

    def test_camera_loss_and_bad_voltage_stop_active_motion(self):
        self.c.move_pose({'2':1300,'3':3700},1.5,True)
        with self.assertRaises(BusError):self.c.poll(False)
        self.assertTrue(self.c.state.startswith('FAULT'))
        self.assertIsNone(self.c.active)

    def test_stall_has_deadline_and_does_not_replay(self):
        self.c.move_pose({'2':1300,'3':3700},1.5,True)
        self.now+=10
        with self.assertRaises(BusError):self.c.poll()
        self.assertTrue(self.c.state.startswith('FAULT'))
        self.assertEqual(sum(x[0]=='sync' for x in self.bus.history),1)

    def test_wrong_direction_stops(self):
        self.c.move_pose({'2':1300,'3':3700},1.5,True)
        self.bus.f[2]=replace(self.bus.f[2],position=900)
        with self.assertRaises(BusError):self.c.poll()
        self.assertIsNone(self.c.active)

    def test_outside_passive_wrist_never_written(self):
        self.bus.f[5]=replace(self.bus.f[5],position=3127);self.c.targets[5]=3127
        self.c.play_sequence([{'positions':{'2':1300}}, {'positions':{'2':1400}}],True)
        self.bus.f[5]=replace(self.bus.f[5],position=3128)
        self.arrive()
        self.assertTrue(all(5 not in x[1] for x in self.bus.history if x[0]=='sync'))

    def test_duration_limits_profiles_without_unlimited_sentinel(self):
        duration,profiles=profiles_for({1:1000,2:1000},{1:2000,2:1500},.25)
        self.assertAlmostEqual(duration,1000/3400+3400/15000)
        self.assertTrue(all(1<=v<=3400 and 1<=a<=150 for p,v,a in profiles.values()))
        self.assertEqual(profiles[1][2],150)
        self.assertAlmostEqual(profiles[1][1]/profiles[2][1],2,delta=.02)

    def test_short_move_uses_triangle_at_factory_acceleration(self):
        duration,p=profiles_for({1:1000},{1:2000},.25,max_acceleration=50)
        self.assertAlmostEqual(duration,2*(1000/5000)**.5)
        self.assertEqual(p[1][2],50)
        self.assertAlmostEqual(p[1][1],(1000*5000)**.5,delta=.5)

    def test_no_extra_dwell_but_moving_flag_blocks_advance(self):
        self.c.play_sequence([{'positions':{'2':1300}},{'positions':{'2':1400}}],True)
        self.bus.f[2]=replace(self.bus.f[2],position=1300,moving=True)
        self.c.poll();self.assertEqual(self.c.active['index'],1)
        self.bus.f[2]=replace(self.bus.f[2],moving=False)
        self.c.poll();self.assertEqual(self.c.active['index'],2)

    def test_explicit_dwell_still_applies(self):
        self.c.play_sequence([{'positions':{'2':1300},'dwell':.4},{'positions':{'2':1400}}],True)
        self.bus.f[2]=replace(self.bus.f[2],position=1300)
        self.c.poll();self.now+=.3;self.c.poll()
        self.assertEqual(self.c.active['index'],1)
        self.now+=.11;self.c.poll();self.assertEqual(self.c.active['index'],2)

    def test_sdk_packet_matches_manufacturer_layout_and_checksum(self):
        serial=SerialFake(b'');Bus(serial).sync_goal({2:(1300,250,5),3:(3700,500,10)})
        self.assertEqual(len(serial.written),1)
        wire=serial.written[0]
        self.assertEqual(wire[:7],bytes([255,255,254,20,131,41,7]))
        self.assertEqual(wire[7:-1],bytes.fromhex('02 05 14 05 00 00 fa 00 03 0a 74 0e 00 00 f4 01'))
        self.assertEqual(sum(wire[2:]) & 255,255)

    def test_invalid_sdk_profile_never_writes(self):
        serial=SerialFake(b'')
        with self.assertRaises(ValueError):Bus(serial).sync_goal({2:(1300,0,5)})
        self.assertEqual(serial.written,[])

    def test_maximum_numeric_sdk_profile_and_rejected_overflow(self):
        serial=SerialFake(b'');Bus(serial).sync_goal({2:(1300,3400,150)})
        self.assertEqual(serial.written[0][8],150)
        for v,a in [(3401,150),(3400,151),(3400,0)]:
            invalid=SerialFake(b'')
            with self.assertRaises(ValueError):Bus(invalid).sync_goal({2:(1300,v,a)})
            self.assertEqual(invalid.written,[])

    def test_factory_acceleration_limit_read_and_respected(self):
        self.c.move_pose({'2':1300,'3':3700},.25,True)
        self.assertEqual(self.c.motion_acceleration_limit,50)
        self.assertTrue(all(a<=50 for p,v,a in self.bus.history[0][1].values()))
        self.assertEqual(len(self.bus.history),1)

    def test_unreadable_factory_limit_never_starts_motion(self):
        original=self.bus.read
        self.bus.read=lambda i,a,n: b'\0' if a==85 else original(i,a,n)
        with self.assertRaises(BusError):self.c.move_pose({'2':1300},.25,True)
        self.assertEqual(self.bus.history,[])

    def test_readback_failure_holds_without_sync_retry(self):
        original=self.bus.read
        self.bus.read=lambda i,a,n: b'\0'*n if a==41 and self.c.state=='MOVING' else original(i,a,n)
        with self.assertRaises(BusError):self.c.move_pose({'2':1300,'3':3700},1.5,True)
        self.assertEqual(sum(x[0]=='sync' for x in self.bus.history),1)
        self.assertIsNone(self.c.active)


if __name__=='__main__':unittest.main()
