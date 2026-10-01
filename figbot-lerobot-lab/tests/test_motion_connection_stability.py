"""Manual link loss pauses stale commands without pretending a hold succeeded."""
import pytest
from dataclasses import replace
from test_virtual_leader import FakeBus, Clock, profile_value
from figbot_lab._reference_protocol import BusError, BusTimeout, MotorStatusError
from figbot_lab.virtual_motion import (MotionController, Profile, MotionBus, MotorOverheat,
                                       _EMERGENCY_TORQUE_OFF)


class LossBus(FakeBus):
    def __init__(self):
        super().__init__()
        self.trace = []
        self.lost_reads = []
        self.persistent_loss = False
        self.write_ack_lost = False
        self.verify_read_lost = False
        self.hardware_fault = False
        self.off_write_failed = set()
        self.off_ack_lost = set()
        self.off_read_failed = set()
        self.temperatures = {}
        self.motor_status_flags = 0
        self.write_status_flags = 0

    def feedback(self, motor):
        value = super().feedback(motor)
        return replace(value, temperature=self.temperatures.get(motor, value.temperature))

    def feedback_state(self, motor):
        self.trace.append(('feedback', motor))
        if self.hardware_fault:
            raise BusError('Motor error flag: fixture')
        if self.persistent_loss or self.lost_reads and motor == self.lost_reads[0]:
            if self.lost_reads:
                self.lost_reads.pop(0)
            raise BusTimeout(f'ID{motor}: fixture READ timeout')
        if self.motor_status_flags and motor == 2:
            raise MotorStatusError(motor, self.motor_status_flags)
        return super().feedback_state(motor)

    def read(self, motor, address, size):
        self.trace.append(('read', motor, address))
        if address == 40 and motor in self.off_read_failed:
            raise BusTimeout('fixture torque verification READ timeout')
        if self.verify_read_lost and address == 41:
            self.verify_read_lost = False
            raise BusTimeout('fixture command verification READ timeout')
        return super().read(motor, address, size)

    def disable_torque(self, motor, *, authority=None):
        assert authority is _EMERGENCY_TORQUE_OFF
        self.trace.append(('off', motor))
        if motor in self.off_write_failed:
            raise BusTimeout('fixture torque-off WRITE unconfirmed')
        self.torque[motor] = 0
        if motor in self.off_ack_lost:
            raise BusTimeout('fixture off WRITE applied, acknowledgment lost')

    def goal(self, motor, position, speed, acceleration):
        self.trace.append(('goal', motor, position))
        if self.write_status_flags:
            raise MotorStatusError(motor, self.write_status_flags)
        super().goal(motor, position, speed, acceleration)
        if self.write_ack_lost:
            self.write_ack_lost = False
            raise BusTimeout('fixture WRITE acknowledgment timeout')


def manual_controller(recovery=True):
    bus, clock, events = LossBus(), Clock(), []
    motion = MotionController(bus, Profile(profile_value()), clock=clock, on_event=events.append)
    motion.connect_snapshot()
    motion.soft_watchdog = True
    motion.direct_targets = True
    motion.recover_read_timeouts = recovery
    motion.activate()
    bus.trace.clear()
    return motion, bus, clock, events


def request_drag(motion, clock):
    motion.input([.3, 0, 0, 0, 0, 0], motion.epoch, 1, True)
    clock.advance(.1)


def test_one_missing_read_recovers_from_fresh_measurements_and_discards_drag():
    motion, bus, clock, events = manual_controller()
    old_epoch = motion.epoch
    request_drag(motion, clock)
    bus.lost_reads = [2]
    motion.tick()
    assert motion.state == 'ACTIVE' and not motion.connection_recovering
    assert motion.hold_confirmed and not motion.gesture and motion.epoch > old_epoch
    assert motion.desired == bus.positions and bus.goals == bus.positions
    assert motion.snapshot()['sample_age_s'] == 0
    assert not bus.closed
    assert [e['kind'] for e in events][-1] == 'link_recovered'
    count = len(bus.writes)
    motion.input([.3, 0, 0, 0, 0, 0], old_epoch, 2, True)
    clock.advance(.1); motion.tick()
    assert len(bus.writes) == count and not motion.gesture
    motion.input([.3, 0, 0, 0, 0, 0], motion.epoch, 3, True)
    clock.advance(.1); motion.tick()
    assert bus.goals[1] > bus.positions[1]


