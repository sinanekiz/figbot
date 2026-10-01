import unittest
from dataclasses import replace
from software.st3215_test.arm_control import ArmControl,IDS,OFFSETS,JOG_DELTA,JOG_SPEED,JOG_ACCELERATION
from software.st3215_test.arm_commands import CommandSlot,validate_command
from software.st3215_test.protocol import Feedback,BusError,BusTimeout
from software.st3215_test.base_center import center_base,apply_reference
import tempfile
import json
from pathlib import Path


class FakeBus:
    def __init__(self):
        self.f={i:Feedback(p,0,12.2,30,0,False) for i,p in zip(IDS,[4000,1064,3959,1993,36,1485])}
        self.t={i:0 for i in IDS};self.g={};self.profile={};self.history=[];self.fail_enable=None;self.fail_off=None;self.auto_torque=False;self.goal_timeout=False
    def feedback(self,i):return self.f[i]
    def read(self,i,a,n):
        if a==85:return (50).to_bytes(n,'little')
        if a==41:
            p,s,acc=self.profile[i]
            return bytes([acc])+p.to_bytes(2,'little')+b'\0\0'+s.to_bytes(2,'little')
        x={40:self.t[i],42:self.g.get(i,0),31:OFFSETS[i],3:777,33:0}[a]
        return x.to_bytes(n,'little')
    def goal(self,i,p,s,a):
        self.g[i]=p;self.profile[i]=(p,s,a);self.history.append(('goal',i,p,s,a))
        if self.auto_torque:self.t[i]=1
        if self.goal_timeout:raise BusTimeout('lost goal ACK')
    def write(self,i,a,b):
        assert a==40
        self.t[i]=b[0];self.history.append(('torque',i,b[0]))
        if (b[0] and i==self.fail_enable) or (not b[0] and i==self.fail_off):raise BusError('lost ACK')


