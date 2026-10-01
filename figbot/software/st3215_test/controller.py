"""Explicit arming, bounded motion and verified ID changes for one bare motor."""
from .protocol import BusError, BusTimeout, word


class Controller:
    def __init__(self, bus, cancelled=lambda: False):
        self.bus = bus
        self.cancelled = cancelled
        self.servo_id = None
        self.armed = False
        self.origin = None
        self.limits = (0, 4095)

    def inspect(self, servo_id):
        if self.armed:
            raise BusError('Motor seçmeden önce torku kapat.')
        if not 1 <= servo_id <= 253:
            raise ValueError('ID 1–253 olmalı.')
        self.servo_id = None
        self.bus.ping(servo_id)
        model = word(self.bus.read(servo_id, 3, 2))
        mode = self.bus.read(servo_id, 33, 1)[0]
        feedback = self.bus.feedback(servo_id)
        self.servo_id = servo_id
        return model, mode, feedback

    def arm(self, single_unmounted, travel_degrees=60):
        if not single_unmounted or self.servo_id is None:
            raise BusError('Tek motor, mekanizmadan ayrılmış ve gövdesi sabit olmalı.')
        if travel_degrees not in (60, 180, 270):
            raise ValueError('Test aralığı 60, 180 veya 270 derece olmalı.')
        self.armed = False
        servo_id = self.servo_id
        if self.bus.read(servo_id, 33, 1)[0] != 0:
            raise BusError('Motor konum modunda değil. Mod otomatik değiştirilmiyor.')
        self.bus.write(servo_id, 40, [0])
        if self.bus.read(servo_id, 40, 1)[0] != 0:
            raise BusError('Tork kapatma doğrulanamadı.')
        feedback = self.bus.feedback(servo_id)
        if not 0 <= feedback.position <= 4095:
            raise BusError('Tek tur dışında konum; kalibrasyon yapılmadan test engellendi.')
        if not 9 <= feedback.voltage <= 12.6 or feedback.temperature >= 60:
            raise BusError('12 V motor için test gerilimi 9–12,6 V, sıcaklık 60 °C altında olmalı.')
        angle_limits = self.bus.read(servo_id, 9, 4)
        low, high = word(angle_limits[:2]), word(angle_limits[2:])
        if not 0 <= low < high <= 4095 or not low <= feedback.position <= high:
            raise BusError('Motor açı limitleri tezgâh testiyle uyumlu değil; otomatik değiştirilmiyor.')
        span = min(high - low, round(travel_degrees * 4096 / 360))
        start = max(low, min(feedback.position - span // 2, high - span))
        self.limits = start, start + span
        self.origin = feedback.position
        if self.cancelled():
            raise BusError('Test iptal edildi.')
        # Replace any old destination before energizing; verify it was accepted.
        self.bus.goal(servo_id, feedback.position, 171)
        if word(self.bus.read(servo_id, 42, 2)) != feedback.position:
            raise BusError('Başlangıç hedefi doğrulanamadı; tork açılmadı.')
        if self.cancelled():
            raise BusError('Test iptal edildi; tork açılmadı.')
        self.bus.write(servo_id, 40, [1])
        if self.bus.read(servo_id, 40, 1)[0] != 1:
            raise BusError('Tork açılması doğrulanamadı.')
        self.armed = True
        return feedback

    def move(self, position, degrees_per_second):
        if not self.armed or self.cancelled():
            raise BusError('Önce testi etkinleştir.')
        if not self.limits[0] <= position <= self.limits[1]:
            raise BusError('Seçilen test aralığı aşıldı.')
        if degrees_per_second not in (15, 30, 60, 120, 180, 270, 'Maksimum'):
            raise ValueError('Menüdeki hızlardan birini seç.')
        # Waveshare's ST bus-servo position control documents spd=0, acc=0
        # as maximum speed and acceleration. Never use this pair to stop.
        # This requests the fastest profile; measured shaft speed is load-dependent.
        if degrees_per_second == 'Maksimum':
            self.bus.goal(self.servo_id, int(position), 0, acceleration=0)
        else:
            self.bus.goal(self.servo_id, int(position), round(degrees_per_second * 4096 / 360), acceleration=10)

    def stop(self):
        self.armed = False
        # Broadcast works even after an uncertain ID write. This releases ALL bus motors.
        self.bus.write(254, 40, [0])

    def change_id(self, new_id, single_unmounted):
        if not single_unmounted or self.servo_id is None:
            raise BusError('ID değiştirmek için yalnız bir motor fiziksel olarak bağlı olmalı.')
        if not 1 <= new_id <= 253:
            raise ValueError('Yeni ID 1–253 olmalı.')
        old_id = self.servo_id
        if new_id == old_id:
            return
        self.stop()
        try:
            self.bus.ping(new_id)
        except BusTimeout:
            pass
        else:
            raise BusError('Yeni ID kullanımda. Diğer motorları çıkar.')
        try:
            self.bus.write(old_id, 55, [0])
            try:
                self.bus.write(old_id, 5, [new_id])
            except BusTimeout:
                # Firmware may acknowledge at the new ID; verify, never retry the write.
                pass
            if self.bus.read(new_id, 5, 1)[0] != new_id:
                raise BusError('Yeni ID doğrulanamadı.')
            self.servo_id = new_id
        finally:
            # After an interrupted EEPROM transaction either address can still be active.
            locked = False
            for candidate in (new_id, old_id):
                try:
                    self.bus.write(candidate, 55, [1])
                    locked = self.bus.read(candidate, 55, 1)[0] == 1
                    if locked:
                        self.servo_id = candidate
                        break
                except BusError:
                    continue
            if not locked:
                self.servo_id = None
                raise BusError('EEPROM kilidi doğrulanamadı. Gücü kes; yalnız bu motorla yeniden bağlan.')
