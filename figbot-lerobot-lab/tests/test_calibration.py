from dataclasses import replace

import pytest

from figbot_lab._reference_protocol import BusError, Feedback, MotorStatusError
from figbot_lab.calibration import ReadOnlyBus, read_sample, summarize
from figbot_lab.common import JOINTS


class Port:
    def __init__(self):
        self.writes = []
        self.response = b''

    def reset_input_buffer(self):
        pass

    def write(self, command):
        self.writes.append(command)
        body = bytes([command[2], 3, 0, 7])
        self.response = command + b'\xff\xff' + body + bytes([~sum(body) & 255])
        return len(command)

    @property
    def in_waiting(self):
        return len(self.response)

    def read(self, size):
        data, self.response = self.response[:size], self.response[size:]
        return data


@pytest.mark.parametrize('instruction', [1, 3, 4, 5, 6, 131])
def test_nonread_never_reaches_port(instruction):
    port = Port()
    with pytest.raises(BusError):
        ReadOnlyBus(port).transact(1, instruction, b'\x28\x01')
    assert not port.writes


def test_inherited_motion_helpers_cannot_write():
    port = Port()
    with pytest.raises(BusError):
        ReadOnlyBus(port).goal(1, 2000, 100)
    assert not port.writes


@pytest.mark.parametrize('method', ['sync_goal', 'sync_positions'])
def test_sdk_writes_are_blocked_before_sdk_import(method):
    port = Port()
    with pytest.raises(BusError):
        getattr(ReadOnlyBus(port), method)({1: 2000})
    assert not port.writes


def test_read_ignores_echo_and_verifies_response():
    port = Port()
    assert ReadOnlyBus(port).read(1, 40, 1) == b'\x07'
    assert port.writes[0][4] == 2


@pytest.mark.parametrize('flags', [0x04, 0x20, 0x40])
def test_valid_motor_protection_response_preserves_id_and_flags(flags):
    class ProtectedPort(Port):
        def write(self, command):
            self.writes.append(command)
            body = bytes([command[2], 3, flags, 0])
            self.response = command + b'\xff\xff' + body + bytes([~sum(body) & 255])
            return len(command)
    port = ProtectedPort()
    with pytest.raises(MotorStatusError) as error:
        ReadOnlyBus(port).read(4, 40, 1)
    assert error.value.servo_id == 4 and error.value.status_flags == flags
    assert len(port.writes) == 1 and port.writes[0][4] == 2


def test_read_broadcast_rejected():
    port = Port()
    with pytest.raises(BusError):
        ReadOnlyBus(port).read(254, 40, 1)
    assert not port.writes


class BusFixture:
    feedback = Feedback(2000, 0, 12.2, 30, 0, False)
    torque = 0

    def feedback_state(self, motor):
        return self.feedback, self.torque


def test_pose_stability_and_wrap_are_separate_checks():
    bus = BusFixture()
    samples = [read_sample(bus) for _ in range(5)]
    assert summarize(samples, 'neutral')['gripper']['median'] == 2000
    samples[-1]['motors'][JOINTS[0]]['position'] = 2100
    with pytest.raises(ValueError, match='pose moved'):
        summarize(samples, 'drop')
    assert summarize(samples, 'range')[JOINTS[0]]['observed_max'] == 2100
    samples[-1]['motors'][JOINTS[0]]['position'] = 4095
    with pytest.raises(ValueError, match='wrap'):
        summarize(samples, 'range')


@pytest.mark.parametrize('field,value', [('voltage', 9), ('temperature', 55), ('position', -1)])
def test_invalid_feedback_rejected(field, value):
    bus = BusFixture()
    bus.feedback = replace(bus.feedback, **{field: value})
    with pytest.raises(ValueError):
        read_sample(bus)


def test_torque_enabled_rejects_passive_calibration():
    bus = BusFixture()
    bus.torque = 1
    with pytest.raises(ValueError, match='torque'):
        read_sample(bus)


@pytest.mark.parametrize('failure', [None, 'torque', 'settings'])
def test_capture_preserves_evidence_and_detects_setting_changes(monkeypatch, tmp_path, failure):
    import json
    import serial
    from figbot_lab import calibration

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class Device(BusFixture):
        def __init__(self, connection):
            self.reads = 0
            self.torque = int(failure == 'torque')

        def read(self, motor, address, length):
            self.reads += 1
            data = bytearray(40)
            data[5] = motor
            if failure == 'settings' and self.reads > 6:
                data[31] = 1
            return bytes(data)

    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: Connection())
    monkeypatch.setattr(calibration, 'ReadOnlyBus', Device)
    monkeypatch.setattr(calibration, 'new_run', lambda kind: tmp_path)
    if failure:
        with pytest.raises(ValueError):
            calibration.capture(seconds=.5)
    else:
        assert calibration.capture(seconds=.5) == tmp_path
    report = json.loads((tmp_path / 'measurement.json').read_text(encoding='utf-8'))
    assert report['status'] == ('FAILED' if failure else 'MEASURED_REQUIRES_PHYSICAL_REVIEW')
    assert report['motor_commands_sent'] is False


def test_camera_encoder_association_accounts_for_uncertainty():
    from figbot_lab.calibration import associate_camera
    frames = [{'capture_ns': 1, 'pc_capture_interval': [1., 1.1]}]
    samples = [{'midpoint_monotonic': 1.12, 'duration_s': .02}]
    assert associate_camera(frames, samples)[0]['max_separation_s'] == pytest.approx(.13)
    samples[0]['midpoint_monotonic'] = 1.3
    with pytest.raises(ValueError, match='200 ms'):
        associate_camera(frames, samples)


def test_motion_during_photo_is_rejected_even_if_arm_returns_to_start(monkeypatch, tmp_path):
    import time
    import serial
    import figbot_lab.calibration as calibration
    import figbot_lab.phone as phone
    from figbot_lab.common import load_json
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Device(BusFixture):
        def __init__(self, connection): pass
        def read(self, motor, address, length):
            data = bytearray(40)
            data[5] = motor
            return bytes(data)
    moved = {'value': False}
    original_read = calibration.read_sample
    def sample(bus):
        row = original_read(bus)
        if moved['value']:
            row['motors'][JOINTS[0]]['position'] = 2100
        return row
    def camera(seconds, on_frame):
        moved['value'] = True
        on_frame({'capture_ns': 1, 'pc_capture_interval': [time.monotonic()-.01, time.monotonic()]})
        moved['value'] = False
        return tmp_path / 'camera'
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: Connection())
    monkeypatch.setattr(calibration, 'ReadOnlyBus', Device)
    monkeypatch.setattr(calibration, 'read_sample', sample)
    monkeypatch.setattr(calibration, 'new_run', lambda _: tmp_path)
    monkeypatch.setattr(phone, 'capture_phone', camera)
    with pytest.raises(ValueError, match='pose moved'):
        calibration.capture(seconds=.5, camera=True)
    assert load_json(tmp_path / 'measurement.json')['status'] == 'FAILED'
