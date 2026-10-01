"""Temporary relative mouse control; never a verified calibration profile."""
import math
from .common import JOINTS
from .virtual_motion import COUNTS_PER_RADIAN, MotionBus
from .commission_batch import CommissionController
from ._reference_protocol import BusError, BusTimeout, MotorStatusError

FULL_SPEED, FULL_ACCELERATION = 3400, 50  # all six physically read back speed3400 and acceleration50


class RelativeMotionBus(MotionBus):
    """Explicit user-requested profile; passive/verified/probe guards unchanged."""
    motion_speed, motion_acceleration = FULL_SPEED, FULL_ACCELERATION


def validate_angles(angles):
    if (not isinstance(angles, list) or len(angles) != 6 or
            any(type(v) not in (int, float) or not math.isfinite(v) for v in angles)):
        raise ValueError('Altı sonlu eklem açısı gerekli.')


def validate_home_reference(value, settings):
    """A saved physical fold and its visual pose, separate from mouse calibration.

    The saved encoder readings are usable only with the offsets they were read
    with. This checks that fact without changing any persistent motor setting.
    """
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError('Kapalı başlangıç pozu kaydı geçersiz.')
    angles = value.get('closed_angles')
    validate_angles(angles)
    result = {'closed_angles': list(angles)}
    for field, maximum in (('positions', 4095), ('homing_offsets', 65535)):
        values = value.get(field)
        if (not isinstance(values, dict) or len(values) != 6 or
                any(type(key) not in (int, str) for key in values) or
                set(map(str, values)) != set(map(str, range(1, 7)))):
            raise ValueError(f'Kapalı başlangıç pozu: altı {field} değeri gerekli.')
        result[field] = {}
        for i in range(1, 7):
            item = values.get(i, values.get(str(i)))
            if type(item) is not int or not 0 <= item <= maximum:
                raise ValueError(f'Kapalı başlangıç pozu: ID{i} {field} geçersiz.')
            result[field][i] = item
    for i, name in enumerate(JOINTS, 1):
        if result['homing_offsets'][i] != settings[name]['homing_offset_encoded']:
            raise ValueError(f'Kapalı başlangıç pozu: ID{i} motor ofseti kayıtla uyuşmuyor.')
        low, high = settings[name]['register_min'], settings[name]['register_max']
        if low == high == 0:
            low, high = 0, 4095
        if not low <= result['positions'][i] <= high:
            raise ValueError(f'Kapalı başlangıç pozu: ID{i} kayıtlı motor aralığı dışında.')
    return result


class RelativeProfile:
    verified = False
    control_mode = 'RELATIVE_TRIAL'

    def __init__(self, positions, angles, settings):
        validate_angles(angles)
        self.origin_angles = list(angles)
        self.origin_raw = dict(positions)
        self.active_ids = tuple(sorted(positions))
        if self.active_ids not in (tuple(range(1, 7)), tuple(range(1, 6))):
            raise ValueError('Göreli profil için açık beş veya altı motor düzeni gerekli.')
        self.entries = {}
        for i, name in enumerate(JOINTS, 1):
            if i not in self.active_ids:
                continue
            p = positions[i]
            if type(p) is not int or not 0 <= p <= 4095:
                raise ValueError('Geçersiz başlangıç enkoderi.')
            low, high = settings[name]['register_min'], settings[name]['register_max']
            if low == high == 0:  # hardware angle limit disabled; retain single-turn encoder range
                low, high = 0, 4095
            if type(low) is not int or type(high) is not int or not 0 <= low < high <= 4095:
                raise ValueError('Motorun kayıtlı konum aralığı geçersiz.')
            self.entries[name] = {'id': i, 'direction': 1,
                'raw_min': low, 'raw_max': high,
                'offset_encoded': settings[name]['homing_offset_encoded']}

    def angles(self, positions):
        angles = list(self.origin_angles)
        for i in self.active_ids:
            angles[i-1] += (positions[i] - self.origin_raw[i]) / COUNTS_PER_RADIAN
        return angles

    def targets(self, angles):
        validate_angles(angles)
        result = {}
        for i, name in enumerate(JOINTS, 1):
            if i not in self.active_ids:
                continue
            entry = self.entries[name]
            raw = self.origin_raw[i] + COUNTS_PER_RADIAN * (angles[i-1] - self.origin_angles[i-1])
            result[i] = round(max(entry['raw_min'], min(entry['raw_max'], raw)))
        return result

    def bounds(self):
        low = {i: self.entries[n]['raw_min'] for i, n in enumerate(JOINTS, 1) if i in self.active_ids}
        high = {i: self.entries[n]['raw_max'] for i, n in enumerate(JOINTS, 1) if i in self.active_ids}
        return list(map(list, zip(self.angles(low), self.angles(high))))