def test_multiple_read_losses_back_off_with_no_writes_and_eventually_hold():
    motion, bus, clock, _ = manual_controller()
    request_drag(motion, clock)
    bus.lost_reads = [2, 4]
    count = len(bus.writes)
    motion.tick()
    assert motion.connection_recovering and motion.state == 'ACTIVE'
    assert not motion.hold_confirmed and not motion.gesture
    assert len(bus.writes) == count
    pending_epoch = motion.epoch
    motion.input([.3, 0, 0, 0, 0, 0], pending_epoch, 2, True)
    assert not motion.gesture
    reads = len(bus.trace)
    clock.advance(.05); motion.tick()
    assert len(bus.trace) == reads  # bounded retry, rather than a busy serial loop
    clock.advance(.06); motion.tick()
    assert not motion.connection_recovering and motion.hold_confirmed
    assert motion.epoch > pending_epoch and bus.goals == bus.positions


def test_persistent_loss_retains_owner_and_never_claims_or_writes_a_hold():
    motion, bus, clock, _ = manual_controller()
    request_drag(motion, clock)
    count = len(bus.writes)
    bus.persistent_loss = True
    for _ in range(12):
        motion.tick(); clock.advance(.11)
    snap = motion.snapshot()
    assert motion.bus is bus and not bus.closed and motion.state == 'ACTIVE'
    assert snap['connection_recovering'] and snap['hold_confirmed'] is False
    assert not motion.gesture and len(bus.writes) == count
    assert 'doğrulanmadı' in snap['message'] and snap['sample_age_s'] > 1
    assert motion.recovery_attempts < 12
    bus.persistent_loss = False
    clock.advance(1.1); motion.tick()
    assert motion.hold_confirmed and not motion.connection_recovering
    assert bus.goals == bus.positions and not motion.gesture


@pytest.mark.parametrize('lost_ack', [True, False])
def test_write_or_verification_loss_reads_before_new_measured_hold_without_goal_replay(lost_ack):
    motion, bus, clock, events = manual_controller()
    request_drag(motion, clock)
    requested = motion.desired[1]
    if lost_ack:
        bus.write_ack_lost = True
    else:
        bus.verify_read_lost = True
    motion.tick()
    goals = [event for event in bus.trace if event[0] == 'goal']
    assert goals[0] == ('goal', 1, requested)
    assert goals[1:] == [('goal', i, bus.positions[i]) for i in range(1, 7)]
    assert sum(position == requested for _, _, position in goals) == 1
    first_write = bus.trace.index(goals[0])
    hold_write = bus.trace.index(goals[1])
    assert [event for event in bus.trace[first_write+1:hold_write] if event[0] == 'feedback'] == [
        ('feedback', i) for i in range(1, 7)]
    paused = next(e for e in events if e['kind'] == 'link_paused')
    assert paused['write_ack_uncertain'] is lost_ack
    assert motion.state == 'ACTIVE' and not motion.gesture and motion.hold_confirmed


def test_release_read_loss_returns_paused_state_and_worker_recovers_it():
    motion, bus, clock, _ = manual_controller()
    request_drag(motion, clock)
    bus.lost_reads = [3]
    count = len(bus.writes)
    motion.hold()
    assert motion.connection_recovering and not motion.hold_confirmed
    assert len(bus.writes) == count and not motion.gesture
    motion.tick()
    assert not motion.connection_recovering and motion.hold_confirmed
    assert motion.state == 'ACTIVE' and bus.goals == bus.positions


