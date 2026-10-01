import json
import math
import pytest
from test_virtual_leader import FakeBus, Clock
from figbot_lab.common import JOINTS
from figbot_lab.calibration import read_settings
from figbot_lab.relative_motion import RelativeProfile, RelativeController, RelativeMotionBus, FULL_SPEED, FULL_ACCELERATION
from figbot_lab.virtual_motion import COUNTS_PER_RADIAN
from figbot_lab.virtual_server import Application


def fixture():
    bus, clock = FakeBus(), Clock()
    bus.positions[3] = 3999
    settings = read_settings(bus)
    # Fixture hardware maximum temperature, no actual EEPROM writes.
    for entry in settings.values():
        data = bytearray.fromhex(entry['registers_0_39_hex']); data[13:16] = bytes([70,140,40])
        entry['registers_0_39_hex'] = data.hex()
    angles = [.1, -1.7, 1.5, 1.3, 1.6, -.1]
    return bus, clock, settings, angles


def closed_reference(bus, settings, angles):
    return {'positions': dict(bus.positions), 'closed_angles': list(angles),
            'homing_offsets': {i: settings[name]['homing_offset_encoded']
                               for i, name in enumerate(JOINTS, 1)}}


def test_relative_anchor_roundtrip_and_full_encoder_range_without_wrap():
    bus, _, settings, angles = fixture()
    profile = RelativeProfile(bus.positions, angles, settings)
    assert profile.targets(angles) == bus.positions
    assert profile.angles(bus.positions) == angles
    assert not profile.verified
    assert profile.targets([v + 10 for v in angles])[3] == 4095
    assert profile.targets([v - 10 for v in angles])[1] == 0
    assert profile.targets([v + 1 for v in angles])[1] > 2048 + 256
    for invalid in ([math.nan]*6, [True]*6, [0]*5):
        with pytest.raises(ValueError): profile.targets(invalid)


def test_trial_activation_stream_hold_watchdog_and_verified_mode_gate():
    bus, clock, settings, angles = fixture()
    motion = RelativeController(bus, settings, dict(bus.positions), angles, clock=clock)
    motion.activate()
    assert all(position == bus.positions[i] for i, position, _, _ in bus.writes)
    snap = motion.snapshot()
    assert snap['origin_excursion_limit'] is None and snap['direct_targets']
    assert all(speed == FULL_SPEED and acceleration == FULL_ACCELERATION for _, _, speed, acceleration in bus.writes)
    assert snap['state'] == 'ACTIVE' and not snap['profile_verified']
    assert snap['control_mode'] == 'RELATIVE_TRIAL' and snap['calibration'] == 'UNVERIFIED'
    request = angles.copy(); request[0] += .1
    motion.input(request, motion.epoch, 1, True)
    clock.advance(.1); motion.tick()
    assert bus.goals[1] == round(2048 + .1 * COUNTS_PER_RADIAN)
    assert all(bus.goals[i] == bus.positions[i] for i in range(2, 7))
    epoch = motion.epoch
    motion.hold()
    assert bus.goals[1] == bus.positions[1]
    motion.input(request, epoch, 2, True)
    assert not motion.gesture and bus.goals[1] == bus.positions[1]
    motion.input(request, motion.epoch, 3, True)
    clock.advance(.4); motion.tick()
    assert motion.state == 'ACTIVE' and motion.gesture
    clock.advance(1.1); motion.tick()
    assert motion.state == 'ACTIVE' and not motion.gesture
    assert all(bus.goals[i] == bus.positions[i] for i in range(1,7))
    app = Application(); app.motion = motion
    with pytest.raises(ValueError): app.action('activate', {})


def test_relative_stream_pause_keeps_session_and_discards_old_commands():
    bus, clock, settings, angles = fixture()
    motion = RelativeController(bus, settings, dict(bus.positions), angles, clock=clock)
    motion.activate(); epoch = motion.epoch
    request = angles.copy(); request[0] += .2
    motion.input(request, epoch, 1, True)
    clock.advance(1.1); motion.tick()
    assert motion.state == 'ACTIVE' and motion.epoch > epoch
    writes = len(bus.writes)
    motion.input(request, epoch, 2, True)
    clock.advance(.1); motion.tick()
    assert not motion.gesture and len(bus.writes) == writes
    motion.input(request, motion.epoch, 3, True)
    clock.advance(.1); motion.tick()
    assert motion.state == 'ACTIVE' and bus.goals[1] > bus.positions[1]


