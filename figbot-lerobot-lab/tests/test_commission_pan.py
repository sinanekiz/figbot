from datetime import datetime, timezone
import pytest

from figbot_lab import commission_pan as probe
from figbot_lab._reference_protocol import Bus, BusError, BusTimeout
from figbot_lab.common import sha256


@pytest.fixture
def rig(monkeypatch, tmp_path):
    monkeypatch.setattr(probe, 'ROOT', tmp_path)
    image = tmp_path / 'review.jpg'
    image.write_bytes(b'test capture')
    review = {'status': 'CLEARED_FOR_SINGLE_BASE_PROBE',
              'reviewed_utc': datetime.now(timezone.utc).isoformat(),
              'whole_arm_visible': True, 'base_clamped': True,
              'clearance_visible': True, 'hands_clear': True,
              'image': str(image), 'image_sha256': sha256(image),
              'positions': {str(i): 2100 for i in range(1, 7)}}
    registers = {i: bytearray(71) for i in range(1, 7)}
    for i, values in registers.items():
        values[3:5] = (777).to_bytes(2, 'little')
        values[5] = i
        values[13] = 70
        values[56:58] = (2100).to_bytes(2, 'little')
        values[62:64] = bytes([123, 30])
    writes, state = [], {'clock': 0., 'lost_ack': False, 'auto_torque': False}

    def transport(self, servo_id, instruction, data=b'', response_size=None):
        values = registers[servo_id]
        if instruction == 2:
            return bytes(values[data[0]:data[0] + data[1]])
        writes.append((servo_id, bytes(data)))
        values[data[0]:data[0] + len(data) - 1] = data[1:]
        if data[0] == 41:
            values[56:58] = data[2:4]
            if state['auto_torque']:
                values[40] = 1
            if state['lost_ack']:
                raise BusTimeout('Applied write with lost acknowledgement')
        return b''

    monkeypatch.setattr(Bus, 'transact', transport)
    bus = probe.PanProbeBus(None)
    def clock():
        return state['clock']
    def sleep(seconds):
        state['clock'] += seconds
    def frame():
        return {'pc_read_monotonic': clock(), 'pc_age_upper_s': .02}
    def run(**kwargs):
        return probe.run_pan_probe(bus, review, kwargs.pop('fresh_frame', frame),
                                   clock=clock, sleep=sleep, **kwargs)
    return bus, review, registers, writes, state, run


@pytest.mark.parametrize('auto_torque', [False, True])
def test_excursion_return_single_motor_and_no_persistent_writes(rig, auto_torque):
    bus, review, registers, writes, state, run = rig
    state['auto_torque'] = auto_torque
    original = {i: bytes(v[:40]) for i, v in registers.items()}
    result = run()
    assert result['home'] == 2100 and result['peak'] == 2094
    assert result['final'][1]['position'] == 2100
    assert result['physical_mapping'] == 'UNVERIFIED' and not result['profile_created']
    assert all(i == 1 and data[0] in (40, 41) for i, data in writes)
    goals = [int.from_bytes(data[2:4], 'little') for _, data in writes if data[0] == 41]
    assert goals == [2100, 2098, 2096, 2094, 2096, 2098, 2100]
    assert all(bytes(registers[i][:40]) == original[i] for i in registers)
    assert registers[1][40] == 1 and all(registers[i][40] == 0 for i in range(2, 7))


def test_uncleared_scene_and_changed_capture_never_write(rig):
    bus, review, registers, writes, state, run = rig
    review['hands_clear'] = False
    with pytest.raises(ValueError):
        run()
    review['hands_clear'] = True
    review['image_sha256'] = 'incorrect'
    with pytest.raises(ValueError):
        run()
    assert writes == []


def test_stale_review_and_foreign_image_rejected(rig):
    bus, review, registers, writes, state, run = rig
    review['reviewed_utc'] = '2020-01-01T00:00:00+00:00'
    with pytest.raises(ValueError):
        run()
    review['reviewed_utc'] = datetime.now(timezone.utc).isoformat()
    review['image'] = str(probe.ROOT.parent / 'outside.jpg')
    with pytest.raises(ValueError):
        run()
    assert writes == []


@pytest.mark.parametrize('fault', ['torque', 'mode', 'position', 'current'])
def test_preflight_fault_never_writes(rig, fault):
    bus, review, registers, writes, state, run = rig
    if fault == 'torque':
        registers[2][40] = 1
    elif fault == 'mode':
        registers[1][33] = 1
    elif fault == 'position':
        registers[1][56:58] = (2090).to_bytes(2, 'little')
    else:
        registers[1][69:71] = (151).to_bytes(2, 'little')
    with pytest.raises(BusError):
        run()
    assert writes == []


def test_stale_camera_before_goal_never_writes(rig):
    bus, review, registers, writes, state, run = rig
    with pytest.raises(BusError):
        run(fresh_frame=lambda: {'pc_read_monotonic': -10., 'pc_age_upper_s': .02})
    assert writes == []


def test_lost_ack_is_not_retried_and_leaves_uncertain_small_goal(rig):
    bus, review, registers, writes, state, run = rig
    state.update(lost_ack=True, auto_torque=True)
    with pytest.raises(BusTimeout):
        run()
    assert len(writes) == 1
    assert registers[1][40] == 1
    assert int.from_bytes(registers[1][42:44], 'little') == 2100


def test_camera_loss_after_activation_sends_no_further_goal(rig):
    bus, review, registers, writes, state, run = rig
    state['auto_torque'] = True
    calls = [0]
    def frame():
        calls[0] += 1
        return {'pc_read_monotonic': state['clock'],
                'pc_age_upper_s': .02 if calls[0] == 1 else 1.}
    with pytest.raises(BusError):
        run(fresh_frame=frame)
    assert len(writes) == 1 and registers[1][40] == 1


def test_packet_guard_rejects_other_motors_eeprom_large_steps_and_broadcast(rig):
    bus, review, registers, writes, state, run = rig
    with pytest.raises(BusError):
        bus.goal(1, 2100, 57, 1)
    bus.set_home(2100)
    for action in (lambda: bus.goal(2, 2100, 57, 1),
                   lambda: bus.goal(1, 2097, 57, 1),
                   lambda: bus.goal(1, 2101, 57, 1),
                   lambda: bus.write(1, 31, b'\0\0'),
                   lambda: bus.write(1, 40, b'\0'),
                   lambda: bus.write(1, 40, b'\1'),
                   lambda: bus.transact(254, 3, b'\x28\x01')):
        with pytest.raises(BusError):
            action()
    assert writes == []