def test_uncertain_hold_write_is_not_replayed_until_another_complete_read():
    motion, bus, clock, _ = manual_controller()
    bus.write_ack_lost = True
    motion.hold()
    assert motion.connection_recovering and not motion.hold_confirmed
    before = len(bus.trace)
    motion.tick()
    new_trace = bus.trace[before:]
    assert new_trace[:6] == [('feedback', i) for i in range(1, 7)]
    assert new_trace[6][0] == 'goal'
    assert motion.hold_confirmed and motion.state == 'ACTIVE'


def test_default_verified_mode_still_latches_timeout_and_motor_error_still_faults():
    motion, bus, _, _ = manual_controller(recovery=False)
    bus.persistent_loss = True
    motion.tick()
    assert motion.state == 'FAULT_UNCONFIRMED' and not motion.connection_recovering
    motion, bus, _, _ = manual_controller()
    bus.hardware_fault = True
    motion.tick()
    assert motion.state == 'FAULT_UNCONFIRMED' and not motion.connection_recovering
    assert motion.hold_confirmed is False


def test_disconnect_during_persistent_loss_does_not_report_a_confirmed_hold():
    motion, bus, _, _ = manual_controller()
    bus.persistent_loss = True
    bus.off_write_failed = bus.off_read_failed = set(range(1, 7))
    motion.tick(); motion.disconnect()
    assert bus.closed and motion.state == 'FAULT_UNCONFIRMED'
    assert motion.hold_confirmed is False and 'doğrulanamadı' in motion.message


def test_manual_disconnect_releases_all_torque_and_never_sends_holding_goals():
    motion, bus, _, _ = manual_controller()
    motion.input([.3, 0, 0, 0, 0, 0], motion.epoch, 1, True)
    count = len(bus.writes)
    motion.disconnect()
    assert [item for item in bus.trace if item[0] == 'off'] == [('off', i) for i in range(1, 7)]
    assert len(bus.writes) == count and set(bus.torque.values()) == {0}
    assert motion.state == 'DISCONNECTED' and motion.torque_release_confirmed
    assert bus.closed and not motion.gesture and 'torku kapalı' in motion.message


def test_verified_disconnect_still_holds_measured_pose_without_torque_off():
    motion, bus, _, _ = manual_controller(recovery=False)
    count = len(bus.writes)
    motion.disconnect()
    assert not [item for item in bus.trace if item[0] == 'off']
    assert len(bus.writes) == count + 6 and set(bus.torque.values()) == {1}
    assert motion.state == 'DISCONNECTED' and bus.closed


def test_opted_in_connection_recovery_before_activation_remains_read_only():
    bus, clock = LossBus(), Clock()
    motion = MotionController(bus, Profile(profile_value()), clock=clock)
    motion.connect_snapshot()
    motion.recover_read_timeouts = True
    bus.lost_reads = [2]
    motion.tick()
    assert motion.state == 'CONNECTED' and not motion.connection_recovering
    assert bus.writes == [] and not motion.may_be_live
    assert motion.hold_confirmed is None


def test_dedicated_emergency_bus_authority_only_allows_the_exact_sram_byte(monkeypatch):
    from figbot_lab._reference_protocol import Bus
    seen = []
    monkeypatch.setattr(Bus, 'transact', lambda *args, **kwargs: seen.append((args, kwargs)))
    bus = MotionBus(object())
    for motor in (0, 7, 254, True):
        with pytest.raises(BusError):
            bus.disable_torque(motor, authority=_EMERGENCY_TORQUE_OFF)
    with pytest.raises(BusError): bus.disable_torque(1)
    with pytest.raises(BusError): bus.transact(1, 3, b'\x28\0')
    assert seen == []
    bus.disable_torque(1, authority=_EMERGENCY_TORQUE_OFF)
    assert seen[0][0][1:] == (1, 3, b'\x28\0')
    assert seen[0][1] == {'response_size': 0}


