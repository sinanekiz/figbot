import copy
import json
import math
import threading
import urllib.request
import urllib.error
from dataclasses import replace
import pytest
from figbot_lab._reference_protocol import Feedback, BusError
from figbot_lab.common import JOINTS, load_json, ROOT
from figbot_lab.virtual_motion import Profile, MotionBus, MotionController, RATE, SPEED
from figbot_lab.virtual_server import Application, server_for


def profile_value():
    return {'status': 'VERIFIED', 'evidence': 'TEST FIXTURE ONLY', 'joints': {
        name: {'id': i, 'zero_raw': 2048, 'direction': -1 if i == 3 else 1,
               'raw_min': 1500, 'raw_max': 2600, 'offset_encoded': 85, 'evidence': 'TEST FIXTURE ONLY'}
        for i, name in enumerate(JOINTS, 1)}}


class Clock:
    def __init__(self): self.now = 10.
    def __call__(self): return self.now
    def advance(self, value): self.now += value


class FakeBus:
    def __init__(self):
        self.positions = {i: 2048 for i in range(1, 7)}
        self.torque = {i: 0 for i in range(1, 7)}
        self.goals, self.writes = {}, []
        self.profiles = {}
        self.failed = False
        self.closed = False
    def read(self, i, address, size):
        if self.failed: raise BusError('test cable loss')
        if address == 0:
            data = bytearray(40); data[3:5] = (777).to_bytes(2, 'little'); data[5] = i
            data[31:33] = (85).to_bytes(2, 'little'); return bytes(data)
        if address == 40: return bytes([self.torque[i]])
        if address == 41:
            position = self.goals.get(i, self.positions[i])
            speed, acceleration = self.profiles.get(i, (SPEED, 1))
            return bytes([acceleration]) + position.to_bytes(2, 'little') + b'\0\0' + speed.to_bytes(2, 'little')
        if address == 42: return self.goals.get(i, self.positions[i]).to_bytes(2, 'little')
        raise AssertionError((i, address, size))
    def feedback(self, i):
        if self.failed: raise BusError('test cable loss')
        return Feedback(self.positions[i], 0, 12.2, 30, 0, False)
    def feedback_state(self, i): return self.feedback(i), self.torque[i]
    def goal(self, i, position, speed, acceleration):
        if self.failed: raise BusError('test cable loss')
        self.goals[i] = position; self.torque[i] = 1
        self.profiles[i] = speed, acceleration
        self.writes.append((i, position, speed, acceleration))
    def write(self, i, address, data):
        assert address == 40 and data == b'\1'
        self.torque[i] = 1
    def close(self): self.closed = True


def controller(profile=True):
    clock, bus = Clock(), FakeBus()
    motion = MotionController(bus, Profile(profile_value()) if profile else None, clock)
    motion.connect_snapshot()
    return motion, bus, clock


def test_unverified_template_rejected():
    with pytest.raises(ValueError): Profile(load_json(ROOT / 'configs/virtual_leader.template.json'))


@pytest.mark.parametrize('field,value', [('direction', 0), ('direction', True), ('raw_min', -1), ('raw_max', 4096), ('offset_encoded', None), ('zero_raw', float('nan')), ('evidence', '')])
def test_bad_profile_rejected(field, value):
    data = profile_value(); data['joints']['shoulder_pan'][field] = value
    with pytest.raises(ValueError): Profile(data)


def test_bidirectional_profile_and_no_encoder_wrap():
    profile = Profile(profile_value()); values = [0, .1, -.2, .2, 0, .3]
    result = profile.targets(values)
    assert profile.angles(result) == pytest.approx(values, abs=.001)
    assert result[3] > 2048
    with pytest.raises(ValueError): profile.targets([4, 0, 0, 0, 0, 0])
    with pytest.raises(ValueError): profile.targets([True, 0, 0, 0, 0, 0])


def test_read_pose_never_writes_or_enables():
    motion, bus, _ = controller(False)
    motion.tick()
    assert not bus.writes and set(bus.torque.values()) == {0}
    with pytest.raises(ValueError): motion.activate()
    assert not bus.writes


def test_passive_telemetry_remains_fresh_above_motion_temperature_threshold():
    motion, bus, clock = controller()
    original = bus.feedback
    bus.feedback = lambda i: replace(original(i), temperature=68 if i == 2 else 30)
    clock.advance(.1)
    motion.tick()
    assert motion.state == 'CONNECTED' and motion.rows[2]['temperature'] == 68
    assert motion.snapshot()['sample_age_s'] == 0
    assert bus.writes == []
    with pytest.raises(BusError):
        motion.activate()
    assert bus.writes == []


def test_activate_holds_measured_pose_before_accepting_targets():
    motion, bus, _ = controller()
    motion.activate()
    assert motion.state == 'ACTIVE'
    assert all(position == 2048 and speed == 57 and acceleration == 1 for _, position, speed, acceleration in bus.writes)


