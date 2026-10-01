"""Supervised, small relative tests of all six motors, not angle calibration."""
import time
from dataclasses import asdict
from ._reference_protocol import BusError, word
from .calibration import read_settings
from .common import JOINTS
from .virtual_motion import MotionBus, MotionController
from .commission_pan import validate_review

EXCURSION = 48  # ~4.22 encoder degrees, not a measured mechanical limit
STEP = 8
TEST_SIGNS = (-1, 1, -1, 1, 1, 1)  # test paths, NOT model/encoder direction mappings


class CommissionController(MotionController):
    """User-authorized probe uses the preserved hardware thermal limit only.

    Full teleoperation's lower prototype threshold remains unchanged.
    """
    def __init__(self, bus, settings, **kwargs):
        super().__init__(bus, **kwargs)
        self.temperature_limits = {i: bytes.fromhex(settings[name]['registers_0_39_hex'])[13]
                                   for i, name in enumerate(JOINTS, 1) if i in self.active_ids}
        if any(not 40 <= value <= 85 for value in self.temperature_limits.values()):
            raise BusError('Unknown hardware thermal limit; no probe write permitted.')

    def read_all(self, checked=True):
        began, rows = self.clock(), {}
        for i in self.active_ids:
            feedback, torque = self.bus.feedback_state(i)
            row = {**asdict(feedback), 'torque': torque}
            if (not 0 <= row['position'] <= 4095 or torque not in (0, 1) or
                    checked and (not 10 <= row['voltage'] <= 12.6 or
                    row['temperature'] >= self.temperature_limits[i] or
                    abs(row['current_raw']) > 150)):
                raise BusError(f'ID{i}: commissioning feedback rejected: {row}')
            rows[i] = row
        if self.clock() - began > .25:
            raise BusError('Probe telemetry exceeded 250 ms.')
        self.rows, self.updated = rows, self.clock()
        self.event('feedback', read_interval=[began, self.updated], motors=rows)
        return rows


