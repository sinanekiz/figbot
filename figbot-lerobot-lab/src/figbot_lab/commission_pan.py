"""One supervised relative base probe, independent of model-angle calibration.

No serial port is opened on import. This does not establish mechanical limits,
absolute angles, collision clearance or a VERIFIED teleoperation profile.
"""
from datetime import datetime, timezone
import time

from ._reference_protocol import BusError, word
from .calibration import read_settings
from .common import JOINTS, ROOT, sha256
from .virtual_motion import MotionBus, MotionController, SPEED, ACCELERATION


class PanProbeBus(MotionBus):
    """Packet guard: only motor 1, a six-count excursion, two-count steps."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.home = self.previous = None
        self.preloaded = False

    def set_home(self, position):
        if self.home is not None or type(position) is not int or not 16 <= position <= 4079:
            raise BusError('Probe home must be a fresh single-turn position.')
        self.home = self.previous = position

    def transact(self, servo_id, instruction, data=b'', response_size=None):
        if instruction != 2:
            if instruction != 3 or servo_id != 1 or self.home is None:
                raise BusError('Probe permits motor 1 SRAM writes only after preflight.')
            if data == b'\x28\x01':
                if not self.preloaded:
                    raise BusError('Read back the current-position goal before torque-on.')
            elif len(data) == 8 and data[0] == 41:
                target = word(data[2:4])
                if not self.home - 6 <= target <= self.home or abs(target - self.previous) > 2:
                    raise BusError('Probe target exceeds the fixed excursion/step budget.')
                # A timeout may still have applied a write. Never retry automatically.
                self.previous = target
            else:
                raise BusError('Probe rejects calibration, torque-off and other writes.')
        return super().transact(servo_id, instruction, data, response_size)


def validate_review(review, now=None, expected_status='CLEARED_FOR_SINGLE_BASE_PROBE'):
    from pathlib import Path
    now = now or datetime.now(timezone.utc)
    recorded = datetime.fromisoformat(review['reviewed_utc'])
    if recorded.tzinfo is None or not 0 <= (now - recorded).total_seconds() <= 30:
        raise ValueError('A scene review within 30 seconds is required.')
    if review.get('status') != expected_status:
        raise ValueError('Scene has not been reviewed for the base probe.')
    for field in ('whole_arm_visible', 'base_clamped', 'clearance_visible', 'hands_clear'):
        if review.get(field) is not True:
            raise ValueError(f'Scene prerequisite missing: {field}')
    image = Path(review['image']).resolve()
    if not image.is_relative_to(ROOT.resolve()) or sha256(image) != review['image_sha256']:
        raise ValueError('Reviewed image must be an unchanged lab capture.')
    positions = review['positions']
    if set(positions) != {str(i) for i in range(1, 7)} or any(
            type(p) is not int or not 0 <= p <= 4095 for p in positions.values()):
        raise ValueError('Six measured review positions are required.')


def run_pan_probe(bus, review, fresh_frame, *, event=None,
                  clock=time.monotonic, sleep=time.sleep):
    """Caller owns serial exclusively; fresh_frame captures/saves live images.

    Leaves only the base motor holding its final bounded target. On an error,
    its last small goal may remain powered; no fall-inducing torque-off is sent.
    Camera freshness is a transport check, not automatic collision detection.
    """
    event = event or (lambda value: None)
    validate_review(review)
    controller = MotionController(bus, clock=clock)
    settings = read_settings(bus)
    for name in JOINTS:
        s = settings[name]
        if s['operating_mode'] != 0 or word(bytes.fromhex(s['registers_0_39_hex'])[3:5]) != 777:
            raise BusError('Probe requires the observed STS position-mode hardware.')
    first = controller.read_all()
    sleep(.1)
    second = controller.read_all()
    for i in first:
        if (first[i]['torque'] != 0 or second[i]['torque'] != 0 or
                first[i]['moving'] or second[i]['moving'] or
                abs(first[i]['speed']) > 5 or abs(second[i]['speed']) > 5 or
                abs(second[i]['position'] - first[i]['position']) > 2 or
                abs(second[i]['position'] - review['positions'][str(i)]) > 2):
            raise BusError('Probe requires the reviewed, unpowered stationary pose.')
    home = second[1]['position']
    bus.set_home(home)
    deadline = clock() + 10

    def camera():
        meta = fresh_frame()
        if (clock() > deadline or not 0 <= clock() - meta['pc_read_monotonic'] <= .25 or
                not 0 <= meta['pc_age_upper_s'] <= .3):
            raise BusError('Probe deadline/camera freshness check failed.')
        return meta

    def observe(powered):
        meta = camera()
        rows = controller.read_all()
        for i, row in rows.items():
            if i == 1:
                if row['torque'] != int(powered) or not home - 8 <= row['position'] <= home + 2:
                    raise BusError('Base torque/position drift failed.')
                if abs(row['position'] - bus.previous) > 4:
                    raise BusError('Base did not track the small probe goal.')
            elif (row['torque'] != 0 or row['moving'] or abs(row['speed']) > 5 or
                  abs(row['position'] - second[i]['position']) > 2):
                raise BusError('Another joint moved during the base probe.')
        event({'kind': 'feedback', 'motors': rows, 'frame_metadata': meta})
        return rows

    def goal(target):
        # Mark attempted writes before transport; lost acknowledgments are uncertain.
        event({'kind': 'goal_attempt', 'motor': 1, 'position': target})
        controller.write_goal(1, target)
        event({'kind': 'goal_readback', 'motor': 1, 'position': target})

    observe(False)
    goal(home)
    bus.preloaded = True
    # Some firmware may enable torque on a goal write. Read before explicit enable.
    if bus.read(1, 40, 1) != b'\1':
        camera()
        event({'kind': 'torque_on_attempt', 'motor': 1})
        bus.write(1, 40, b'\1')
    observe(True)
    peak = None
    for relative in (-2, -4, -6, -4, -2, 0):
        observe(True)
        goal(home + relative)
        settle_until = clock() + .5
        while clock() < settle_until:
            rows = observe(True)
            sleep(.08)
        if relative == -6:
            peak = rows[1]['position']
            if abs(peak - (home - 6)) > 2:
                raise BusError('Base excursion was not observed; no success claim.')
    final = observe(True)
    if abs(final[1]['position'] - home) > 2 or read_settings(bus) != settings:
        raise BusError('Return position or unchanged persistent settings check failed.')
    result = {'status': 'SMALL_BASE_PROBE_MEASURED', 'home': home, 'peak': peak,
              'final': final, 'base_torque_left_on': True, 'physical_mapping': 'UNVERIFIED',
              'mechanical_limits': 'UNVERIFIED', 'profile_created': False}
    event({'kind': 'completed', **result})
    return result
