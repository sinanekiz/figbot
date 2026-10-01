import unittest
from dataclasses import replace
import numpy as np
from software.st3215_test.smooth_path import SmoothPath
from software.st3215_test.coordinated import validate_waypoints
from software.st3215_test.arm_control import ArmControl
from software.st3215_test.protocol import Bus,BusError
from tests.test_coordinated_motion import SyncBus
from tests.test_st3215_test import SerialFake


class StreamBus(SyncBus):
    def sync_positions(self,positions):
        self.history.append(('stream',dict(positions)));self.g.update(positions)


class SmoothTests(unittest.TestCase):
    def setUp(self):
        self.bus=StreamBus();self.now=0.;self.c=ArmControl(self.bus,lambda:self.now)
        self.c.arm(True);self.now=1.;self.c.poll();self.bus.history.clear()
        self.points=[{'positions':{'2':1300,'3':3700}},
                     {'positions':{'2':1600,'3':3500}},
                     {'positions':{'2':1064,'3':3959}}]

    def test_curve_continuous_limits_and_no_joint_overshoot(self):
        start=dict(self.c.targets)
        path=SmoothPath(start,validate_waypoints(self.points,start,self.c.envelopes,50),50)
        t=np.linspace(0,path.duration,2001);q=path.curve(t)
        self.assertLessEqual(np.max(np.abs(path.curve(t,1))),3400.01)
        self.assertLessEqual(np.max(np.abs(path.curve(t,2))),5000.01)
        self.assertTrue(np.allclose(path.curve([0,path.duration],1),0))
        self.assertGreater(abs(path.curve(path.times[1],1)[1]),1)
        for j,i in enumerate(path.ids):
            self.assertGreaterEqual(q[:,j].min(),path.bounds[i][0]-1e-6)
            self.assertLessEqual(q[:,j].max(),path.bounds[i][1]+1e-6)

    def test_c2_path_has_continuous_acceleration_and_exact_bounds(self):
        start=dict(self.c.targets)
        path=SmoothPath(start,validate_waypoints(self.points,start,self.c.envelopes,50),50,curve_kind='quintic_c2')
        for t in path.times[1:-1]:
            self.assertLess(np.max(abs(path.curve(t-1e-7,2)-path.curve(t+1e-7,2))),.1)
            self.assertLess(np.max(abs(path.curve(t-1e-7,1)-path.curve(t+1e-7,1))),.01)
        self.assertTrue(np.allclose(path.curve([0,path.duration],2),0,atol=1e-7))
        for j,(lo,hi) in enumerate(path.bounds.values()):
            q=path.curve(np.linspace(0,path.duration,2001))[:,j]
            self.assertGreaterEqual(q.min(),lo-1e-6);self.assertLessEqual(q.max(),hi+1e-6)
        self.assertLessEqual(path.max_speed,3400.0001)
        self.assertLessEqual(path.max_acceleration,5000.0001)

    def test_unknown_curve_kind_never_writes(self):
        with self.assertRaises(BusError):self.c.play_smooth(self.points,True,curve_kind='unknown')
        self.assertEqual(self.bus.history,[])

    def test_stream_updates_while_feedback_is_moving_and_finishes_at_home(self):
        self.c.play_smooth(self.points,True)
        path=self.c.smooth_path;started=self.now
        while self.now-started<path.duration+.12:
            self.now+=.04
            for i,p in path.sample(self.now-started).items():
                self.bus.f[i]=replace(self.bus.f[i],position=p,
                    moving=self.now-started<path.duration,speed=100 if self.now-started<path.duration else 0)
            self.c.poll()
        self.assertEqual(self.c.state,'HOLDING')
        self.assertGreater(sum(x[0]=='stream' for x in self.bus.history),10)
        self.assertTrue(all(5 not in x[1] for x in self.bus.history if x[0]=='stream'))
        self.assertEqual(self.c.targets,path.final)

    def test_host_gap_stops_without_skipping_ahead(self):
        self.c.play_smooth(self.points,True);self.now+=.3
        with self.assertRaises(BusError):self.c.poll()
        self.assertIsNone(self.c.active)
        self.assertFalse(any(x[0]=='stream' for x in self.bus.history))
        self.assertTrue(all(self.bus.profile[i][2]==50 for i in self.bus.profile))

    def test_recoverable_host_stall_does_not_skip_unexecuted_path(self):
        self.c.play_smooth(self.points,True);path=self.c.smooth_path
        started=self.now;deadline=self.c.active['deadline']
        for _ in range(10):
            self.now+=.02
            for i,pos in path.sample(self.now-started).items():
                self.bus.f[i]=replace(self.bus.f[i],position=pos)
            self.c.poll()
        previous_phase=self.now-started
        # During a181ms scheduler stall hardware can reach only the last goal.
        for i,pos in self.c.targets.items():self.bus.f[i]=replace(self.bus.f[i],position=pos)
        self.now+=.181;self.c.poll()
        self.assertEqual(self.c.state,'MOVING')
        self.assertAlmostEqual(self.c.active['scheduler_delay'],.141)
        self.assertAlmostEqual(self.now-started-self.c.active['time_offset'],previous_phase+.04)
        self.assertEqual(self.c.active['scheduler_delays'],1)
        self.assertEqual(self.c.active['deadline'],deadline)
        self.assertTrue(all(abs(self.c.targets[i]-self.bus.f[i].position)<=192 for i in path.moving))

    def test_repeated_short_stalls_cannot_extend_original_deadline(self):
        self.c.play_smooth(self.points,True)
        deadline=self.c.active['deadline'];failure=None
        for _ in range(200):
            self.now+=.15
            for i,pos in self.c.targets.items():self.bus.f[i]=replace(self.bus.f[i],position=pos)
            try:self.c.poll()
            except BusError as error:
                failure=str(error);break
        self.assertIn('bitişi doğrulanamadı',failure or '')
        self.assertGreater(self.now,deadline)
        self.assertLessEqual(self.now,deadline+.15)
        self.assertIsNone(self.c.active)

    def test_anticipation_shrinks_without_removing_relative_goal_bound(self):
        self.c.play_smooth(self.points,True);path=self.c.smooth_path
        # A valid tracking error can combine with anticipation to exceed the
        # relative goal cap. Follow the same timeline with less lookahead.
        elapsed=.2;self.now+=elapsed
        expected=path.sample(elapsed);ahead=path.sample(elapsed+.1)
        for i,p in expected.items():
            direction=1 if ahead[i]>p else -1 if ahead[i]<p else 0
            lo,hi=path.bounds[i]
            pos=max(lo,min(hi,p-direction*160))
            self.bus.f[i]=replace(self.bus.f[i],position=pos)
        self.c.poll()
        for kind,values in self.bus.history:
            if kind=='stream':
                self.assertTrue(all(abs(p-self.bus.f[i].position)<=192 for i,p in values.items()))
        self.assertEqual(self.c.state,'MOVING')

    def test_invalid_future_waypoint_does_not_write(self):
        with self.assertRaises(BusError):self.c.play_smooth(self.points+[{'positions':{'2':4095}}],True)
        self.assertEqual(self.bus.history,[])

    def test_custom_stream_timing_is_rebounded_by_actual_acceleration(self):
        start=dict(self.c.targets)
        points=[{**w,'stream_seconds':.25} for w in self.points]
        path=SmoothPath(start,validate_waypoints(points,start,self.c.envelopes,50),50)
        self.assertLessEqual(path.max_acceleration,5000.0001)
        self.assertLessEqual(path.max_speed,3400.0001)
        self.assertGreater(path.duration,.75)
        points[-1]['stream_seconds']=float('nan')
        with self.assertRaises(BusError):self.c.play_smooth(points,True)
        self.assertEqual(self.bus.history,[])

    def test_camera_loss_discards_stream(self):
        self.c.play_smooth(self.points,True)
        with self.assertRaises(BusError):self.c.poll(False)
        self.assertIsNone(self.c.active)

    def test_stream_readback_failure_stops_without_retry(self):
        self.c.play_smooth(self.points,True);self.now+=.08
        read=self.bus.read
        self.bus.read=lambda i,a,n: b'\0\0' if a==42 else read(i,a,n)
        with self.assertRaises(BusError):self.c.poll()
        self.assertIsNone(self.c.active)
        self.assertEqual(sum(x[0]=='stream' for x in self.bus.history),1)

    def test_position_stream_wire_preserves_profile_registers(self):
        serial=SerialFake(b'');Bus(serial).sync_positions({2:1300,3:3700})
        wire=serial.written[0]
        self.assertEqual(wire[:7],bytes([255,255,254,10,131,42,2]))
        self.assertEqual(wire[7:-1],bytes.fromhex('02 14 05 03 74 0e'))
        self.assertEqual(sum(wire[2:])&255,255)

    def test_batched_feedback_preserves_torque_and_all_measurements(self):
        from software.st3215_test.protocol import packet
        payload=bytearray(31);payload[0]=1
        payload[16:18]=(2308).to_bytes(2,'little');payload[18:20]=(0x8000+50).to_bytes(2,'little')
        payload[22]=122;payload[23]=39;payload[26]=1;payload[29:31]=(7).to_bytes(2,'little')
        serial=SerialFake(packet(2,0,payload));feedback,torque=Bus(serial).feedback_state(2)
        self.assertEqual(torque,1);self.assertEqual(feedback.position,2308);self.assertEqual(feedback.speed,-50)
        self.assertEqual(feedback.voltage,12.2);self.assertEqual(feedback.temperature,39)
        self.assertEqual(feedback.current_raw,7);self.assertTrue(feedback.moving)
        self.assertEqual(serial.written,[packet(2,2,bytes([40,31]))])

    def test_stream_scheduler_does_not_add_fixed_sleep_after_bus_work(self):
        from software.st3215_test.arm_console import poll_wait
        self.assertAlmostEqual(poll_wait(10,.02,10.012),.008)
        self.assertEqual(poll_wait(10,.02,10.035),0)

    def test_hardware_trajectory_uses_high_resolution_monotonic_clock(self):
        import time
        self.assertIs(ArmControl(self.bus).clock,time.perf_counter)

    def test_release_waits_for_measured_basket_before_opening(self):
        points=[{'positions':{'2':1300},'release_gate':True,'stream_seconds':.5},
                {'positions':{'2':1300,'6':1600},'stream_seconds':.6},
                {'positions':{'2':1100,'6':1600},'stream_seconds':.5}]
        self.c.play_smooth(points,True,curve_kind='quintic_c2');p=self.c.smooth_path;started=self.now
        gate=p.checkpoints[0]['seconds'];closed=p.sample(gate)[6]
        # Approach with 60 counts of arm lag, within normal tracking tolerance.
        while self.now-started<gate+.12:
            self.now+=.04
            for i,pos in p.sample(min(self.now-started,gate)).items():
                self.bus.f[i]=replace(self.bus.f[i],position=max(p.bounds[i][0],pos-(60 if i==2 else 0)),speed=0)
            self.c.poll()
            self.assertLessEqual(self.c.targets[6],closed)
        self.assertGreater(self.c.active['time_offset'],0)
        for i,pos in p.sample(gate).items():self.bus.f[i]=replace(self.bus.f[i],position=pos,speed=0)
        self.now+=.04;self.c.poll()
        self.assertEqual(self.c.active['checkpoint_index'],1)
        self.assertGreater(self.c.targets[6],closed)
        self.assertEqual(self.c.active['checkpoint_events'][0]['phase'],'basket_arrival')

    def test_arrival_accounts_for_two_count_encoder_jitter(self):
        points=[{'positions':{'2':1300},'release_gate':True,'stream_seconds':.5},
                {'positions':{'6':1600},'stream_seconds':.6}]
        self.c.play_smooth(points,True);p=self.c.smooth_path;started=self.now
        gate=p.checkpoints[0]['seconds']
        while self.now-started<gate+.04:
            self.now+=.02
            for i,pos in p.sample(min(self.now-started,gate)).items():
                self.bus.f[i]=replace(self.bus.f[i],position=pos+(21 if i==2 else 0),speed=0)
            self.c.poll()
        self.assertGreaterEqual(self.c.active['checkpoint_index'],1)
        self.assertEqual(self.c.active['time_offset'],0)

    def test_release_gate_timeout_holds_closed_and_discards_path(self):
        points=[{'positions':{'2':1300},'release_gate':True,'stream_seconds':.5},
                {'positions':{'6':1600},'stream_seconds':.6}]
        self.c.play_smooth(points,True);p=self.c.smooth_path;started=self.now
        gate=p.checkpoints[0]['seconds'];closed=p.sample(gate)[6]
        failed=False
        while self.now-started<gate+1:
            self.now+=.04
            for i,pos in p.sample(min(self.now-started,gate)).items():
                self.bus.f[i]=replace(self.bus.f[i],position=max(p.bounds[i][0],pos-(60 if i==2 else 0)),speed=0)
            try:self.c.poll()
            except BusError:failed=True;break
        self.assertTrue(failed);self.assertIsNone(self.c.active)
        self.assertLessEqual(self.c.targets[6],closed)

    def test_invalid_release_cannot_write_hardware(self):
        points=[{'positions':{'2':1300},'release_gate':True},
                {'positions':{'2':1400,'6':1600}}]
        with self.assertRaises(BusError):self.c.play_smooth(points,True)
        self.assertEqual(self.bus.history,[])


if __name__=='__main__':unittest.main()