class ArmTests(unittest.TestCase):
    def setUp(self):
        self.bus=FakeBus();self.now=0;self.c=ArmControl(self.bus,lambda:self.now)
    def ready(self):
        self.c.arm(True);self.now+=1;self.c.poll()
    def test_current_target_precedes_explicit_enable(self):
        self.ready()
        for i in IDS:
            gi=next(n for n,x in enumerate(self.bus.history) if x[0]=='goal' and x[1]==i)
            ti=next(n for n,x in enumerate(self.bus.history) if x[0]=='torque' and x[1]==i)
            self.assertLess(gi,ti)
        self.assertTrue(all(self.bus.t.values()))
    def test_auto_enable_firmware(self):
        self.bus.auto_torque=True;self.ready()
        self.assertTrue(all(self.bus.t.values()));self.assertEqual(self.c.state,'HOLDING')
    def test_missing_goal_ack_accepted_only_with_readback(self):
        self.ready();self.bus.goal_timeout=True
        self.c.jog(4,23,True);self.assertEqual(self.c.state,'MOVING');self.assertEqual(self.c.ack_losses,1)
    def test_enable_ack_loss_releases_all(self):
        self.bus.fail_enable=4
        with self.assertRaises(BusError):self.ready()
        self.assertEqual(self.c.state,'DISARMED');self.assertFalse(any(self.bus.t.values()))
        self.assertEqual([x[1] for x in self.bus.history if x[0]=='torque' and x[2]==0],list(IDS))
    def test_lost_release_ack_independent_readback(self):
        self.ready();self.bus.fail_off=3
        self.assertTrue(self.c.release());self.assertFalse(any(self.bus.t.values()))
    def test_camera_refuses_arm_without_writes(self):
        with self.assertRaises(BusError):self.c.arm(False)
        self.assertFalse(self.bus.history)
    def test_stationary_manual_pose_can_be_held_outside_jog_envelope(self):
        self.bus.f[4]=replace(self.bus.f[4],position=2659)
        self.ready()
        self.assertEqual(self.c.state,'HOLDING')
        with self.assertRaises(BusError):self.c.jog(4,JOG_DELTA,True)
    def test_hold_remains_after_jog(self):
        self.ready();self.c.jog(3,-JOG_DELTA,True)
        self.bus.f[3]=replace(self.bus.f[3],position=3959-JOG_DELTA)
        self.c.poll();self.now+=.4;self.c.poll()
        self.assertEqual(self.c.state,'HOLDING');self.assertTrue(all(self.bus.t.values()))
    def test_wrong_direction_latches_and_stop_cannot_clear(self):
        self.ready();self.c.jog(2,JOG_DELTA,True)
        self.bus.f[2]=replace(self.bus.f[2],position=1040)
        with self.assertRaises(BusError):self.c.poll()
        self.assertEqual(self.c.state,'FAULT_HOLD');n=len(self.bus.history)
        self.c.poll();self.c.pause();self.assertEqual(len(self.bus.history),n)
        self.assertEqual(self.c.state,'FAULT_HOLD')
    def test_passive_joint_drift_freezes(self):
        self.ready();self.bus.f[3]=replace(self.bus.f[3],position=3900)
        with self.assertRaises(BusError):self.c.jog(2,57,True)
        self.assertEqual(self.c.state,'FAULT_HOLD')
    def test_no_wrap_or_large_jog(self):
        self.ready()
        for i,d in [(5,-JOG_DELTA),(2,JOG_DELTA+1),(1,JOG_DELTA*2)]:
            with self.assertRaises(BusError):self.c.jog(i,d,True)
        self.assertEqual(self.c.state,'HOLDING')
    def test_camera_loss_holds_not_drops(self):
        self.ready();self.c.jog(2,JOG_DELTA,True)
        with self.assertRaises(BusError):self.c.poll(False)
        self.assertEqual(self.c.state,'FAULT_HOLD');self.assertTrue(all(self.bus.t.values()))
    def test_poll_fault_does_not_repeat_writes(self):
        self.ready();self.bus.f[2]=replace(self.bus.f[2],temperature=55)
        self.c.poll();self.c.poll()
        with self.assertRaises(BusError):self.c.poll()
        n=len(self.bus.history)
        with self.assertRaises(BusError):self.c.poll()
        self.assertEqual(len(self.bus.history),n)

    def test_single_invalid_feedback_is_transient_then_continues(self):
        self.ready();self.bus.f[2]=replace(self.bus.f[2],temperature=55)
        self.c.poll();self.assertEqual(self.c.state,'HOLDING')
        self.bus.f[2]=replace(self.bus.f[2],temperature=30)
        self.c.poll();self.assertEqual(self.c.state,'HOLDING')

    def test_existing_stationary_hardware_hold_is_adopted_without_write(self):
        self.ready(); before=len(self.bus.history)
        other=ArmControl(self.bus,lambda:self.now)
        other.attach_existing_hold(True)
        self.assertEqual(other.state,'HOLDING')
        self.assertEqual(other.targets,self.c.targets)
        self.assertEqual(len(self.bus.history),before)
    def test_base_low_branch_does_not_allow_wrap(self):
        self.bus.f[1]=replace(self.bus.f[1],position=20);self.ready()
        with self.assertRaises(BusError):self.c.jog(1,-JOG_DELTA,True)
        self.c.jog(1,JOG_DELTA,True);self.assertEqual(self.c.targets[1],134)

    def mixed_hold(self):
        for i in IDS:
            self.bus.t[i]=int(i!=5)
            self.bus.g[i]=self.bus.f[i].position
        self.bus.g[5]=1000  # Must not replay this stale disabled-joint goal.
        self.bus.f[5]=replace(self.bus.f[5],position=3692)

    def test_recovery_only_enables_missing_hold_at_measured_position(self):
        self.mixed_hold();self.c.recover_current_hold(True)
        self.assertEqual(self.c.state,'STARTING')
        self.assertEqual(self.bus.history,[('goal',5,3692,57,1),('torque',5,1)])
        self.now=1;self.c.poll();self.assertEqual(self.c.state,'HOLDING')
        with self.assertRaises(BusError):self.c.jog(5,23,True)

    def test_recovery_failure_preserves_preexisting_holds(self):
        self.mixed_hold();self.bus.auto_torque=True;self.bus.goal_timeout=True
        self.c.ack_losses=2
        with self.assertRaises(BusError):self.c.recover_current_hold(True)
        self.assertEqual(self.c.state,'FAULT_STOPPED')
        self.assertEqual(self.bus.t,{i:int(i!=5) for i in IDS})
        self.assertTrue(all(entry[1]==5 for entry in self.bus.history))

    def test_recovery_unexpected_movement_cuts_new_joint_without_second_goal(self):
        self.mixed_hold();self.c.recover_current_hold(True)
        self.bus.f[5]=replace(self.bus.f[5],position=3750,speed=400,moving=True)
        with self.assertRaises(BusError):self.c.poll()
        self.assertEqual(self.c.state,'FAULT_STOPPED')
        self.assertEqual(self.bus.t,{i:int(i!=5) for i in IDS})
        self.assertEqual(sum(x[0]=='goal' for x in self.bus.history),1)

    def test_recovery_lost_feedback_or_camera_cuts_only_new_joint(self):
        for kind in ('camera','feedback'):
            self.setUp();self.mixed_hold();self.c.recover_current_hold(True)
            if kind=='feedback':
                def broken(i):raise BusTimeout('disconnected')
                self.bus.feedback=broken
            with self.assertRaises(BusError):self.c.poll(kind!='camera')
            self.assertEqual(self.c.state,'FAULT_STOPPED')
            self.assertEqual(self.bus.t,{i:int(i!=5) for i in IDS})

    def test_recovery_checks_entire_chain_before_any_write(self):
        for failure in ('camera','goal','offset','moving','drift'):
            self.setUp();self.mixed_hold()
            if failure=='goal':self.bus.g[6]+=100
            if failure=='moving':self.bus.f[6]=replace(self.bus.f[6],moving=True)
            if failure=='offset':
                read=self.bus.read
                self.bus.read=lambda i,a,n: b'\0\0' if i==6 and a==31 else read(i,a,n)
            if failure=='drift':
                feedback=self.bus.feedback;calls=[0]
                def changing(i):
                    calls[0]+=1
                    f=feedback(i)
                    return replace(f,position=f.position+20) if calls[0]>6 else f
                self.bus.feedback=changing
            with self.assertRaises(BusError):self.c.recover_current_hold(failure!='camera')
            self.assertFalse(self.bus.history)
    def test_pause_does_not_reenable_lost_torque(self):
        self.bus.auto_torque=True;self.ready();self.bus.t[3]=0
        self.c.pause();self.assertEqual(self.bus.t[3],0);self.assertEqual(self.c.state,'FAULT_STOPPED')
    def test_stop_goal_ack_is_not_proof_of_physical_stop(self):
        self.ready();self.c.pause()
        self.bus.f[1]=replace(self.bus.f[1],position=3950,speed=-100)
        self.now+=.4;self.c.poll()
        self.assertEqual(self.c.state,'FAULT_STOPPED');self.assertEqual(self.bus.t[1],0)
        self.assertEqual(self.bus.t[2],1)
    def test_moving_stop_keeps_target_and_torque_during_bounded_return(self):
        self.ready();self.c.motion_acceleration_limit=50
        self.bus.f[2]=replace(self.bus.f[2],speed=1050,moving=True)
        captured=self.bus.f[2].position;before=self.now
        self.c.pause('tracking fault',fault=True)
        deadline=self.c.stop_check_at
        self.assertGreater(deadline-before,.7)
        self.assertLessEqual(deadline-before,.9)
        self.assertEqual(self.c.targets[2],captured)
        self.assertEqual(self.bus.profile[2],(captured,JOG_SPEED,50))
        self.bus.f[2]=replace(self.bus.f[2],position=captured+160,speed=200)
        self.now=before+.2;self.c.poll()
        self.bus.f[2]=replace(self.bus.f[2],position=captured+55,speed=-500)
        self.now=before+.4;self.c.poll()
        self.assertTrue(all(self.bus.t.values()))
        self.assertEqual(self.c.state,'FAULT_HOLD')
        self.bus.f[2]=replace(self.bus.f[2],position=captured+7,speed=0,moving=False)
        self.now=deadline+.01;self.c.poll()
        self.assertTrue(all(self.bus.t.values()))
        self.assertEqual(self.c.targets[2],captured)
        self.assertIsNone(self.c.stop_check_at)
        self.assertIsNone(self.c.active)
        self.assertEqual(self.c.state,'FAULT_HOLD')
    def test_stop_excursion_over_192_fails_before_settling_deadline(self):
        self.ready();self.c.motion_acceleration_limit=50
        self.bus.f[2]=replace(self.bus.f[2],speed=1050,moving=True)
        self.c.pause(fault=True);deadline=self.c.stop_check_at
        self.bus.f[2]=replace(self.bus.f[2],position=self.c.targets[2]+193,speed=500)
        self.now+=.05;self.assertLess(self.now,deadline);self.c.poll()
        self.assertEqual(self.c.state,'FAULT_STOPPED')
        self.assertEqual(self.bus.t[2],0)
        self.assertTrue(all(self.bus.t[i] for i in IDS if i!=2))
        self.assertIsNone(self.c.stop_check_at)
    def test_stationary_stop_retains_original_point_35_second_deadline(self):
        self.ready();before=self.now;self.c.pause()
        self.assertAlmostEqual(self.c.stop_check_at-before,.35)
        self.now+=.36;self.c.poll()
        self.assertIsNone(self.c.stop_check_at)
        self.assertTrue(all(self.bus.t.values()))
        self.assertEqual(self.c.state,'PAUSED_HOLD')
    def test_moving_stop_stuck_or_running_fails_at_finite_deadline(self):
        for drift,speed in ((20,0),(0,100)):
            with self.subTest(drift=drift,speed=speed):
                self.setUp();self.ready();self.c.motion_acceleration_limit=50
                self.bus.f[2]=replace(self.bus.f[2],speed=1050,moving=True)
                self.c.pause(fault=True)
                self.bus.f[2]=replace(self.bus.f[2],position=self.c.targets[2]+drift,speed=speed)
                self.now=self.c.stop_check_at+.01;self.c.poll()
                self.assertEqual(self.c.state,'FAULT_STOPPED')
                self.assertEqual(self.bus.t[2],0)
                self.assertTrue(all(self.bus.t[i] for i in IDS if i!=2))
    def test_moving_stop_allowance_is_capped_even_for_large_capture_speed(self):
        self.ready();self.c.motion_acceleration_limit=50
        self.bus.f[2]=replace(self.bus.f[2],speed=10000,moving=True)
        before=self.now;self.c.pause(fault=True)
        self.assertAlmostEqual(self.c.stop_check_at-before,.9)
    def test_stop_settling_still_validates_health_and_has_finite_failure_deadline(self):
        self.ready();self.c.motion_acceleration_limit=50
        self.bus.f[2]=replace(self.bus.f[2],speed=1050,moving=True)
        self.c.pause(fault=True);deadline=self.c.stop_check_at
        self.bus.f[3]=replace(self.bus.f[3],temperature=56)
        self.now+=.05;self.assertLess(self.now,deadline)
        with self.assertRaises(BusError):self.c.poll()
        self.assertEqual(self.c.state,'FAULT_HOLD')
        self.assertTrue(all(self.bus.t.values()))
        self.assertEqual(self.c.stop_check_at,deadline)
        self.now=deadline+.01
        with self.assertRaises(BusError):self.c.poll()
        self.assertEqual(self.c.state,'FAULT_STOPPED')
        self.assertFalse(any(self.bus.t.values()))
    def test_startup_requires_actual_stationary_readings(self):
        self.c.arm(True);self.assertEqual(self.c.state,'STARTING')
        with self.assertRaises(BusError):self.c.jog(2,JOG_DELTA,True)
        self.bus.f[1]=replace(self.bus.f[1],position=3995,speed=-101)
        self.c.poll();self.c.poll()
        with self.assertRaises(BusError):self.c.poll()
        self.assertEqual(self.c.state,'FAULT_HOLD')

    def test_high_speed_profile_and_ten_degree_jog_are_verified(self):
        self.ready();self.c.jog(2,JOG_DELTA,True)
        self.assertEqual(self.bus.profile[2],(1064+JOG_DELTA,JOG_SPEED,JOG_ACCELERATION))

    def test_probe_is_slow_and_bounded_and_retains_existing_guards(self):
        self.bus.f[5]=replace(self.bus.f[5],position=12)
        self.ready();n=len(self.bus.history)
        for delta in (0,24,-24,True):
            with self.assertRaises(BusError):self.c.probe(2,delta,True)
        with self.assertRaises(BusError):self.c.probe(2,23,False)
        with self.assertRaises(BusError):self.c.probe(5,-23,True)
        self.assertEqual(len(self.bus.history),n)
        self.c.probe(2,23,True)
        self.assertEqual(self.bus.profile[2],(1087,57,1))


    def test_retreat_only_moves_toward_existing_interval_without_expansion(self):
        self.bus.f[4]=replace(self.bus.f[4],position=2659)
        self.ready();limits=dict(self.c.envelopes)
        for op,delta in ((self.c.probe,-23),(self.c.retreat_probe,23),(self.c.retreat_probe,-24)):
            with self.assertRaises(BusError):op(4,delta,True)
        self.c.retreat_probe(4,-23,True)
        self.assertEqual(self.bus.profile[4],(2636,57,1))
        self.assertEqual(self.c.envelopes,limits)

    def test_retreat_below_interval_never_crosses_encoder_zero(self):
        self.bus.f[5]=replace(self.bus.f[5],position=2)
        self.ready()
        with self.assertRaises(BusError):self.c.retreat_probe(5,-23,True)
        self.c.retreat_probe(5,5,True)
        self.assertEqual(self.bus.profile[5],(7,57,1))

    def test_slow_step_has_separate_size_limit_and_same_motion_guards(self):
        self.ready()
        with self.assertRaises(BusError):self.c.step(2,58,True)
        self.c.step(2,57,True)
        self.assertEqual(self.bus.profile[2],(1121,57,1))


