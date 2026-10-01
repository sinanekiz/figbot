"""Mouse teleoperation in a separate, explicit motor controller.

Calibration's READ-only bus stays unchanged. No import opens serial or writes.
This is supervised joint control, not a collision/force safety controller.
"""
from __future__ import annotations
from dataclasses import asdict
import math
import time
from .common import JOINTS, ROOT, load_json, sha256
from ._reference_protocol import Bus, BusError, BusTimeout, MotorStatusError, word

COUNTS_PER_RADIAN = 4096 / (2 * math.pi)
RATE = 45.0  # initial experiment counts/s, not a physically validated safe speed
SPEED, ACCELERATION = 57, 1
WATCHDOG = .35
MANUAL_THERMAL_CUTOFF_C, MANUAL_COOLDOWN_C = 55, 45
_EMERGENCY_TORQUE_OFF = object()


class MotionWriteTimeout(BusTimeout):
    """A WRITE may have reached the servo; its requested goal is never replayed."""


class MotorOverheat(BusError):
    """A measured temperature requires torque release, never a holding goal."""


class MotionBus(Bus):
    """Only telemetry, bounded SRAM motion and torque-on; no EEPROM operations."""
    motion_speed, motion_acceleration = SPEED, ACCELERATION
    def disable_torque(self, servo_id, *, authority=None):
        if authority is not _EMERGENCY_TORQUE_OFF or type(servo_id) is not int or servo_id not in range(1, 7):
            raise BusError('Acil tork kapatma yetkisi ve motor 1–6 gerekli.')
        # The ordinary transact guard still rejects torque-off. This dedicated
        # operation permits exactly one motor's volatile torque byte, no EEPROM.
        return Bus.transact(self, servo_id, 3, b'\x28\x00', response_size=0)
    def transact(self, servo_id, instruction, data=b'', response_size=None):
        if servo_id not in range(1, 7):
            raise BusError('Sanal sürücü yalnız motor 1–6 ile çalışır.')
        if instruction == 2:
            if len(data) != 2 or not 0 <= data[0] <= 70 or not 1 <= data[1] <= 40 or data[0] + data[1] > 71:
                raise BusError('Geçersiz okuma aralığı.')
        elif instruction == 3:
            if data == b'\x28\x01':
                pass
            elif len(data) == 8 and data[0] == 41:
                position, speed = word(data[2:4]), word(data[6:8])
                if data[1] != self.motion_acceleration or not 0 <= position <= 4095 or speed != self.motion_speed or data[4:6] != b'\0\0':
                    raise BusError('Sınırlı hareket profili gerekli.')
            else:
                raise BusError('Yalnız sınırlı SRAM hedefi veya açık tork komutu izinli.')
        else:
            raise BusError('Kalıcı ayar, yayın ve SDK yazmaları engellendi.')
        return super().transact(servo_id, instruction, data, response_size)

    def sync_goal(self, profiles):
        raise BusError('Yayın yazması bu denetleyicide kullanılmaz.')

    def sync_positions(self, positions):
        raise BusError('Yayın yazması bu denetleyicide kullanılmaz.')


class Profile:
    verified = True
    control_mode = 'CALIBRATED'
    def __init__(self, value):
        if value.get('status') != 'VERIFIED' or not isinstance(value.get('evidence'), str) or not value['evidence'].strip():
            raise ValueError('Gerçek sürüş için fiziksel eşleme gerekli. SANAL_SURUCU.md dosyasına bakın.')
        entries = value.get('joints', {})
        if set(entries) != set(JOINTS):
            raise ValueError('Altı eklem eşlemesi gerekli.')
        for motor, name in enumerate(JOINTS, 1):
            entry = entries[name]
            if entry.get('id') != motor or type(entry['id']) is not int:
                raise ValueError('Eklem/motor sırası hatalı.')
            for field in ('zero_raw', 'raw_min', 'raw_max', 'offset_encoded'):
                if type(entry.get(field)) is not int:
                    raise ValueError(f'{name}: {field} doğrulanmamış.')
            if (not 0 <= entry['raw_min'] < entry['raw_max'] <= 4095 or
                    not 0 <= entry['zero_raw'] <= 4095 or not 0 <= entry['offset_encoded'] <= 65535 or
                    type(entry.get('direction')) is not int or entry['direction'] not in (-1, 1) or
                    not isinstance(entry.get('evidence'), str) or not entry['evidence'].strip()):
                raise ValueError(f'{name}: fiziksel yön/sınır/kanıt hatalı.')
        self.entries = entries

    def angles(self, positions):
        return [(positions[i + 1] - self.entries[n]['zero_raw']) /
                (COUNTS_PER_RADIAN * self.entries[n]['direction']) for i, n in enumerate(JOINTS)]

    def targets(self, angles):
        if (not isinstance(angles, list) or len(angles) != 6 or
                any(type(v) not in (int, float) or not math.isfinite(v) for v in angles)):
            raise ValueError('Altı sonlu eklem açısı gerekli.')
        result = {}
        for i, (name, angle) in enumerate(zip(JOINTS, angles), 1):
            entry = self.entries[name]
            raw = round(entry['zero_raw'] + entry['direction'] * COUNTS_PER_RADIAN * angle)
            if not entry['raw_min'] <= raw <= entry['raw_max']:
                raise ValueError(f'{name}: doğrulanmış çalışma sınırı aşıldı.')
            result[i] = raw
        return result