def test_changed_hardware_offset_prevents_all_writes():
    motion, bus, _ = controller()
    motion.settings['shoulder_pan']['homing_offset_encoded'] = 4080
    with pytest.raises(BusError): motion.activate()
    assert not bus.writes


def test_fast_drag_is_rate_limited_and_release_cancels_pending_target():
    motion, bus, clock = controller(); motion.activate()
    old_epoch = motion.epoch
    motion.input([.5, 0, 0, 0, 0, 0], old_epoch, 1, True)
    clock.advance(.1); motion.tick()
    assert abs(bus.goals[1] - 2048) <= math.ceil(RATE * .1)
    motion.hold()
    assert bus.goals[1] == 2048  # measured pose, not far-away requested position
    count = len(bus.writes)
    clock.advance(.1); motion.tick()
    assert len(bus.writes) == count
    with pytest.raises(ValueError): motion.input([.5, 0, 0, 0, 0, 0], old_epoch, 2, True)


def test_no_input_watchdog_holds_and_requires_new_connection():
    motion, bus, clock = controller(); motion.activate()
    motion.input([.2, 0, 0, 0, 0, 0], motion.epoch, 1, True)
    clock.advance(.4); motion.tick()
    assert motion.state == 'FAULT_HOLD' and not motion.gesture
    assert all(value == 2048 for value in bus.goals.values())


def test_invalid_target_cancels_previous_drag_instead_of_continuing():
    motion, bus, clock = controller(); motion.activate()
    motion.input([.2, 0, 0, 0, 0, 0], motion.epoch, 1, True)
    with pytest.raises(ValueError): motion.input([float('nan')] * 6, motion.epoch, 2, True)
    assert motion.state == 'FAULT_HOLD' and not motion.gesture
    assert all(position == 2048 for position in bus.goals.values())


def test_lost_motor_link_is_not_reported_as_stopped():
    motion, bus, clock = controller(); motion.activate(); bus.failed = True
    motion.tick()
    assert motion.state == 'FAULT_UNCONFIRMED'
    assert 'doğrulayamadım' in motion.message
    motion.disconnect(); assert bus.closed


def test_motion_packet_guard_rejects_eeprom_broadcast_torque_off_and_zero_speed():
    class NoIO:
        def reset_input_buffer(self): raise AssertionError('serial I/O not expected')
    bus = MotionBus(NoIO())
    for servo, instruction, data in [(1, 3, b'\x1f\0\0'), (254, 2, b'\x28\1'), (1, 3, b'\x28\0'),
                                     (1, 6, b''), (1, 3, b'\x29\1\0\10\0\0\0\0')]:
        with pytest.raises(BusError): bus.transact(servo, instruction, data)
    with pytest.raises(BusError): bus.sync_positions({1: 2048})


def test_recording_is_explicitly_simulation_and_not_training_ready(tmp_path, monkeypatch):
    app = Application()
    monkeypatch.setattr('figbot_lab.virtual_server.new_run', lambda _: tmp_path)
    app.action('record/start', {})
    app.action('record/simulation', {'angles': [0] * 6, 'sequence': 1})
    app.action('record/stop', {})
    session = json.loads((tmp_path / 'session.json').read_text())
    assert session['source'] == 'SIMULATION_ONLY' and not session['training_ready'] and not session['camera_included']
    events = [json.loads(line) for line in (tmp_path / 'events.jsonl').read_text().splitlines()]
    assert any(e['kind'] == 'simulation_pose' for e in events)


def test_loopback_server_rejects_foreign_origin_missing_token_and_traversal(tmp_path):
    app = Application(); (tmp_path / 'index.html').write_text('virtual test')
    server = server_for(app, 0, tmp_path); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    url = f'http://127.0.0.1:{server.server_port}'
    try:
        assert server.server_address[0] == '127.0.0.1'
        assert json.load(urllib.request.urlopen(url + '/api/state'))['state'] == 'DISCONNECTED'
        for origin, token in [('https://foreign.example', app.token), (url, '')]:
            request = urllib.request.Request(url + '/api/activate', b'{}', headers={'Origin': origin, 'X-Figbot-Token': token, 'Content-Type': 'application/json'})
            with pytest.raises(urllib.error.HTTPError) as error: urllib.request.urlopen(request)
            assert error.value.code == 403
        with pytest.raises(urllib.error.HTTPError) as error: urllib.request.urlopen(url + '/%2e%2e/outside')
        assert error.value.code == 403
        request = urllib.request.Request(url + '/api/activate', b'{}', headers={'Origin': url, 'X-Figbot-Token': app.token, 'Content-Type': 'application/json'})
        with pytest.raises(urllib.error.HTTPError) as error: urllib.request.urlopen(request)
        assert error.value.code == 400 and not app.motion.may_be_live
    finally:
        server.shutdown(); thread.join(timeout=2); server.server_close(); app.close()