def test_manual_voltage_uses_preserved_registers_not_prototype_gate():
    from dataclasses import replace
    bus, clock, settings, angles = fixture()
    original = bus.feedback
    bus.feedback = lambda i: replace(original(i),voltage=5.8,current_raw=180) if i==1 else original(i)
    motion = RelativeController(bus,settings,dict(bus.positions),angles,clock=clock)
    motion.activate();clock.advance(.1);motion.tick()
    assert motion.state == 'ACTIVE'
    bus.feedback = lambda i: replace(original(i),voltage=3.2) if i==1 else original(i)
    clock.advance(.1);motion.tick()
    assert motion.state.startswith('FAULT')
    assert 'hardware-configured' in motion.message


@pytest.mark.parametrize('temperature', [46, 54])
def test_manual_activation_waits_for_45c_before_any_goal_write(temperature):
    from dataclasses import replace
    bus, clock, settings, angles = fixture()
    original = bus.feedback
    bus.feedback = lambda i: replace(original(i), temperature=temperature if i == 2 else 30)
    motion = RelativeController(bus, settings, dict(bus.positions), angles, clock=clock)
    with pytest.raises(ValueError):
        motion.activate()
    assert bus.writes == [] and motion.state != 'ACTIVE'


def test_manual_activation_at_55c_cuts_existing_torque_without_goal_writes():
    from dataclasses import replace
    from figbot_lab.virtual_motion import MotorOverheat
    bus, clock, settings, angles = fixture()
    bus.torque = {i: 1 for i in range(1, 7)}
    bus.disable_torque = lambda motor, **kwargs: bus.torque.__setitem__(motor, 0)
    original = bus.feedback
    bus.feedback = lambda i: replace(original(i), temperature=55 if i == 4 else 30)
    motion = RelativeController(bus, settings, dict(bus.positions), angles, clock=clock)
    with pytest.raises(MotorOverheat):
        motion.activate()
    assert bus.writes == [] and set(bus.torque.values()) == {0}
    assert motion.state != 'ACTIVE'


def test_manual_overheat_cuts_torque_and_never_automatically_resumes_or_holds():
    from dataclasses import replace
    bus, clock, settings, angles = fixture()
    bus.disable_torque = lambda motor, **kwargs: bus.torque.__setitem__(motor, 0)
    original = bus.feedback
    motion = RelativeController(bus, settings, dict(bus.positions), angles, clock=clock)
    motion.activate(); writes = len(bus.writes)
    request = angles.copy(); request[0] += .2
    motion.input(request, motion.epoch, 1, True)
    bus.feedback = lambda i: replace(original(i), temperature=55 if i == 4 else 30)
    clock.advance(.1); motion.tick()
    assert set(bus.torque.values()) == {0} and len(bus.writes) == writes
    assert motion.state != 'ACTIVE' and not motion.gesture
    bus.feedback = original
    clock.advance(1); motion.tick(); motion.hold()
    assert set(bus.torque.values()) == {0} and len(bus.writes) == writes
    assert motion.state != 'ACTIVE'


def test_manual_activation_at_45c_is_allowed_after_fresh_read():
    from dataclasses import replace
    bus, clock, settings, angles = fixture()
    original = bus.feedback
    bus.feedback = lambda i: replace(original(i), temperature=45)
    motion = RelativeController(bus, settings, dict(bus.positions), angles, clock=clock)
    motion.activate()
    assert motion.state == 'ACTIVE' and bus.writes


def test_home_overheat_during_initial_hold_never_queues_folded_target():
    from dataclasses import replace
    bus, clock, settings, angles = fixture()
    home = closed_reference(bus, settings, angles)
    bus.positions[1] += 300
    bus.disable_torque = lambda motor, **kwargs: bus.torque.__setitem__(motor, 0)
    original = bus.feedback
    motion = RelativeController(bus, settings, dict(bus.positions), angles,
                                home_reference=home, clock=clock)
    motion.activate(); writes = len(bus.writes)
    bus.feedback = lambda i: replace(original(i), temperature=55 if i == 4 else 30)
    motion.home()
    assert set(bus.torque.values()) == {0} and len(bus.writes) == writes
    assert not motion.homing and not motion.gesture
    assert motion.desired != home['positions'] and motion.state != 'ACTIVE'