class MotionController:
    """One serial owner. Caller serializes API calls and tick with one lock."""
    def __init__(self, bus=None, profile=None, clock=time.monotonic, on_event=None, *, active_ids=None):
        self.active_ids = tuple(range(1, 7)) if active_ids is None else tuple(active_ids)
        if self.active_ids not in (tuple(range(1, 7)), tuple(range(1, 6))):
            raise ValueError('Yalnız altı motor veya açıkça seçilmiş beş motor düzeni kullanılabilir.')
        if profile and profile.verified and len(self.active_ids) != 6:
            raise ValueError('Beş motor düzeninde eski doğrulanmış profil kullanılamaz.')
        self.bus, self.profile, self.clock = bus, profile, clock
        self.on_event = on_event or (lambda event: None)
        self.state = 'DISCONNECTED' if bus is None else 'CONNECTED'
        self.message = 'Gerçek kol bağlı değil.'
        self.rows, self.settings, self.targets, self.desired = {}, {}, {}, {}
        self.updated = None
        self.last_tick, self.last_input = clock(), clock()
        self.epoch = 0
        self.last_sequence = -1
        self.gesture = False
        self.may_be_live = False
        self.last_write = {}
        self.rate, self.lead = RATE, 16
        self.speed, self.acceleration = SPEED, ACCELERATION
        self.direct_targets = False
        self.watchdog = WATCHDOG
        self.soft_watchdog = False
        self.hold_settle_seconds = 0
        # Manual operation opts in explicitly. Verified/probe behavior stays latched.
        self.recover_read_timeouts = False
        self.connection_recovering = False
        self.hold_confirmed = None
        self.recovery_attempts = 0
        self.next_recovery_read = 0.
        self.thermal_latched = False
        self.emergency_latched = False
        self.torque_release_confirmed = None
        self.emergency_result = None
        self.next_emergency_read = 0.
        self.manual_temperature_monitor = False

    def event(self, kind, **values):
        self.on_event({'kind': kind, 'monotonic': self.clock(), **values})

    def read_all(self, checked=True):
        began = self.clock()
        rows = {}
        for i in self.active_ids:
            feedback, torque = self.bus.feedback_state(i)
            r = {**asdict(feedback), 'torque': torque}
            if (not 0 <= r['position'] <= 4095 or torque not in (0, 1) or
                    checked and (not 10 <= r['voltage'] <= 12.6 or
                                 r['temperature'] >= 55 or abs(r['current_raw']) > 150)):
                raise BusError(f'ID{i}: konum/gerilim/sıcaklık/akım/tork denetimi başarısız.')
            rows[i] = r
        if self.clock() - began > .25:
            raise BusError('Motor ölçümü 250 ms sınırını aştı.')
        self.rows, self.updated = rows, self.clock()
        self.event('feedback', read_interval=[began, self.updated], motors=rows)
        return rows

    def connect_snapshot(self):
        from .calibration import read_settings
        self.settings = read_settings(self.bus, motor_ids=self.active_ids) if len(self.active_ids) != 6 else read_settings(self.bus)
        self.read_all(checked=False)  # telemetry remains readable above motion thresholds
        self.message = 'Konumlar okundu; motorlara hareket komutu gönderilmedi.'

    def activate(self):
        try:
            self._activate()
        except MotorStatusError as exc:
            self.fault(exc)
            raise

    def _activate(self):
        if self.emergency_latched:
            raise ValueError('Acil kesme kilidi için yeni soğuma ölçümü ve açık yeniden başlatma gerekli.')
        if self.state != 'CONNECTED' or self.profile is None:
            raise ValueError('Kontrol başlangıcı için bağlı kol ve doğrulanmış eşleme gerekli.')
        try:
            first = self.read_all()
        except MotorOverheat as exc:
            self.emergency_torque_off(str(exc), thermal=True)
            raise
        for i, name in enumerate(JOINTS, 1):
            if i not in self.active_ids:
                continue
            e, s, r = self.profile.entries[name], self.settings[name], first[i]
            if (s['homing_offset_encoded'] != e['offset_encoded'] or s['operating_mode'] != 0 or
                    word(bytes.fromhex(s['registers_0_39_hex'])[3:5]) != 777 or
                    not e['raw_min'] <= r['position'] <= e['raw_max'] or r['moving'] or abs(r['speed']) > 5):
                raise BusError(f'ID{i}: model, ofset, sınır veya sabit başlangıç pozu uyuşmuyor.')
            if r['torque'] and abs(word(self.bus.read(i, 42, 2)) - r['position']) > 20:
                raise BusError('Mevcut donanım hedefi ölçülen pozdan uzak.')
        try:
            second = self.read_all()
        except MotorOverheat as exc:
            self.emergency_torque_off(str(exc), thermal=True)
            raise
        if any(abs(second[i]['position'] - first[i]['position']) > 8 or second[i]['moving'] or
               abs(second[i]['speed']) > 5 or second[i]['torque'] != first[i]['torque'] for i in first):
            raise BusError('Başlangıç ölçümünde kol hareket etti.')
        self.targets = {i: float(r['position']) for i, r in second.items()}
        self.desired = dict(self.targets)
        self.may_be_live = True  # even a timed-out goal write may enable torque
        try:
            for i in self.active_ids:
                if abs(self.bus.feedback(i).position - self.targets[i]) > 8:
                    raise BusError('Etkinleştirme sırasında kol oynadı.')
                self.write_goal(i, round(self.targets[i]))
                if self.bus.read(i, 40, 1) != b'\1':
                    self.bus.write(i, 40, b'\1')
                if self.bus.read(i, 40, 1) != b'\1':
                    raise BusError('Motor tutması doğrulanamadı.')
            self.read_all()
            if any(abs(self.rows[i]['position'] - self.targets[i]) > 8 for i in self.rows):
                raise BusError('Etkinleştirme sırasında başlangıç pozu değişti.')
        except Exception as exc:
            self.fault(exc)
            raise
        self.state, self.gesture = 'ACTIVE', False
        self.torque_release_confirmed = False
        self.epoch += 1
        self.last_sequence = -1
        self.last_input = self.last_tick = self.clock()
        self.message = 'Gerçek kol mevcut pozdan kontrol ediliyor.'
        self.event('activated', epoch=self.epoch, positions=self.targets)

    def write_goal(self, motor, position):
        began = self.clock()
        try:
            self.bus.goal(motor, position, self.speed, self.acceleration)
        except (BusTimeout, OSError) as exc:
            if self.recover_read_timeouts:
                raise MotionWriteTimeout(f'ID{motor}: hedef yazma yanıtı doğrulanamadı: {exc}') from exc
            raise
        expected = bytes([self.acceleration]) + position.to_bytes(2, 'little') + b'\0\0' + self.speed.to_bytes(2, 'little')
        if self.bus.read(motor, 41, 7) != expected:
            raise BusError(f'ID{motor}: komut geri okuması uyuşmuyor.')
        self.last_write[motor] = position
        self.event('command', motor=motor, position=position, speed=self.speed,
                   acceleration=self.acceleration, write_interval=[began, self.clock()], verified=True)

    def input(self, angles, epoch, sequence, gesture):
        if self.connection_recovering:
            self.event('input_ignored_during_recovery', epoch=epoch)
            return
        if self.state != 'ACTIVE' or type(epoch) is not int or epoch != self.epoch:
            if self.soft_watchdog and self.state == 'ACTIVE' and type(epoch) is int and epoch < self.epoch:
                self.event('stale_input_ignored', epoch=epoch, current_epoch=self.epoch)
                return
            raise ValueError('Kontrol oturumu etkin değil; eski komut reddedildi.')
        if type(sequence) is not int or sequence <= self.last_sequence or type(gesture) is not bool:
            raise ValueError('Komut sırası veya fare durumu geçersiz.')
        if not gesture:
            self.hold()
            self.last_sequence = sequence
            return
        try:
            desired = self.profile.targets(angles)  # validate entire request before mutation
        except (ValueError, TypeError) as exc:
            self.fault('Geçersiz hareket hedefi: ' + str(exc))
            raise
        self.desired, self.gesture = desired, True
        self.last_input, self.last_sequence = self.clock(), sequence

    def hold(self):
        self.gesture = False
        self.epoch += 1  # invalidate any delayed request from a released drag
        self.last_sequence = -1
        if self.emergency_latched:
            return  # a thermal/emergency stop must never become a holding goal
        if not self.may_be_live:
            return
        if self.connection_recovering:
            return  # recovery reads first; releasing the mouse cannot repeat a WRITE
        try:
            self._hold_measured()
        except (MotorOverheat, MotorStatusError) as exc:
            self.fault(exc)
        except (BusTimeout, OSError) as exc:
            if not self.recover_read_timeouts:
                raise
            self._begin_link_recovery(exc, 'hold')

    def _hold_measured(self):
        """Fresh complete feedback always precedes a measured-pose hold."""
        rows = self.read_all()
        self.targets = {i: float(r['position']) for i, r in rows.items()}
        self.desired = dict(self.targets)
        for i in rows:
            self.write_goal(i, round(self.targets[i]))
        deadline = self.clock() + self.hold_settle_seconds
        for _ in range(20):
            verify = self.read_all()
            if any(verify[i]['torque'] != 1 for i in verify):
                raise BusError('Konum tutma sırasında motor torku kayboldu.')
            if all(abs(verify[i]['position'] - self.targets[i]) <= 20 for i in verify):
                break
            if self.clock() >= deadline:
                raise BusError('Konum tutma doğrulanamadı.')
            time.sleep(.02)
        else:
            raise BusError('Konum tutma doğrulanamadı.')
        self.last_input = self.last_tick = self.clock()
        self.message = 'Fare bırakıldı; ölçülen poz tutuluyor.'
        self.hold_confirmed = True
        self.event('hold', epoch=self.epoch, positions=self.targets)

    def cancel_pending_motion(self):
        self.gesture = False
        self.targets = {i: float(r['position']) for i, r in self.rows.items()}
        self.desired = dict(self.targets)

    def check_manual_temperature(self, rows):
        hot = {i: row['temperature'] for i, row in rows.items()
               if row['temperature'] >= MANUAL_THERMAL_CUTOFF_C}
        if hot:
            values = ', '.join(f'ID{i}: {temperature} °C' for i, temperature in hot.items())
            raise MotorOverheat(f'Motor sıcaklık kesmesi ({MANUAL_THERMAL_CUTOFF_C} °C): {values}.')

    def require_manual_cooling(self, rows):
        if (set(rows) != set(self.active_ids) or rows is not self.rows or self.updated is None or
                self.clock() - self.updated > .25):
            raise ValueError('Başlatmak için etkin motorların yeni sıcaklık ölçümü gerekli.')
        try:
            self.check_manual_temperature(rows)
        except MotorOverheat as exc:
            if not self.emergency_latched:
                self.emergency_torque_off(str(exc), thermal=True)
            else:
                self.thermal_latched = True
                self.state = 'THERMAL_CUTOFF' if self.torque_release_confirmed else 'THERMAL_UNCONFIRMED'
                self.message = str(exc) + ' Soğuma bekleniyor; tork yeniden açılmadı.'
            raise
        if any(row['temperature'] > MANUAL_COOLDOWN_C for row in rows.values()):
            raise ValueError(f'Motorlar {MANUAL_COOLDOWN_C} °C veya altına soğumadan kontrol açılamaz.')
        if self.emergency_latched:
            if any(row['torque'] != 0 for row in rows.values()):
                raise ValueError('Yeniden başlatmadan önce etkin motorların tork kapatması doğrulanmalı.')
            self.thermal_latched = self.emergency_latched = False
            self.state = 'CONNECTED'
            self.may_be_live = False
            self.hold_confirmed = None
            self.cancel_pending_motion()
            self.event('emergency_reset_for_explicit_activation', motors=rows)

    def emergency_torque_off(self, message='Acil tork kapatma istendi.', *, thermal=False):
        """One off WRITE per motor, independent acknowledgments and READ verification."""
        self.cancel_pending_motion()
        self.connection_recovering = False
        self.emergency_latched = True
        self.thermal_latched = self.thermal_latched or thermal
        self.hold_confirmed = False
        self.torque_release_confirmed = False
        self.epoch += 1
        self.last_sequence = -1
        self.state = 'THERMAL_UNCONFIRMED' if self.thermal_latched else 'EMERGENCY_UNCONFIRMED'
        motors = {}
        for i in self.active_ids:
            row = motors[i] = {'write_acknowledged': False, 'torque': None, 'torque_off_confirmed': False}
            try:
                if self.bus is None:
                    raise BusError('Seri bağlantı açık değil.')
                self.bus.disable_torque(i, authority=_EMERGENCY_TORQUE_OFF)
                row['write_acknowledged'] = True
            except Exception as exc:
                row['write_error'] = str(exc)  # attempt every other motor once too
        for i, row in motors.items():
            try:
                if self.bus is None:
                    raise BusError('Seri bağlantı açık değil.')
                value = self.bus.read(i, 40, 1)
                if value not in (b'\0', b'\1'):
                    raise BusError('Tork geri okuması geçersiz.')
                row['torque'] = value[0]
                row['torque_off_confirmed'] = value == b'\0'
                if i in self.rows:
                    self.rows[i]['torque'] = value[0]
            except Exception as exc:
                row['read_error'] = str(exc)
        confirmed = all(row['torque_off_confirmed'] for row in motors.values())
        self.torque_release_confirmed = confirmed
        self.may_be_live = not confirmed
        if confirmed:
            self.state = 'THERMAL_CUTOFF' if self.thermal_latched else 'EMERGENCY_TORQUE_OFF'
        self.emergency_result = {'motors': motors, 'torque_release_confirmed': confirmed,
                                 'thermal_latched': self.thermal_latched, 'reason': str(message)}
        self.message = (str(message) + (' Etkin motorların torku kapatıldı.' if confirmed else
                       ' Tork kapatması doğrulanamadı; motor beslemesini kesin.'))
        self.next_emergency_read = self.clock() + .5
        self.event('thermal_cutoff' if self.thermal_latched else 'emergency_torque_off',
                   state=self.state, message=self.message, **self.emergency_result)
        return self.emergency_result

    def _read_emergency_state(self):
        if self.clock() < self.next_emergency_read:
            return
        self.next_emergency_read = self.clock() + .5
        try:
            rows = self.read_all(checked=False)
            self.torque_release_confirmed = all(row['torque'] == 0 for row in rows.values())
            self.may_be_live = not self.torque_release_confirmed
            if self.torque_release_confirmed:
                self.state = 'THERMAL_CUTOFF' if self.thermal_latched else 'EMERGENCY_TORQUE_OFF'
            else:
                self.state = 'THERMAL_UNCONFIRMED' if self.thermal_latched else 'EMERGENCY_UNCONFIRMED'
        except Exception as exc:
            self.event('emergency_read_failed', message=str(exc))

    def _begin_link_recovery(self, exc, operation):
        if not self.connection_recovering:
            self.cancel_pending_motion()
            self.connection_recovering = True
            self.hold_confirmed = False
            self.epoch += 1
            self.last_sequence = -1
            self.recovery_attempts = 0
            self.next_recovery_read = self.clock()
            self.event('link_paused', operation=operation, message=str(exc), epoch=self.epoch,
                       write_ack_uncertain=isinstance(exc, MotionWriteTimeout), hold_confirmed=False)
        self.message = 'Motor yanıtı bekleniyor; hareket hedefi iptal edildi, tutma henüz doğrulanmadı.'

    def _retry_link(self):
        if self.clock() < self.next_recovery_read:
            return
        self.recovery_attempts += 1
        self.cancel_pending_motion()
        try:
            # This reads all six motors before writing any newly measured hold.
            # A lost WRITE acknowledgment never causes its old goal to be retried.
            if self.may_be_live:
                self._hold_measured()
            else:
                # A failed activation preflight must retain READ-only semantics.
                rows = self.read_all(checked=False)
                self.targets = {i: float(r['position']) for i, r in rows.items()}
                self.desired = dict(self.targets)
        except (BusTimeout, OSError) as exc:
            delay = min(1., .1 * 2 ** min(self.recovery_attempts - 1, 4))
            self.next_recovery_read = self.clock() + delay
            self.hold_confirmed = False
            self.message = 'Motor yanıtı bekleniyor; yeni hareket komutu gönderilmiyor, tutma doğrulanmadı.'
            self.event('link_read_retry', attempt=self.recovery_attempts, retry_in_s=delay,
                       message=str(exc), write_ack_uncertain=isinstance(exc, MotionWriteTimeout),
                       hold_confirmed=False)
            return
        except MotorOverheat as exc:
            self.emergency_torque_off(str(exc), thermal=True)
            return
        except Exception as exc:
            self.connection_recovering = False
            self.fault(exc)  # motor error flags and physical checks stay faults
            return
        self.connection_recovering = False
        self.hold_confirmed = True if self.may_be_live else None
        self.epoch += 1  # also discard requests queued while the link was recovering
        self.last_sequence = -1
        self.last_input = self.last_tick = self.clock()
        self.message = ('Motor bağlantısı yenilendi; ölçülen poz tutuluyor. Yeni fare hareketiyle devam edin.'
                        if self.may_be_live else 'Motor bağlantısı yenilendi; konumlar okundu.')
        self.event('link_recovered', attempt=self.recovery_attempts, epoch=self.epoch,
                   positions=self.targets, hold_confirmed=self.hold_confirmed)

    def fault(self, message):
        if isinstance(message, (MotorStatusError, MotorOverheat)):
            thermal = isinstance(message, MotorOverheat) or bool(message.status_flags & 0x04)
            if self.emergency_latched:
                self.thermal_latched = self.thermal_latched or thermal
                if self.thermal_latched:
                    self.state = 'THERMAL_CUTOFF' if self.torque_release_confirmed else 'THERMAL_UNCONFIRMED'
                return
            self.emergency_torque_off(str(message), thermal=thermal)
            return
        if self.emergency_latched:
            return  # later fault handling must not undo the torque release
        message = str(message)
        self.connection_recovering = False
        recover = self.recover_read_timeouts
        self.recover_read_timeouts = False
        try:
            self.hold()
            if self.emergency_latched:
                return
            self.state = 'FAULT_HOLD' if self.may_be_live else 'FAULT'
        except Exception:
            self.state = 'FAULT_UNCONFIRMED'
            self.hold_confirmed = False
        finally:
            self.recover_read_timeouts = recover
            self.connection_recovering = False
        self.message = message + (' Kolun durduğunu doğrulayamadım; fiziksel durumu kontrol edin.'
                                  if self.state == 'FAULT_UNCONFIRMED' else ' Kontrol durduruldu.')
        self.event('fault', message=self.message, state=self.state)

    def tick(self):
        if self.bus is not None and self.emergency_latched:
            self._read_emergency_state()
            return
        if self.bus is None or self.state not in ('CONNECTED', 'ACTIVE'):
            return
        try:
            if self.connection_recovering:
                self._retry_link()
                return
            self.read_all(checked=self.state == 'ACTIVE')
            if self.manual_temperature_monitor:
                self.check_manual_temperature(self.rows)
            now = self.clock()
            if self.state != 'ACTIVE':
                return
            if any(r['torque'] != 1 for r in self.rows.values()):
                raise BusError('Motor tutması kayboldu.')
            if now - self.last_input > self.watchdog:
                if self.gesture:
                    if self.soft_watchdog:
                        self.hold()
                        self.message = 'Komut akışı gecikti; poz tutuluyor, kontrol açık.'
                        self.event('stream_paused', epoch=self.epoch)
                    else:
                        self.fault('Fare/tarayıcı iletişimi kesildi.')
                return
            dt = min(now - self.last_tick, .1)
            self.last_tick = now
            if not self.gesture:
                return
            for i, r in self.rows.items():
                if self.direct_targets:
                    target = self.desired[i]
                    self.targets[i] = target
                    if target != self.last_write.get(i):
                        self.write_goal(i, target)
                    continue
                if abs(r['position'] - self.targets[i]) > 80:
                    raise BusError(f'ID{i}: hareket takibi sapması.')
                # Neither a fast mouse drag nor a large request may build a far-away trajectory.
                change = max(-self.rate * dt, min(self.rate * dt, self.desired[i] - self.targets[i]))
                target = max(r['position'] - self.lead, min(r['position'] + self.lead, self.targets[i] + change))
                self.targets[i] = target
                if round(target) != self.last_write.get(i):
                    self.write_goal(i, round(target))
        except MotorOverheat as exc:
            self.emergency_torque_off(str(exc), thermal=True)
        except (BusTimeout, OSError) as exc:
            if self.recover_read_timeouts:
                self._begin_link_recovery(exc, 'write' if isinstance(exc, MotionWriteTimeout) else 'read')
                self._retry_link()
            else:
                self.fault(exc)
        except Exception as exc:
            self.fault(exc)

    def snapshot(self):
        positions = {i: r['position'] for i, r in self.rows.items()}
        return {'state': self.state, 'message': self.message, 'epoch': self.epoch,
                'active_motor_ids': list(self.active_ids), 'gripper_available': 6 in self.active_ids,
                'profile_verified': bool(self.profile and self.profile.verified), 'motors': self.rows,
                'control_mode': self.profile.control_mode if self.profile else 'SIMULATION',
                'angles': self.profile.angles(positions) if self.profile and positions else None,
                'connection_recovering': self.connection_recovering,
                'hold_confirmed': self.hold_confirmed,
                'gesture_active': self.gesture,
                'thermal_latched': self.thermal_latched,
                'thermal_cutoff_c': MANUAL_THERMAL_CUTOFF_C,
                'cooldown_c': MANUAL_COOLDOWN_C,
                'emergency_latched': self.emergency_latched,
                'torque_release_confirmed': self.torque_release_confirmed,
                'emergency_result': self.emergency_result,
                'manual_temperature_monitor': self.manual_temperature_monitor,
                'read_retry_in_s': max(0., self.next_recovery_read - self.clock()) if self.connection_recovering else None,
                'sample_age_s': None if self.updated is None else self.clock() - self.updated}

    def disconnect(self):
        if self.bus is not None and self.recover_read_timeouts and not self.emergency_latched:
            # Manual control must not leave the last pose powered indefinitely.
            # Verified/probe controllers retain their existing disconnect hold.
            self.emergency_torque_off('Manuel bağlantı kapatılıyor; motor torku bırakılıyor.')
        was_live = self.may_be_live
        error = None
        if self.bus:
            recover = self.recover_read_timeouts
            self.recover_read_timeouts = False
            self.connection_recovering = False
            try:
                if self.may_be_live and not self.emergency_latched:
                    self.hold()
            except Exception as exc:
                error = str(exc)
                self.hold_confirmed = False
            finally:
                self.bus.close()
                self.bus = None
                self.recover_read_timeouts = recover
        self.state = 'FAULT_UNCONFIRMED' if error else 'DISCONNECTED'
        if self.emergency_latched:
            self.state = 'DISCONNECTED' if self.torque_release_confirmed else 'FAULT_UNCONFIRMED'
            self.message = ('Bağlantı kapandı; motor torku kapalı olarak doğrulanmıştı.' if self.torque_release_confirmed
                            else 'Bağlantı kapandı; tork kapatması doğrulanamadı, motor beslemesini kesin.')
        else:
            self.message = ('Bağlantı kapandı; tutma doğrulanamadı: ' + error if error else
                            'Bağlantı kapandı. Son ölçülen pozu tutma komutu gönderildi.' if was_live else
                            'Bağlantı kapandı.')
        self.may_be_live = False
        self.gesture = False
        self.connection_recovering = False
        self.epoch += 1


def load_profile():
    path = ROOT / 'configs/virtual_leader.verified.json'
    if not path.exists():
        return None, 'Fiziksel eklem eşlemesi gerekli.'
    try:
        return Profile(load_json(path)), sha256(path)
    except (ValueError, KeyError, TypeError) as exc:
        return None, str(exc)