class RelativeController(CommissionController):
    def __init__(self, bus, settings, positions, angles, *, home_reference=None, **kwargs):
        active_ids = tuple(sorted(positions))
        if len(active_ids) != 6 and home_reference is not None:
            raise ValueError('Motor değişiminden önceki kapalı poz beş motorla kullanılamaz.')
        self.home_reference = validate_home_reference(home_reference, settings)
        super().__init__(bus, settings, profile=RelativeProfile(positions, angles, settings), active_ids=active_ids, **kwargs)
        self.settings = settings
        self.speed, self.acceleration = FULL_SPEED, FULL_ACCELERATION
        self.direct_targets = True
        self.watchdog, self.soft_watchdog = 1.0, True
        self.recover_read_timeouts = True
        self.manual_temperature_monitor = True
        self.hold_settle_seconds = .6
        self.homing = False
        self.home_deadline = None
        self.home_completed_epoch = None
        self.voltage_limits = {}
        for i, name in enumerate(JOINTS, 1):
            if i not in self.active_ids:
                continue
            registers = bytes.fromhex(settings[name]['registers_0_39_hex'])
            low, high = registers[15] / 10, registers[14] / 10
            if not 0 < low < high <= 25.4:
                raise BusError('Motorun kayıtlı gerilim koruması okunamadı.')
            self.voltage_limits[i] = low, high

    def read_all(self, checked=True):
        rows = super().read_all(checked=False)
        if checked:
            self.check_manual_temperature(rows)
            for i, row in rows.items():
                low, high = self.voltage_limits[i]
                if not low <= row['voltage'] <= high or row['temperature'] >= self.temperature_limits[i]:
                    raise BusError(f'ID{i}: hardware-configured voltage/temperature threshold: {row}')
        # Prototype current150 and voltage10..12.6 cutoffs belong to commissioning.
        # Motor status error bits still propagate through the protocol adapter.
        return rows

    def home(self):
        if self.state != 'ACTIVE':
            raise ValueError('Başlangıca dönmek için kontrolü açın.')
        if getattr(self, 'connection_recovering', False):
            raise ValueError('Motor yanıtı bekleniyor; başlangıca dönüş henüz başlatılamaz.')
        if self.home_reference is None:
            raise ValueError('Kapalı başlangıç pozu kaydı bulunamadı.')
        from .calibration import read_settings
        # Offsets may have changed since the session was opened. Reject the
        # saved counts before sending even a current-position hold command.
        try:
            validate_home_reference(self.home_reference, read_settings(self.bus))
        except MotorStatusError as exc:
            self.fault(exc)
            raise
        except (BusTimeout, OSError) as exc:
            self._begin_link_recovery(exc, 'home_reference_read')
            return
        self.hold()
        if (getattr(self, 'connection_recovering', False) or self.state != 'ACTIVE' or
                getattr(self, 'emergency_latched', False)):
            return
        self.desired = dict(self.home_reference['positions'])
        self.homing, self.gesture = True, True
        self.home_deadline = self.clock() + 15
        self.last_input = self.last_tick = self.clock()
        self.message = 'Başlangıca dönüyor…'
        self.event('home_requested', positions=self.desired,
                   closed_angles=self.home_reference['closed_angles'], calibration='UNVERIFIED')

    def input(self, *args, **kwargs):
        if self.homing:
            raise ValueError('Başlangıca dönüş sürüyor.')
        return super().input(*args, **kwargs)

    def hold(self):
        self.homing = False
        return super().hold()

    def cancel_pending_motion(self):
        self.homing = False
        return super().cancel_pending_motion()

    def tick(self):
        if self.homing:
            if self.clock() >= self.home_deadline:
                try:
                    self.hold()
                    if (self.state == 'ACTIVE' and not self.emergency_latched and
                            not self.connection_recovering and self.hold_confirmed):
                        self.message = 'Başlangıca dönüş tamamlanamadı; poz tutuluyor.'
                    self.event('home_timeout', state=self.state, hold_confirmed=self.hold_confirmed)
                except Exception as exc:
                    self.fault(exc)
                return
            self.last_input = self.clock()  # button-initiated move does not require mouse heartbeat
        previous_updated = self.updated
        super().tick()
        if (self.homing and self.state == 'ACTIVE' and self.updated != previous_updated and
                not getattr(self, 'connection_recovering', False)):
            reached = all(abs(self.rows[i]['position'] - p) <= 20 and abs(self.rows[i]['speed']) <= 5
                          for i, p in self.home_reference['positions'].items())
            if reached:
                # Rebase from the actual reached counts, independently from
                # the earlier mouse origin. The saved physical home stays fixed.
                self.profile.origin_raw = {i: row['position'] for i, row in self.rows.items()}
                self.profile.origin_angles = list(self.home_reference['closed_angles'])
                self.homing, self.gesture = False, False
                self.epoch += 1
                self.last_sequence = -1
                self.home_completed_epoch = self.epoch
                self.message = 'Başlangıç pozuna dönüldü.'
                self.event('home_completed', motors=self.rows,
                           closed_angles=self.profile.origin_angles,
                           rebased_origin_raw=self.profile.origin_raw, calibration='UNVERIFIED')

    def activate(self):
        # Every manual activation requires a fresh cooled arm, including after
        # an application restart where no in-memory thermal latch remains.
        try:
            self.require_manual_cooling(self.read_all(checked=False))
        except MotorStatusError as exc:
            self.fault(exc)
            raise
        super().activate()
        self.message = 'Tam hız kontrolü açık · Sol tuş kol, tekerlek kıskaç, sağ tuş görünüm.'

    def snapshot(self):
        return {**super().snapshot(), 'trial_bounds': self.profile.bounds(),
                'motion_speed': self.speed, 'motion_acceleration': self.acceleration,
                'direct_targets': True, 'origin_excursion_limit': None,
                'stream_timeout_s': self.watchdog, 'stream_timeout_action': 'HOLD_WITHOUT_SESSION_LOCK',
                'voltage_limits': self.voltage_limits,
                'homing': self.homing, 'home_available': self.home_reference is not None,
                'home_completed_epoch': self.home_completed_epoch,
                'home_angles': None if self.home_reference is None else list(self.home_reference['closed_angles']),
                'home_raw': None if self.home_reference is None else dict(self.home_reference['positions']),
                'raw_command_bounds': {i: [self.profile.entries[n]['raw_min'], self.profile.entries[n]['raw_max']]
                                       for i, n in enumerate(JOINTS, 1) if i in self.active_ids},
                'calibration': 'UNVERIFIED', 'trial_origin_raw': self.profile.origin_raw}