class CommandsTests(unittest.TestCase):
    def test_new_supervised_operations_still_require_current_session(self):
        for op in ('recover','probe','retreat_probe','step'):
            good={'session':'a','seq':1,'created_unix':100,'op':op}
            self.assertEqual(validate_command(good,'a',0,101),1)
            with self.assertRaises(ValueError):validate_command(good,'a',0,104)

    def test_read_only_connection_commands_keep_session_and_expiry_guards(self):
        for op in ('connect','attach'):
            good={'session':'a','seq':1,'created_unix':100,'op':op}
            self.assertEqual(validate_command(good,'a',0,101),1)
            for data,last,now in [(dict(good,session='b'),0,101),(good,1,101),(good,0,104)]:
                with self.assertRaises(ValueError):validate_command(data,'a',last,now)
        with self.assertRaises(ValueError):
            validate_command({'session':'a','seq':1,'created_unix':100,'op':'unknown'},'a',0,101)

    def test_stale_session_replay_expiry(self):
        good={'session':'a','seq':1,'created_unix':100,'op':'jog'}
        self.assertEqual(validate_command(good,'a',0,101),1)
        for data,last,now in [(dict(good,session='b'),0,101),(good,1,101),(good,0,104),(dict(good,created_unix=float('nan')),0,101)]:
            with self.assertRaises(ValueError):validate_command(data,'a',last,now)
    def test_stop_priority_no_backlog(self):
        s=CommandSlot(lambda:100)
        self.assertTrue(s.put({'op':'jog'}));self.assertFalse(s.put({'op':'jog'}))
        self.assertTrue(s.put({'op':'pause'}));self.assertFalse(s.put({'op':'arm'}))
        self.assertEqual(s.take()['op'],'pause');self.assertIsNone(s.take())
    def test_expiry_rechecked_on_execution(self):
        t=[100];s=CommandSlot(lambda:t[0]);s.put({'op':'jog'});t[0]=104
        with self.assertRaises(ValueError):s.take()
        self.assertIsNone(s.take())