def test_connected_manual_session_cuts_rising_temperature_before_activation():
    from dataclasses import replace
    bus, clock, settings, angles = fixture()
    bus.torque = {i: 1 for i in range(1, 7)}
    bus.disable_torque = lambda motor, **kwargs: bus.torque.__setitem__(motor, 0)
    original = bus.feedback
    bus.feedback = lambda i: replace(original(i), temperature=55 if i == 4 else 30)
    motion = RelativeController(bus, settings, dict(bus.positions), angles, clock=clock)
    clock.advance(.1); motion.tick()
    assert motion.thermal_latched and motion.emergency_latched
    assert bus.writes == [] and set(bus.torque.values()) == {0}


def test_firmware_fault_in_manual_cooling_preflight_cuts_without_goal_writes():
    from figbot_lab._reference_protocol import MotorStatusError
    bus, clock, settings, angles = fixture()
    bus.torque = {i: 1 for i in range(1, 7)}
    bus.disable_torque = lambda motor, **kwargs: bus.torque.__setitem__(motor, 0)
    bus.feedback_state = lambda _: (_ for _ in ()).throw(MotorStatusError(4, 4))
    motion = RelativeController(bus, settings, dict(bus.positions), angles, clock=clock)
    with pytest.raises(MotorStatusError):
        motion.activate()
    assert motion.emergency_latched and set(bus.torque.values()) == {0} and bus.writes == []


def test_firmware_fault_in_home_saved_offset_read_cuts_without_holding():
    from figbot_lab._reference_protocol import MotorStatusError
    bus, clock, settings, angles = fixture()
    home = closed_reference(bus, settings, angles)
    bus.disable_torque = lambda motor, **kwargs: bus.torque.__setitem__(motor, 0)
    motion = RelativeController(bus, settings, dict(bus.positions), angles,
                                home_reference=home, clock=clock)
    motion.activate(); writes = len(bus.writes)
    original = bus.read
    def failed_read(motor, address, size):
        if motor == 4 and address == 0:
            raise MotorStatusError(4, 4)
        return original(motor, address, size)
    bus.read = failed_read
    with pytest.raises(MotorStatusError):
        motion.home()
    assert motion.emergency_latched and set(bus.torque.values()) == {0}
    assert len(bus.writes) == writes and not motion.homing


def test_home_timeout_keeps_thermal_cutoff_message_and_never_claims_position_held():
    from dataclasses import replace
    bus, clock, settings, angles = fixture()
    home = closed_reference(bus, settings, angles)
    bus.disable_torque = lambda motor, **kwargs: bus.torque.__setitem__(motor, 0)
    original = bus.feedback
    motion = RelativeController(bus, settings, dict(bus.positions), angles,
                                home_reference=home, clock=clock)
    motion.activate(); bus.positions[1] += 300; motion.home()
    writes = len(bus.writes)
    bus.feedback = lambda i: replace(original(i), temperature=55 if i == 4 else 30)
    clock.advance(16); motion.tick()
    assert motion.thermal_latched and motion.emergency_latched
    assert 'poz tutuluyor' not in motion.message and not motion.homing
    assert len(bus.writes) == writes and set(bus.torque.values()) == {0}


def test_registered_hardware_bounds_preserved_without_initial_pose_window():
    bus, _, settings, angles = fixture()
    settings[JOINTS[0]]['register_min'] = 100
    settings[JOINTS[0]]['register_max'] = 3900
    p = RelativeProfile(bus.positions, angles, settings)
    assert p.targets([v+10 for v in angles])[1] == 3900
    assert p.targets([v-10 for v in angles])[1] == 100


def test_home_uses_saved_folded_pose_and_rebases_corrupted_relative_calibration():
    bus, clock, settings, angles = fixture()
    home = closed_reference(bus, settings, angles)
    bus.positions[1] += 300; bus.positions[2] += 200
    wrong_angles = [angle + .3 for angle in angles]
    motion = RelativeController(bus, settings, dict(bus.positions), wrong_angles,
                                home_reference=home, clock=clock)
    motion.activate(); origin = dict(bus.positions)
    snapshot = motion.snapshot()
    assert snapshot['home_available'] and snapshot['home_raw'] == home['positions']
    assert snapshot['home_angles'] == angles and snapshot['angles'] == wrong_angles
    motion.home(); clock.advance(2); motion.tick()
    assert motion.homing and motion.state == 'ACTIVE'
    assert bus.goals == home['positions']
    assert motion.profile.origin_raw == origin and motion.profile.origin_angles == wrong_angles
    pre_completion_epoch = motion.epoch
    bus.positions = {i: p + 3 for i, p in home['positions'].items()}
    clock.advance(2); motion.tick()
    assert not motion.homing and not motion.gesture and motion.state == 'ACTIVE'
    assert motion.snapshot()['angles'] == angles
    assert motion.profile.origin_raw == bus.positions and motion.profile.origin_angles == angles
    assert motion.snapshot()['home_raw'] == home['positions']
    assert not motion.snapshot()['profile_verified'] and motion.snapshot()['calibration'] == 'UNVERIFIED'
    assert motion.profile.targets(angles) == bus.positions
    assert motion.snapshot()['home_completed_epoch'] == motion.epoch > pre_completion_epoch
    writes = len(bus.writes)
    motion.input(wrong_angles, pre_completion_epoch, 1, True)
    assert not motion.gesture and len(bus.writes) == writes


