from dataclasses import replace
import pytest

from figbot_lab.calibration import read_settings
from figbot_lab.relative_motion import RelativeController
from figbot_lab.virtual_motion import MotionController, Profile
from figbot_lab.virtual_server import Application
from test_motion_connection_stability import LossBus
from test_virtual_leader import Clock, profile_value


class FiveBus(LossBus):
    def read(self, motor, address, size):
        assert motor != 6, 'Absent motor must never be polled'
        data = super().read(motor, address, size)
        if address == 0:
            raw = bytearray(data); raw[13:16] = bytes([70, 140, 40]); return bytes(raw)
        return data
    def feedback_state(self, motor):
        assert motor != 6, 'Absent motor must never be polled'
        return super().feedback_state(motor)
    def goal(self, motor, *values):
        assert motor != 6, 'Absent motor must never receive motion'
        return super().goal(motor, *values)
    def disable_torque(self, motor, **kwargs):
        assert motor != 6, 'Absent motor must never receive torque commands'
        return super().disable_torque(motor, **kwargs)


def controller():
    bus, clock = FiveBus(), Clock()
    settings = read_settings(bus, motor_ids=(1, 2, 3, 4, 5))
    angles = [0, -.3, .7, .2, 0, .1]
    motion = RelativeController(bus, settings, {i: bus.positions[i] for i in range(1, 6)}, angles, clock=clock)
    return motion, bus, clock, angles


def test_five_motor_activation_stream_hold_and_release_never_touch_six():
    motion, bus, clock, angles = controller()
    motion.activate()
    request = list(angles); request[3] += .1; request[5] += 1
    motion.input(request, motion.epoch, 1, True)
    clock.advance(.1); motion.tick()
    assert set(bus.goals) == set(range(1, 6)) and bus.goals[4] > bus.positions[4]
    snap = motion.snapshot()
    assert snap['gripper_available'] is False and snap['angles'][5] == angles[5]
    assert snap['trial_bounds'][5] == [angles[5], angles[5]]
    motion.hold(); motion.disconnect()
    assert motion.torque_release_confirmed and bus.closed
    assert [r[1] for r in bus.trace if r[0] == 'off'] == list(range(1, 6))


def test_five_motor_overheat_and_cooldown_apply_to_present_motors():
    motion, bus, clock, angles = controller(); motion.activate()
    bus.temperatures[4] = 55; clock.advance(.1); motion.tick()
    count = len(bus.writes)
    assert motion.thermal_latched and motion.torque_release_confirmed
    bus.temperatures[4] = 46
    with pytest.raises(ValueError, match='45'): motion.activate()
    assert len(bus.writes) == count
    bus.temperatures[4] = 45; motion.activate()
    assert motion.state == 'ACTIVE' and len(bus.writes) == count + 5


def test_five_motor_timeout_recovers_without_missing_motor_or_old_target():
    motion, bus, clock, angles = controller(); motion.activate()
    request = list(angles); request[4] += .3
    motion.input(request, motion.epoch, 1, True)
    bus.persistent_loss = True; clock.advance(.1); motion.tick()
    assert motion.connection_recovering and not motion.gesture
    bus.persistent_loss = False; clock.advance(1); motion.tick()
    assert not motion.connection_recovering and not motion.gesture
    assert bus.goals[5] == bus.positions[5]


def test_five_motor_server_invalidates_old_home_before_any_write():
    app = Application()
    motion, bus, clock, angles = controller(); app.motion = motion
    app.hardware = {'active_motor_ids': [1, 2, 3, 4, 5], 'closed_home_valid': False}
    with pytest.raises(ValueError, match='Motor değişti'): app.action('home', {'angles': angles})
    assert bus.writes == []
    result = app.action('activate_trial', {'angles': angles})
    assert result['active_motor_ids'] == [1, 2, 3, 4, 5] and not result['home_available']


def test_old_verified_six_motor_profile_cannot_be_used_with_five_motors():
    with pytest.raises(ValueError):
        MotionController(FiveBus(), Profile(profile_value()), active_ids=(1, 2, 3, 4, 5))