def test_emergency_attempts_every_motor_once_and_verifies_each_without_write_replay():
    motion, bus, _, _ = manual_controller()
    bus.off_write_failed = {2}
    bus.off_ack_lost = {3}
    bus.off_read_failed = {4}
    count = len(bus.writes)
    result = motion.emergency_torque_off('fixture physical overheating', thermal=True)
    assert [item for item in bus.trace if item[0] == 'off'] == [('off', i) for i in range(1, 7)]
    assert [item for item in bus.trace if item[0] == 'read'] == [('read', i, 40) for i in range(1, 7)]
    assert result['motors'][3]['write_acknowledged'] is False
    assert result['motors'][3]['torque_off_confirmed'] is True  # actual READ settles the missing ACK
    assert result['motors'][2]['torque_off_confirmed'] is False
    assert result['motors'][4]['torque_off_confirmed'] is False
    assert motion.state == 'THERMAL_UNCONFIRMED' and motion.thermal_latched
    assert not motion.gesture and not motion.connection_recovering
    assert not motion.torque_release_confirmed and len(bus.writes) == count
    motion.hold(); motion.fault('later error'); motion.disconnect()
    assert len(bus.writes) == count and bus.closed
    assert motion.state == 'FAULT_UNCONFIRMED' and 'beslemesini kesin' in motion.message


def test_confirmed_emergency_cancels_pending_input_and_reads_only_until_explicit_reset():
    motion, bus, clock, _ = manual_controller()
    request_drag(motion, clock)
    count = len(bus.writes)
    result = motion.emergency_torque_off('fixture user stop')
    assert result['torque_release_confirmed'] and motion.state == 'EMERGENCY_TORQUE_OFF'
    assert set(bus.torque.values()) == {0}
    with pytest.raises(ValueError):
        motion.input([.3, 0, 0, 0, 0, 0], motion.epoch, 2, True)
    clock.advance(.6); motion.tick()
    motion.hold(); motion.fault('late browser error')
    assert len(bus.writes) == count and not motion.gesture
    assert len([item for item in bus.trace if item[0] == 'off']) == 6
    with pytest.raises(ValueError): motion.activate()


class ThermalManualController(MotionController):
    def read_all(self, checked=True):
        rows = super().read_all(checked=False)
        if checked:
            self.check_manual_temperature(rows)
        return rows


def thermal_controller():
    bus, clock = LossBus(), Clock()
    motion = ThermalManualController(bus, Profile(profile_value()), clock=clock)
    motion.connect_snapshot(); motion.soft_watchdog = True; motion.recover_read_timeouts = True
    motion.activate(); bus.trace.clear()
    return motion, bus, clock


@pytest.mark.parametrize('operation', ['tick', 'hold', 'recovery', 'fault'])
def test_thermal_detection_cuts_torque_in_every_path_and_never_sends_holding_goals(operation):
    motion, bus, clock = thermal_controller()
    bus.temperatures[4] = 55
    count = len(bus.writes)
    if operation == 'tick': motion.tick()
    elif operation == 'hold': motion.hold()
    elif operation == 'fault': motion.fault('fixture other error')
    else:
        bus.lost_reads = [2]
        motion.tick()
    assert len(bus.writes) == count
    assert set(bus.torque.values()) == {0} and motion.state == 'THERMAL_CUTOFF'
    assert motion.thermal_latched and motion.emergency_latched and motion.torque_release_confirmed
    assert not motion.hold_confirmed and not motion.connection_recovering
    clock.advance(.6); motion.tick()
    assert motion.rows[4]['temperature'] == 55 and len(bus.writes) == count
    assert len([item for item in bus.trace if item[0] == 'off']) == 6


def test_manual_cooling_hysteresis_requires_fresh_all_six_and_no_automatic_resume():
    motion, bus, clock = thermal_controller()
    bus.temperatures[4] = 61
    motion.tick()
    count = len(bus.writes)
    bus.temperatures[4] = 46
    clock.advance(.6); motion.tick()
    with pytest.raises(ValueError, match='45'):
        motion.require_manual_cooling(motion.rows)
    assert motion.thermal_latched and len(bus.writes) == count
    bus.temperatures[4] = 45
    clock.advance(.6); motion.tick()
    assert motion.state == 'THERMAL_CUTOFF' and not motion.gesture and len(bus.writes) == count
    old_rows = dict(motion.rows)
    with pytest.raises(ValueError, match='yeni sıcaklık'):
        motion.require_manual_cooling(old_rows)
    clock.advance(.3)
    with pytest.raises(ValueError, match='yeni sıcaklık'):
        motion.require_manual_cooling(motion.rows)
    motion.read_all(checked=False)
    motion.require_manual_cooling(motion.rows)  # an explicit activation path does this
    assert motion.state == 'CONNECTED' and not motion.thermal_latched
    assert not motion.emergency_latched and not motion.may_be_live and len(bus.writes) == count
    motion.activate()
    assert motion.state == 'ACTIVE' and len(bus.writes) > count


