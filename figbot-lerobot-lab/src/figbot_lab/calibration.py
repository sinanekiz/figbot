"""Passive measurements. Never enables torque or changes motor registers."""
from __future__ import annotations

from dataclasses import asdict
import time

from ._reference_protocol import Bus, BusError, word
from .common import JOINTS, new_run, save_json


class ReadOnlyBus(Bus):
    def sync_goal(self, profiles):
        raise BusError('Calibration rejects SDK motor writes')

    def sync_positions(self, positions):
        raise BusError('Calibration rejects SDK motor writes')

    def transact(self, servo_id, instruction, data=b'', response_size=None):
        if instruction != 2 or servo_id not in range(1, 7):
            raise BusError('Calibration permits only READ packets to motor IDs 1..6')
        return super().transact(servo_id, instruction, data, response_size)


def read_settings(bus, motor_ids=None):
    ids = tuple(range(1, 7)) if motor_ids is None else tuple(motor_ids)
    if ids not in (tuple(range(1, 7)), tuple(range(1, 6))):
        raise ValueError('Explicit five- or six-motor configuration required')
    result = {}
    for motor, name in enumerate(JOINTS, 1):
        if motor not in ids:
            continue
        data = bus.read(motor, 0, 40)
        if data[5] != motor:
            raise ValueError('Motor ID readback mismatch')
        result[name] = {'id': motor, 'registers_0_39_hex': data.hex(),
                        'homing_offset_encoded': word(data[31:33]),
                        'register_min': word(data[9:11]),
                        'register_max': word(data[11:13]),
                        'operating_mode': data[33]}
    return result


def read_sample(bus):
    began = time.monotonic()
    motors = {}
    for motor, name in enumerate(JOINTS, 1):
        feedback, torque = bus.feedback_state(motor)
        if torque != 0:
            raise ValueError(f'{name}: torque is enabled; passive calibration stopped')
        if not 0 <= feedback.position <= 4095:
            raise ValueError(f'{name}: encoder outside single-turn range')
        if not 10 <= feedback.voltage <= 12.6 or feedback.temperature >= 55:
            raise ValueError(f'{name}: voltage/temperature outside existing bench envelope')
        motors[name] = {**asdict(feedback), 'torque_enabled': torque}
    duration = time.monotonic() - began
    if duration > .25:
        raise ValueError('Motor sample took over 250 ms; incomplete/stale measurement')
    return {'monotonic': began, 'duration_s': duration,
            'midpoint_monotonic': began + duration / 2, 'motors': motors}


def associate_camera(frames, samples):
    """Bound clock uncertainty; single-turn samples are read sequentially."""
    associations = []
    for frame in frames:
        low, high = frame['pc_capture_interval']
        errors = [max(abs(row['midpoint_monotonic'] - low),
                      abs(row['midpoint_monotonic'] - high)) + row['duration_s'] / 2
                  for row in samples]
        best = min(range(len(errors)), key=errors.__getitem__)
        if errors[best] > .2:
            raise ValueError('Camera/encoder uncertainty exceeds 200 ms')
        associations.append({'capture_ns': frame['capture_ns'], 'sample_index': best,
                             'max_separation_s': errors[best]})
    return associations


def summarize(samples, kind):
    if len(samples) < 5:
        raise ValueError('At least five samples required')
    result = {}
    for name in JOINTS:
        values = [row['motors'][name]['position'] for row in samples]
        # A wrap is not evidence for the whole mechanical range.
        if any(abs(b - a) > 2048 for a, b in zip(values, values[1:])):
            raise ValueError(f'{name}: encoder wrap detected; coordinate review required')
        span = max(values) - min(values)
        if kind != 'range' and (span > 8 or any(
            abs(row['motors'][name]['speed']) > 5 or row['motors'][name]['moving']
            for row in samples
        )):
            raise ValueError(f'{name}: pose moved during measurement; hold it steady and retry')
        result[name] = {'observed_min': min(values), 'observed_max': max(values),
                        'median': sorted(values)[len(values) // 2]}
    return result


def capture(kind='baseline', seconds=2, port='COM5', camera=False):
    import serial
    if kind not in ('baseline', 'neutral', 'range', 'drop'):
        raise ValueError('Unknown calibration stage')
    if not .5 <= seconds <= 120:
        raise ValueError('Duration must be 0.5..120 seconds')
    if camera and kind == 'range':
        raise ValueError('Range sweeps and stationary camera-pose capture are separate measurements')
    run = new_run('calibration_' + kind)
    report = {'kind': kind, 'status': 'INCOMPLETE', 'port': port,
              'joint_order': list(JOINTS), 'motor_commands_sent': False,
              'samples': [], 'note': 'Observed values are not certified mechanical limits or a motion route.'}
    try:
        with serial.Serial(port, 1000000, timeout=.02, write_timeout=.3) as connection:
            bus = ReadOnlyBus(connection)
            report['settings_before'] = read_settings(bus)
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                report['samples'].append(read_sample(bus))
                time.sleep(.05)
            report['summary'] = summarize(report['samples'], kind)
            if camera:
                from .phone import capture_phone
                camera_frames = []
                def observe(meta):
                    report['samples'].append(read_sample(bus))
                    camera_frames.append(meta)
                report['camera_run'] = str(capture_phone(seconds=1, on_frame=observe))
                report['samples'].append(read_sample(bus))
                report['camera_associations'] = associate_camera(camera_frames, report['samples'])
                report['summary'] = summarize(report['samples'], kind)
            report['settings_after'] = read_settings(bus)
            if report['settings_before'] != report['settings_after']:
                raise ValueError('Motor settings changed during capture')
        report['status'] = 'MEASURED_REQUIRES_PHYSICAL_REVIEW'
    except BaseException as exc:
        report['status'] = 'FAILED'
        report['error'] = str(exc)
        save_json(run / 'measurement.json', report)
        if not isinstance(exc, Exception):
            raise
        raise ValueError(f'{exc}; evidence: {run}') from exc
    save_json(run / 'measurement.json', report)
    return run