def test_hold_cancels_home_and_home_timeout_does_not_kill_session():
    bus, clock, settings, angles = fixture()
    home = closed_reference(bus, settings, angles)
    motion = RelativeController(bus, settings, dict(bus.positions), angles,
                                home_reference=home, clock=clock)
    motion.activate(); bus.positions[1] += 300
    motion.home(); motion.hold(); clock.advance(2); motion.tick()
    assert not motion.homing and bus.goals[1] == bus.positions[1]
    motion.home(); clock.advance(16); motion.tick()
    assert not motion.homing and motion.state == 'ACTIVE'
    assert bus.goals[1] == bus.positions[1]


def test_missing_closed_home_is_unavailable_and_does_not_use_session_origin():
    bus, clock, settings, angles = fixture()
    motion = RelativeController(bus, settings, dict(bus.positions), angles, clock=clock)
    motion.activate(); writes = len(bus.writes)
    snapshot = motion.snapshot()
    assert not snapshot['home_available'] and snapshot['home_angles'] is None and snapshot['home_raw'] is None
    with pytest.raises(ValueError, match='kaydı bulunamadı'):
        motion.home()
    assert len(bus.writes) == writes


@pytest.mark.parametrize('field,value', [('positions', {str(i): 4096 for i in range(1, 7)}),
                                       ('positions', {str(i): True for i in range(1, 7)}),
                                       ('positions', {'1': 2000}),
                                       ('homing_offsets', {str(i): 86 for i in range(1, 7)}),
                                       ('closed_angles', [float('nan')] * 6)])
def test_invalid_saved_home_rejected_before_writes(field, value):
    bus, clock, settings, angles = fixture()
    home = closed_reference(bus, settings, angles); home[field] = value
    with pytest.raises(ValueError):
        RelativeController(bus, settings, dict(bus.positions), angles,
                           home_reference=home, clock=clock)
    assert bus.writes == []


def test_saved_home_checks_fresh_offsets_before_current_pose_hold(monkeypatch):
    bus, clock, settings, angles = fixture()
    home = closed_reference(bus, settings, angles)
    motion = RelativeController(bus, settings, dict(bus.positions), angles,
                                home_reference=home, clock=clock)
    motion.activate(); writes = len(bus.writes)
    settings[JOINTS[1]]['homing_offset_encoded'] += 1
    monkeypatch.setattr('figbot_lab.calibration.read_settings', lambda _: settings)
    with pytest.raises(ValueError, match='ofseti'):
        motion.home()
    assert len(bus.writes) == writes and not motion.homing


def test_home_does_not_rebase_from_stale_measurements(monkeypatch):
    bus, clock, settings, angles = fixture()
    home = closed_reference(bus, settings, angles)
    wrong_angles = [angle + .3 for angle in angles]
    motion = RelativeController(bus, settings, dict(bus.positions), wrong_angles,
                                home_reference=home, clock=clock)
    motion.activate(); motion.home()
    monkeypatch.setattr(motion, 'read_all', lambda checked=True: motion.rows)
    clock.advance(.1); motion.tick()
    assert motion.homing and motion.profile.origin_angles == wrong_angles