def test_activation_preflight_detects_hot_motor_and_releases_existing_torque():
    bus, clock = LossBus(), Clock()
    bus.torque = {i: 1 for i in range(1, 7)}
    motion = ThermalManualController(bus, Profile(profile_value()), clock=clock)
    motion.connect_snapshot()
    bus.temperatures[4] = 55
    with pytest.raises(MotorOverheat): motion.activate()
    assert bus.writes == [] and set(bus.torque.values()) == {0}
    assert motion.state == 'THERMAL_CUTOFF' and motion.thermal_latched


def test_server_opted_in_passive_pose_monitor_cuts_existing_hot_torque():
    bus, clock = LossBus(), Clock()
    bus.torque = {i: 1 for i in range(1, 7)}
    bus.temperatures[4] = 61
    motion = MotionController(bus, clock=clock)
    motion.manual_temperature_monitor = True
    motion.connect_snapshot()
    assert bus.writes == [] and not [item for item in bus.trace if item[0] == 'off']
    assert set(bus.torque.values()) == {1}  # connect_snapshot itself remains READ-only
    motion.tick()
    assert motion.state == 'THERMAL_CUTOFF' and motion.thermal_latched
    assert set(bus.torque.values()) == {0} and bus.writes == []
    assert motion.snapshot()['manual_temperature_monitor']


def test_default_pose_snapshot_and_tick_do_not_enable_manual_thermal_monitor():
    bus, clock = LossBus(), Clock()
    bus.torque = {i: 1 for i in range(1, 7)}
    bus.temperatures[4] = 61
    motion = MotionController(bus, clock=clock)
    motion.connect_snapshot(); motion.tick()
    assert motion.state == 'CONNECTED' and not motion.thermal_latched
    assert bus.writes == [] and not [item for item in bus.trace if item[0] == 'off']
    assert set(bus.torque.values()) == {1}


@pytest.mark.parametrize('operation', ['tick', 'hold', 'activation', 'write', 'recovery', 'fault'])
@pytest.mark.parametrize('flags', [0x04, 0x20, 0x40])
def test_servo_protection_flags_latch_torque_off_and_never_send_a_holding_position(operation, flags):
    motion, bus, clock, _ = manual_controller()
    count = len(bus.writes)
    if operation == 'fault':
        motion.fault(MotorStatusError(2, flags))
    elif operation == 'write':
        bus.write_status_flags = flags
        request_drag(motion, clock)
        motion.tick()
    else:
        bus.motor_status_flags = flags
        if operation == 'activation':
            motion.state = 'CONNECTED'
            with pytest.raises(MotorStatusError): motion.activate()
        elif operation == 'hold': motion.hold()
        elif operation == 'recovery':
            bus.lost_reads = [1]
            motion.tick()
        else: motion.tick()
    assert len(bus.writes) == count
    assert set(bus.torque.values()) == {0} and motion.emergency_latched
    assert motion.thermal_latched is bool(flags & 0x04)
    assert motion.state == ('THERMAL_CUTOFF' if flags & 0x04 else 'EMERGENCY_TORQUE_OFF')
    assert len([item for item in bus.trace if item[0] == 'off']) == 6
    motion.fault(MotorStatusError(2, flags))
    motion.hold(); clock.advance(.6); motion.tick()
    assert len(bus.writes) == count
    assert len([item for item in bus.trace if item[0] == 'off']) == 6