class BatchProbeBus(MotionBus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected = self.home = self.previous = None
        self.preloaded = False
        self.completed = set()
        self.prepared = set()
        self.phase = 'hold'

    def select(self, motor, home):
        sequence = self.prepared if self.phase == 'hold' else self.completed
        if (type(motor) is not int or motor != len(sequence) + 1 or
                motor not in range(1, 7) or type(home) is not int or
                not 16 <= home <= 4079):
            raise BusError('A fresh home and sequential, unrepeated motor test are required.')
        self.selected, self.home, self.previous, self.preloaded = motor, home, home, False

    def hold_done(self):
        if self.phase != 'hold' or self.previous != self.home or not self.preloaded:
            raise BusError('Verified current-position hold required.')
        self.prepared.add(self.selected)
        self.selected = None

    def begin_probes(self):
        if self.phase != 'hold' or self.prepared != set(range(1, 7)):
            raise BusError('All six current-position holds must precede movement.')
        self.phase = 'probe'

    def complete(self):
        if self.previous != self.home:
            raise BusError('Return to the original target before the next motor.')
        self.completed.add(self.selected)
        self.selected = None

    def transact(self, servo_id, instruction, data=b'', response_size=None):
        if instruction != 2:
            if instruction != 3 or servo_id != self.selected:
                raise BusError('Only the current single motor can receive a probe write.')
            if data == b'\x28\x01':
                if not self.preloaded:
                    raise BusError('Verify the current-position target before torque-on.')
            elif len(data) == 8 and data[0] == 41:
                target = word(data[2:4])
                relative = TEST_SIGNS[servo_id - 1] * (target - self.home)
                if (self.phase == 'hold' and target != self.home or
                        not 0 <= relative <= EXCURSION or abs(target - self.previous) > STEP):
                    raise BusError('Fixed forty-eight-count excursion / eight-count step exceeded.')
                self.previous = target  # uncertain writes are never retried
            else:
                raise BusError('Persistent settings, torque-off and other writes are rejected.')
        return super().transact(servo_id, instruction, data, response_size)


def run_batch_probe(bus, review, fresh_frame, *, event=None,
                    clock=time.monotonic, sleep=time.sleep):
    validate_review(review, expected_status='CLEARED_FOR_SIX_JOINT_PROBE')
    event = event or (lambda value: None)
    settings = read_settings(bus)
    controller = CommissionController(bus, settings, clock=clock)
    for name in JOINTS:
        if settings[name]['operating_mode'] != 0 or word(bytes.fromhex(
                settings[name]['registers_0_39_hex'])[3:5]) != 777:
            raise BusError('Expected STS position-mode hardware is required.')
    initial = controller.read_all()
    sleep(.1)
    stationary = controller.read_all()
    expected_torque = review.get('torques', {str(i): (initial[1]['torque'] if i == 1 else 0)
                                           for i in range(1, 7)})
    for i, row in stationary.items():
        if (row['moving'] or initial[i]['moving'] or abs(row['speed']) > 5 or
                abs(initial[i]['speed']) > 5 or row['torque'] != initial[i]['torque'] or
                row['torque'] != expected_torque[str(i)] or
                abs(row['position'] - initial[i]['position']) > 2 or
                abs(row['position'] - review['positions'][str(i)]) > 2):
            raise BusError('Reviewed stationary pose required; only base may already be powered.')
        if row['torque'] and abs(word(bus.read(i, 42, 2)) - row['position']) > 16:
            raise BusError('Existing powered target differs from measured position.')
    homes = {i: row['position'] for i, row in stationary.items()}
    powered = {i: row['torque'] for i, row in stationary.items()}
    deadline = clock() + 45
    results = []

    def camera():
        meta = fresh_frame()
        if (clock() > deadline or not 0 <= clock() - meta['pc_read_monotonic'] <= .25 or
                not 0 <= meta['pc_age_upper_s'] <= .3):
            raise BusError('Camera freshness or batch deadline failed.')
        return meta

    def observe(selected=None):
        began = clock()
        while True:
            meta = camera()
            rows = controller.read_all()
            # Retain the offending measurement as well as passing measurements.
            event({'kind': 'feedback', 'motors': rows, 'frame_metadata': meta})
            pending = []
            for i, row in rows.items():
                if row['torque'] != powered[i]:
                    raise BusError(f'ID{i}: unexpected torque state.')
                expected = bus.previous if i == selected else homes[i]
                if abs(row['position'] - expected) > (32 if i == selected else 16):
                    raise BusError(f'ID{i}: tracking or another-joint drift failed.')
                if i != selected:
                    if row['moving'] or abs(row['speed']) > 5:
                        pending.append(i)
            if not pending:
                return rows
            # Hold the last bounded target. Issue NO new goal during this pause.
            if clock() - began >= .25:
                raise BusError(f'ID{pending}: another-joint movement flag persisted.')
            event({'kind': 'pause_for_movement_flag', 'motors': pending})
            sleep(.04)

    def goal(motor, target):
        event({'kind': 'goal_attempt', 'motor': motor, 'position': target})
        controller.write_goal(motor, target)
        event({'kind': 'goal_readback', 'motor': motor, 'position': target})

    for motor in range(1, 7):
        observe()
        bus.select(motor, homes[motor])
        goal(motor, homes[motor])
        bus.preloaded = True
        camera()
        if bus.read(motor, 40, 1) != b'\1':
            event({'kind': 'torque_on_attempt', 'motor': motor})
            bus.write(motor, 40, b'\1')
        powered[motor] = 1
        observe(motor)
        bus.hold_done()
        event({'kind': 'current_pose_hold_completed', 'motor': motor, 'position': homes[motor]})
    bus.begin_probes()
    observe()
    for motor in range(1, 7):
        observe()
        bus.select(motor, homes[motor])
        bus.preloaded = True
        peak = None
        for distance in (*range(STEP, EXCURSION + 1, STEP), *range(EXCURSION - STEP, -1, -STEP)):
            rows = observe(motor)
            target = homes[motor] + TEST_SIGNS[motor - 1] * distance
            wait_until = clock() + 1
            while abs(target - rows[motor]['position']) > 32:
                if clock() >= wait_until:
                    raise BusError(f'ID{motor}: next goal would lead measured position too far.')
                sleep(.04)
                rows = observe(motor)
            goal(motor, target)
            until = clock() + (1. if distance in (EXCURSION, 0) else .25)
            while clock() < until:
                rows = observe(motor)
                sleep(.04)
            if distance == EXCURSION:
                peak = rows[motor]['position']
                if abs(peak - bus.previous) > 16:
                    raise BusError(f'ID{motor}: excursion was not observed.')
        final = observe(motor)[motor]
        if abs(final['position'] - homes[motor]) > 16 or final['moving'] or abs(final['speed']) > 5:
            raise BusError(f'ID{motor}: return was not observed.')
        bus.complete()
        result = {'motor': motor, 'home': homes[motor], 'peak': peak, 'final': final}
        results.append(result)
        event({'kind': 'joint_completed', **result})
    final = observe()
    if read_settings(bus) != settings:
        raise BusError('Persistent motor settings changed.')
    return {'status': 'SIX_SMALL_MOTOR_PROBES_MEASURED', 'joints': results, 'final': final,
            'torque_left_on': list(range(1, 7)), 'physical_mapping': 'UNVERIFIED',
            'mechanical_limits': 'UNVERIFIED', 'profile_created': False}
