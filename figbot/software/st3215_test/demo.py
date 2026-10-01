"""In-memory demo for UI QA; never opens a serial port."""
from .protocol import Feedback, BusTimeout, word


class DemoBus:
    def __init__(self):
        self.motor_id = 1
        self.position = 2048
        self.torque = 0
        self.lock = 1
        self.goal_position = 2048

    def ping(self, servo_id):
        if servo_id != self.motor_id:
            raise BusTimeout('DEMO: Bu ID mevcut değil.')

    def read(self, servo_id, address, length):
        self.ping(servo_id)
        values = {3: (777).to_bytes(2, 'little'), 5: bytes([self.motor_id]),
                  9: b'\x00\x00\xff\x0f', 33: b'\x00', 40: bytes([self.torque]),
                  42: self.goal_position.to_bytes(2, 'little'), 55: bytes([self.lock])}
        return values[address][:length]

    def write(self, servo_id, address, data):
        if servo_id != 254:
            self.ping(servo_id)
        if address == 40:
            self.torque = data[0]
        elif address == 55:
            self.lock = data[0]
        elif address == 5:
            self.motor_id = data[0]

    def feedback(self, servo_id):
        self.ping(servo_id)
        return Feedback(self.position, 0, 12.0, 26, 0, False)

    def goal(self, servo_id, position, speed, acceleration=10):
        self.ping(servo_id)
        self.goal_position = position
        if self.torque:
            self.position = position

    def close(self):
        pass