def test_link_loss_cancels_home_without_rebase_or_replaying_saved_target():
    from figbot_lab._reference_protocol import BusTimeout
    bus, clock, settings, angles = fixture()
    home = closed_reference(bus, settings, angles)
    bus.positions[1] += 300
    wrong_angles = [angle + .3 for angle in angles]
    motion = RelativeController(bus, settings, dict(bus.positions), wrong_angles,
                                home_reference=home, clock=clock)
    motion.activate(); motion.home()
    original = bus.feedback_state
    bus.feedback_state = lambda _: (_ for _ in ()).throw(BusTimeout('dropped read'))
    clock.advance(.1); motion.tick()
    assert motion.connection_recovering and not motion.homing
    assert motion.profile.origin_angles == wrong_angles
    assert motion.desired == bus.positions
    bus.feedback_state = original
    clock.advance(.1); motion.tick()
    assert not motion.connection_recovering and motion.state == 'ACTIVE'
    assert not motion.homing and bus.goals == bus.positions
    assert motion.profile.origin_angles == wrong_angles


def test_home_hold_timeout_does_not_queue_saved_home(monkeypatch):
    from figbot_lab._reference_protocol import BusTimeout
    bus, clock, settings, angles = fixture()
    home = closed_reference(bus, settings, angles)
    bus.positions[1] += 300
    motion = RelativeController(bus, settings, dict(bus.positions), angles,
                                home_reference=home, clock=clock)
    motion.activate()
    monkeypatch.setattr('figbot_lab.calibration.read_settings', lambda _: settings)
    bus.feedback_state = lambda _: (_ for _ in ()).throw(BusTimeout('dropped read'))
    motion.home()
    assert motion.connection_recovering and not motion.homing
    assert motion.desired == bus.positions and motion.state == 'ACTIVE'


def test_fault_diagnostic_survives_reconnection(tmp_path, monkeypatch):
    app = Application()
    monkeypatch.setattr('figbot_lab.virtual_server.new_run', lambda _: tmp_path)
    app.event({'kind':'feedback','motors':{1:{'current_raw':180}}})
    app.event({'kind':'fault','message':'fixture fault','state':'FAULT_HOLD'})
    recorded = json.loads((tmp_path/'fault.json').read_text())
    assert recorded['fault']['message'] == 'fixture fault'
    assert recorded['recent_events'][0]['motors']['1']['current_raw'] == 180
    assert app.state()['last_fault']['message'] == 'fixture fault'


def test_full_speed_packet_guard_accepts_only_explicit_finite_profile(monkeypatch):
    from figbot_lab._reference_protocol import Bus, BusError
    seen = []
    monkeypatch.setattr(Bus, 'transact', lambda self, *args: seen.append(args) or b'')
    bus = RelativeMotionBus(object())
    good = b'\x29' + bytes([FULL_ACCELERATION]) + (2000).to_bytes(2,'little') + b'\0\0' + FULL_SPEED.to_bytes(2,'little')
    bus.transact(1, 3, good)
    assert len(seen) == 1
    for motor, data in [(1, good[:-2]+b'\0\0'), (254, good), (1, b'\x28\0'), (1, b'\x1f\0\0')]:
        with pytest.raises(BusError): bus.transact(motor, 3, data)
    assert len(seen) == 1


def test_relative_recording_remains_unverified(tmp_path, monkeypatch):
    bus, clock, settings, angles = fixture()
    app = Application()
    app.motion = RelativeController(bus, settings, dict(bus.positions), angles, clock=clock)
    app.motion.activate()
    monkeypatch.setattr('figbot_lab.virtual_server.new_run', lambda _: tmp_path)
    app.action('record/start', {}); app.action('record/stop', {})
    saved = json.loads((tmp_path/'session.json').read_text())
    assert saved['source'] == 'COMMANDED_MOTOR_ACTIONS_RELATIVE_TRIAL'
    assert saved['training_ready'] is False


def test_server_trial_route_anchors_current_pose_and_preserves_full_gate(monkeypatch):
    from figbot_lab.virtual_motion import MotionController
    bus, clock, settings, angles = fixture()
    app = Application(); app.motion = MotionController(bus, clock=clock)
    app.hardware = {}  # six-motor reference fixture
    app.closed_home = closed_reference(bus, settings, angles)
    monkeypatch.setattr('figbot_lab.calibration.read_settings', lambda _: settings)
    with pytest.raises(ValueError): app.action('activate_trial', {'angles': [math.nan]*6})
    assert bus.writes == []
    result = app.action('activate_trial', {'angles': angles})
    assert result['state'] == 'ACTIVE' and result['angles'] == angles
    assert result['trial_origin_raw'] == bus.positions and not result['profile_verified']
    assert 'speed3400 accel50' in result['profile_note']
    assert bus.writes and all(position == bus.positions[i] for i, position, _, _ in bus.writes)
    with pytest.raises(ValueError): app.action('activate', {})
