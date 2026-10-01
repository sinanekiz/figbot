"""PCA9685 bench protocol. Acknowledgements describe commands, never feedback."""
import time
import serial

JOINTS = ('Taban dönüşü', 'Omuz motoru 1', 'Omuz motoru 2', 'Dirsek', 'Bilek', 'Tutucu / kıskaç')
SHOULDERS = (1, 7)


def channel_mask(channel):
    return 3 << channel if channel in SHOULDERS else 1 << channel


class PCAController:
    def __init__(self, factory=serial.Serial, clock=time.monotonic):
        self.factory, self.clock = factory, clock
        self.link = None
        self.ready = False
        self.enabled = self.active = 0
        self.buffer = ''
        self.last_rx = self.last_ping = 0
        self.message = 'Bağlı değil'
        self.acks = {}

    def connect(self, port):
        self.disconnect()
        self.link = self.factory(port=port, baudrate=115200, timeout=0, write_timeout=.25)
        self.buffer = ''
        self.acks = {}
        self.deadline = self.clock() + 6
        self.last_ping = 0
        self.message = 'UNO / PCA9685 yanıtı bekleniyor…'

    def write(self, data):
        if not self.link:
            raise RuntimeError('Önce bağlan.')
        self.link.write(data.encode('ascii'))

    def handle_line(self, line):
        if line == 'FIGBOT_PCA9685_V5':
            self.ready = False
            self.enabled = self.active = 0
        elif line.startswith(('STATUS ', 'STATUS2 ', 'STATUS3 ', 'STATUS4 ')) or line in ('FIGBOT_PCA9685_V1', 'FIGBOT_PCA9685_V2', 'FIGBOT_PCA9685_V3', 'FIGBOT_PCA9685_V4'):
            raise RuntimeError('360°/sn ayarı için UNO V5 yazılımı yüklenmeli')
        elif line.startswith('STATUS5 '):
            fields = line[8:].split(',')
            if len(fields) != 2 or not all(x.isdigit() for x in fields):
                raise RuntimeError('Geçersiz kart yanıtı')
            enabled, active = map(int, fields)
            if not (0 <= enabled < 4096 and 0 <= active < 4096) or active & ~enabled:
                raise RuntimeError('Geçersiz kanal maskesi')
            for c in SHOULDERS:
                if any((mask >> c) & 3 not in (0, 3) for mask in (enabled, active)):
                    raise RuntimeError('Omuz kanalları eşlenmemiş; durduruluyor')
            self.enabled, self.active = enabled, active
            self.ready = True
            self.last_rx = self.clock()
            self.message = 'PCA9685 bağlı · 0x40 · hedefler komut açısıdır'
        elif line.startswith('PAIR '):
            fields = list(map(int, line[5:].split(',')))
            if len(fields) != 5 or fields[0] not in SHOULDERS or not 0 <= fields[1] <= 180 or not 10 <= fields[2] <= 360 or fields[3] not in range(500,1001,100) or fields[4] != 3000-fields[3]:
                raise RuntimeError('Geçersiz omuz onayı')
            ch, angle, speed, lo, hi = fields
            self.acks[ch] = [angle, speed, lo, hi]
            self.acks[ch+1] = [180-angle, speed, lo, hi]
            self.last_rx = self.clock()
        elif line.startswith('ACK '):
            fields = list(map(int, line[4:].split(',')))
            if len(fields) != 5 or not 0 <= fields[0] < 12:
                raise RuntimeError('Geçersiz hareket onayı')
            self.acks[fields[0]] = fields[1:]
            self.last_rx = self.clock()
        elif line.startswith('OFF '):
            self.enabled = self.active = 0
            self.message = 'PWM kapalı; motor elektriği kesilmedi. Kolu destekle.'
        elif line.startswith('ERR '):
            raise RuntimeError(line)

    def poll(self):
        if not self.link:
            return
        waiting = self.link.in_waiting
        if waiting:
            self.buffer += self.link.read(min(waiting, 4096)).decode('ascii', errors='replace')
            if len(self.buffer) > 8192:
                raise RuntimeError('Seri veri sınırı aşıldı')
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                self.handle_line(line.strip())
        now = self.clock()
        if (not self.ready and now > self.deadline) or (self.ready and now - self.last_rx > 1.2):
            raise RuntimeError('Kart yanıt vermiyor; bağlantı kapatılıyor.')
        if now - self.last_ping >= .3:
            self.write('H\n')
            self.last_ping = now

    def arm(self, channel, enabled):
        self.require_channel(channel)
        self.write(f'{"E" if enabled else "D"}{channel}\n')

    def require_channel(self, channel):
        if type(channel) is not int or not 0 <= channel < 12:
            raise ValueError('Kanal 0–11 olmalı')
        if channel in (2, 8):
            raise ValueError('Karşı omuz motoru bağımsız sürülemez; ortak omuz kontrolünü kullan')
        if not self.ready:
            raise RuntimeError('PCA9685 henüz hazır değil')

    def position(self, channel, angle, speed, wide=False):
        self.require_channel(channel)
        mask = channel_mask(channel)
        if self.enabled & mask != mask:
            raise RuntimeError('Önce bu kanalı etkinleştir')
        if type(angle) is not int or not 0 <= angle <= 180 or type(speed) is not int or not 10 <= speed <= 360:
            raise ValueError('Açı 0–180, hız 10–360 olmalı')
        lo, hi = (500, 2500) if wide else (1000, 2000)
        if channel in SHOULDERS:
            if wide:
                raise ValueError('Omuz: yalnız dar darbe aralığı, hız 10–360 komut derece/sn')
            if self.active & mask != mask and angle != 90:
                raise ValueError('Önce mekanik bağlantı ayrıkken omuzu 90° merkezle')
            self.write(f'S{channel},{angle},{speed},1000,2000\n')
        else:
            self.write(f'P{channel},{angle},{speed},{lo},{hi}\n')

    def stop(self):
        if self.link:
            self.write('X\n')
        self.enabled = self.active = 0

    def disconnect(self):
        if self.link:
            try:
                self.write('X\n')
            except (OSError, serial.SerialException):
                pass
            finally:
                try:
                    self.link.close()
                finally:
                    self.link = None
                    self.ready = False
                    self.enabled = self.active = 0
        self.ready = False
        self.enabled = self.active = 0

    def snapshot(self):
        return dict(ready=self.ready, enabled=self.enabled, active=self.active,
                    message=self.message, acks=dict(self.acks), connected=self.link is not None)
