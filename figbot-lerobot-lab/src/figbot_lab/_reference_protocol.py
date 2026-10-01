"""Small STS little-endian protocol implementation.

Register map and packet layout verified against Waveshare STServo_Python
scservo_sdk/sms_sts.py and protocol_packet_handler.py (2026-09-19).
No serial connection or writes occur on import.
"""
import time
from dataclasses import dataclass


class BusError(Exception):
    pass


class BusTimeout(BusError):
    pass


class MotorStatusError(BusError):
    """A servo reports a protection fault; preserve it through controller layers."""
    def __init__(self, servo_id, status_flags):
        self.servo_id, self.status_flags = servo_id, status_flags
        super().__init__(f'Motor {servo_id} hata bayrakları: 0x{status_flags:02X}')


def packet(servo_id, instruction, data=b''):
    if not 1 <= servo_id <= 254:
        raise ValueError('Motor ID 1–253 olmalı; 254 yalnız yayın içindir.')
    body = bytes([servo_id, len(data) + 2, instruction]) + bytes(data)
    return b'\xff\xff' + body + bytes([(~sum(body)) & 255])


def signed_magnitude(value, bit=15):
    return -(value & ~(1 << bit)) if value & (1 << bit) else value


def word(data):
    return int.from_bytes(data, 'little')


@dataclass(frozen=True)
class Feedback:
    position: int
    speed: int
    voltage: float
    temperature: int
    current_raw: int
    moving: bool

    @property
    def degrees(self):
        return self.position * 360 / 4096


class Bus:
    def __init__(self, serial_port, timeout=0.18):
        self.serial = serial_port
        self.timeout = timeout

    def transact(self, servo_id, instruction, data=b'', response_size=None):
        self.serial.reset_input_buffer()
        command = packet(servo_id, instruction, data)
        if self.serial.write(command) != len(command):
            raise BusError('USB yazma işlemi tamamlanamadı.')
        if servo_id == 254:
            return b''
        buffer = bytearray()
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            buffer.extend(self.serial.read(max(1, min(self.serial.in_waiting, 256))))
            while len(buffer) >= 4:
                if buffer[:2] != b'\xff\xff':
                    del buffer[0]
                    continue
                length = buffer[3]
                if not 2 <= length <= 64:
                    del buffer[0]
                    continue
                if len(buffer) < length + 4:
                    break
                frame = bytes(buffer[:length + 4])
                if sum(frame[2:]) & 255 != 255:
                    del buffer[0]
                    continue
                del buffer[:length + 4]
                if frame[2] != servo_id:
                    continue
                # Ignore USB transmit echoes, never treat them as acknowledgments.
                if frame == command:
                    continue
                if frame[4]:
                    raise MotorStatusError(servo_id, frame[4])
                payload = frame[5:-1]
                if response_size is not None and len(payload) != response_size:
                    continue
                return payload
        raise BusTimeout(f'ID {servo_id} yanıt vermedi. Güç, B jumperı, kablo ve ID kontrol edilmeli.')

    def ping(self, servo_id):
        self.transact(servo_id, 1, response_size=0)

    def read(self, servo_id, address, length):
        return self.transact(servo_id, 2, bytes([address, length]), length)

    def write(self, servo_id, address, data):
        self.transact(servo_id, 3, bytes([address]) + bytes(data), 0)

    def feedback(self, servo_id):
        data = self.read(servo_id, 56, 15)
        return self.decode_feedback(data)

    @staticmethod
    def decode_feedback(data):
        return Feedback(signed_magnitude(word(data[:2])),
                        signed_magnitude(word(data[2:4])), data[6] / 10,
                        data[7], signed_magnitude(word(data[13:15])), bool(data[10]))

    def feedback_state(self, servo_id):
        # Torque40 and feedback56..70 in one contiguous read, on the same
        # serial owner. This removes six request/response round trips per tick.
        data=self.read(servo_id,40,31)
        return self.decode_feedback(data[16:]),data[0]

    def goal(self, servo_id, position, speed, acceleration=10):
        # In position mode zero is the manufacturer's maximum-speed/acceleration
        # sentinel, NOT a stop command. Torque-off remains a separate operation.
        if not 0 <= position <= 4095 or not 0 <= speed <= 3400 or not 0 <= acceleration <= 150:
            raise ValueError('Tezgâh testi konum/hız/ivme sınırı aşıldı.')
        self.write(servo_id, 41, bytes([acceleration]) + position.to_bytes(2, 'little')
                   + b'\x00\x00' + speed.to_bytes(2, 'little'))

    def close(self):
        self.serial.close()

    def sync_goal(self, profiles):
        """Use the same Feetech SDK GroupSyncWrite used by LeRobot.

        Wrap the already-owned serial handle; never open a second connection.
        Layout matches manufacturer SMS_STS::SyncWritePosEx (address41, 7bytes).
        The caller must verify register readback and actual motion separately.
        """
        from scservo_sdk import GroupSyncWrite, PacketHandler, COMM_SUCCESS
        if not isinstance(profiles, dict) or not 1 <= len(profiles) <= 6:
            raise ValueError('1–6 motor profili gerekli.')
        class ExistingPort:
            is_using = False
            def clearPort(port): self.serial.reset_input_buffer()
            def writePort(port, data): return self.serial.write(bytes(data))
        group = GroupSyncWrite(ExistingPort(), PacketHandler(0), 41, 7)
        for i, (position, speed, acceleration) in profiles.items():
            if type(i) != int or not 1 <= i <= 6 or any(type(v)!=int for v in (position,speed,acceleration)):
                raise ValueError('Geçersiz eşzamanlı motor profili.')
            if not 0 <= position <= 4095 or not 1 <= speed <= 3400 or not 1 <= acceleration <= 150:
                raise ValueError('Eşzamanlı profil sınırı aşıldı.')
            data = bytes([acceleration])+position.to_bytes(2,'little')+b'\0\0'+speed.to_bytes(2,'little')
            if not group.addParam(i,list(data)):
                raise BusError('SDK motor parametresini kabul etmedi.')
        if group.txPacket() != COMM_SUCCESS:
            raise BusError('SDK eşzamanlı yazma başarısız; otomatik tekrar yok.')

    def sync_positions(self, positions):
        """Stream positions only, preserving verified finite speed/acc limits."""
        from scservo_sdk import GroupSyncWrite, PacketHandler, COMM_SUCCESS
        if not isinstance(positions,dict) or not 1<=len(positions)<=6:
            raise ValueError('1–6 motor konumu gerekli.')
        class ExistingPort:
            is_using=False
            def clearPort(port):self.serial.reset_input_buffer()
            def writePort(port,data):return self.serial.write(bytes(data))
        group=GroupSyncWrite(ExistingPort(),PacketHandler(0),42,2)
        for i,p in positions.items():
            if type(i)!=int or not 1<=i<=6 or type(p)!=int or not 0<=p<=4095:
                raise ValueError('Sürekli motor hedefi geçersiz.')
            if not group.addParam(i,list(p.to_bytes(2,'little'))):
                raise BusError('SDK sürekli hedefi kabul etmedi.')
        if group.txPacket()!=COMM_SUCCESS:
            raise BusError('SDK sürekli yazma başarısız; otomatik tekrar yok.')