class CenterBus(FakeBus):
    def __init__(self):
        super().__init__();self.offset=85;self.bad_center=False;self.drift=False
        self.center_ack_lost=False
    def read(self,i,a,n):
        if i==1 and a==31:return self.offset.to_bytes(n,'little')
        return super().read(i,a,n)
    def write(self,i,a,b):
        if b==b'\x80':
            assert i==1 and a==40 and self.t[1]==0
            self.history.append(('center',i))
            correction=(self.f[1].position+85-2048+2048)%4096-2048
            self.offset=abs(correction)|(2048 if correction<0 else 0)
            self.f[1]=replace(self.f[1],position=2000 if self.bad_center else 2048)
            if self.center_ack_lost:raise BusTimeout('lost calibration ACK')
            return
        super().write(i,a,b)
    def goal(self,i,p,s,a):
        super().goal(i,p,s,a)
        if i==1 and self.offset!=85:
            self.f[1]=replace(self.f[1],position=p+30 if self.drift else p)


class BaseCenterTests(unittest.TestCase):
    def setUp(self):
        self.bus=CenterBus();self.c=ArmControl(self.bus)
        self.bus.t={i:1 for i in IDS};self.bus.g={i:r.position for i,r in self.bus.f.items()}
        self.c.attach_existing_hold(True);self.bus.history.clear()
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.ref=Path(self.tmp.name)/'reference.json';self.audit=Path(self.tmp.name)/'audit.json'
    def run_center(self,camera=lambda:True):
        return center_base(self.c,camera,self.ref,self.audit,sleep=lambda _:None)
    def test_only_base_recentered_and_physical_envelope_preserved(self):
        record=self.run_center()
        self.assertEqual(self.c.envelopes[1],(748,3304))
        self.assertEqual(self.c.targets[1],2048)
        self.assertEqual([v[1] for v in self.bus.history], [1]*len(self.bus.history))
        goals=[v for v in self.bus.history if v[0]=='goal']
        self.assertEqual(goals,[('goal',1,2048,57,1)])
        self.assertTrue(all(self.bus.t.values()))
        self.assertEqual(json.loads(self.ref.read_text())['status'],'VERIFIED')
        other=ArmControl(self.bus);apply_reference(other,record)
        other.attach_existing_hold(True);other.step(1,57,True)
        self.assertEqual(other.targets[1],2105)
    def test_high_branch_negative_offset_is_valid(self):
        self.bus.f[1]=replace(self.bus.f[1],position=4026);self.bus.g[1]=4026;self.c.targets[1]=4026
        record=self.run_center()
        self.assertEqual(record['new_offset'],4081)
        self.assertEqual(self.c.envelopes[1],(722,3278))
    def test_calibration_ack_loss_is_read_back_not_retried(self):
        self.bus.center_ack_lost=True;self.run_center()
        self.assertEqual(sum(v[0]=='center' for v in self.bus.history),1)
    def test_failure_cuts_only_base_and_never_replays_old_goal(self):
        self.bus.bad_center=True
        with self.assertRaises(BusError):self.run_center()
        self.assertEqual(self.bus.t[1],0)
        self.assertTrue(all(self.bus.t[i] for i in range(2,7)))
        self.assertFalse(any(v[0]=='goal' for v in self.bus.history))
        self.assertFalse(self.ref.exists())
        self.assertEqual(json.loads(self.audit.read_text())['status'],'FAILED')
    def test_activation_drift_cuts_only_base(self):
        self.bus.drift=True
        with self.assertRaises(BusError):self.run_center()
        self.assertEqual(self.bus.t[1],0)
        self.assertTrue(all(self.bus.t[i] for i in range(2,7)))
        self.assertFalse(self.ref.exists())
    def test_missing_camera_and_bad_old_offset_do_not_write(self):
        with self.assertRaises(BusError):self.run_center(lambda:False)
        self.bus.offset=86
        with self.assertRaises(BusError):self.run_center()
        self.assertFalse(self.bus.history)
    def test_stale_reference_does_not_enable_motion(self):
        record=self.run_center();self.bus.offset=85
        with self.assertRaises(BusError):apply_reference(ArmControl(self.bus),record)
    def test_encoder_quantization_uses_offset_for_exact_envelope(self):
        record=self.run_center()
        record['old_position']-=1
        apply_reference(ArmControl(self.bus),record)
        record['old_position']-=9
        with self.assertRaises(BusError):apply_reference(ArmControl(self.bus),record)
    def test_center_command_keeps_expiry_and_session_guards(self):
        good={'session':'a','seq':1,'created_unix':100,'op':'center_base'}
        self.assertEqual(validate_command(good,'a',0,101),1)
        with self.assertRaises(ValueError):validate_command(good,'a',0,104)
        with self.assertRaises(ValueError):validate_command(good,'b',0,101)


if __name__=='__main__':unittest.main()
