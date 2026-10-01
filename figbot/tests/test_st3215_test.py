"""Hardware-free protocol, motor gating and queue regression tests."""
import time
import unittest
from dataclasses import replace
from software.st3215_test.protocol import Bus, BusError, BusTimeout, packet, signed_magnitude
from software.st3215_test.controller import Controller
from software.st3215_test.demo import DemoBus
from software.st3215_test.app import Worker


def status(servo_id, data=b'', error=0):
    body = bytes([servo_id, len(data) + 2, error]) + data
    return b'\xff\xff' + body + bytes([~sum(body) & 255])


class SerialFake:
    def __init__(self, response):
        self.response = response
        self.buffer = bytearray()
        self.written = []
        self.closed = False

    @property
    def in_waiting(self):
        return len(self.buffer)

    def reset_input_buffer(self):
        self.buffer.clear()

    def write(self, data):
        self.written.append(data)
        self.buffer.extend(self.response)
        return len(data)

    def read(self, length):
        # Exercise partial serial reads.
        result = self.buffer[:min(length, 3)]
        del self.buffer[:len(result)]
        return result

    def close(self):
        self.closed = True


class RecordingBus(DemoBus):
    def __init__(self):
        super().__init__()
        self.history = []
        self.mode = 0
        self.voltage = 12.0
        self.temperature = 26
        self.corrupt_goal = False
        self.goal_profiles = []

    def read(self, servo_id, address, length):
        if address == 33:
            return bytes([self.mode])
        if address == 42 and self.corrupt_goal:
            return b'\x00\x00'
        return super().read(servo_id, address, length)

    def write(self, servo_id, address, data):
        self.history.append(('write', servo_id, address, list(data)))
        super().write(servo_id, address, data)

    def goal(self, servo_id, position, speed, acceleration=10):
        self.goal_profiles.append((position, speed, acceleration))
        self.history.append(('goal', servo_id, position, speed))
        super().goal(servo_id, position, speed, acceleration)

    def feedback(self, servo_id):
        return replace(super().feedback(servo_id), voltage=self.voltage, temperature=self.temperature)


class ProtocolTests(unittest.TestCase):
    def test_ping_packet(self):
        self.assertEqual(packet(1, 1), bytes.fromhex('FF FF 01 02 01 FB'))

    def test_fragmented_noisy_corrupt_and_wrong_id_frames(self):
        bad = bytearray(status(1, b'\x00\x08'))
        bad[-1] ^= 1
        serial = SerialFake(b'noise' + bad + status(2, b'\x00\x08') + status(1, b'\x00\x08'))
        self.assertEqual(Bus(serial, 0.03).read(1, 56, 2), b'\x00\x08')

    def test_echo_is_not_ack(self):
        serial = SerialFake(packet(1, 1) + status(1))
        Bus(serial, 0.02).ping(1)

    def test_timeout_and_bad_checksum(self):
        for response in (b'', b'\xff\xff\x01\x02\x00\x00'):
            with self.assertRaises(BusTimeout):
                Bus(SerialFake(response), 0.005).ping(1)

    def test_wrong_payload_length_not_accepted(self):
        with self.assertRaises(BusTimeout):
            Bus(SerialFake(status(1, b'\x01')), 0.005).read(1, 56, 2)

    def test_motor_errors_are_not_silent(self):
        with self.assertRaisesRegex(BusError, '0x04'):
            Bus(SerialFake(status(1, error=4)), 0.02).ping(1)

    def test_broadcast_stop_no_ack(self):
        serial = SerialFake(b'')
        Bus(serial).write(254, 40, [0])
        self.assertEqual(serial.written, [packet(254, 3, b'\x28\x00')])

    def test_feedback_signed_values_and_voltage(self):
        data = bytearray(15)
        data[:2] = (2048).to_bytes(2, 'little')
        data[2:4] = (0x8064).to_bytes(2, 'little')
        data[6:8] = bytes([120, 31])
        data[10] = 1
        data[13:15] = (0x8003).to_bytes(2, 'little')
        result = Bus(SerialFake(status(1, bytes(data))), 0.02).feedback(1)
        self.assertEqual((result.degrees, result.speed, result.voltage, result.temperature, result.current_raw, result.moving), (180, -100, 12, 31, -3, True))

    def test_goal_layout_and_bounds(self):
        serial = SerialFake(status(1))
        bus = Bus(serial, 0.02)
        bus.goal(1, 2048, 171)
        self.assertEqual(serial.written[0], packet(1, 3, bytes([41, 10, 0, 8, 0, 0, 171, 0])))
        for pos, speed in ((-1, 171), (4096, 171), (2048, -1), (2048, 3401)):
            with self.assertRaises(ValueError):
                bus.goal(1, pos, speed)

    def test_maximum_profile_packet_contains_zero_speed_and_acceleration(self):
        serial = SerialFake(status(1))
        Bus(serial, 0.02).goal(1, 3072, 0, acceleration=0)
        self.assertEqual(serial.written, [packet(1, 3, bytes([41, 0, 0, 12, 0, 0, 0, 0]))])

    def test_acceleration_bounds(self):
        bus = Bus(SerialFake(status(1)), 0.02)
        for acceleration in (-1, 151):
            with self.assertRaises(ValueError):
                bus.goal(1, 2048, 171, acceleration)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.bus = RecordingBus()
        self.controller = Controller(self.bus)
        self.controller.inspect(1)

    def test_inspect_never_writes(self):
        self.assertEqual(self.bus.history, [])

    def test_unarmed_motion_refused(self):
        with self.assertRaises(BusError):
            self.controller.move(2048, 15)
        self.assertEqual(self.bus.history, [])

    def test_requires_single_unmounted_confirmation(self):
        with self.assertRaises(BusError):
            self.controller.arm(False)
        self.assertEqual(self.bus.history, [])

    def test_arm_preloads_current_before_torque_enable(self):
        self.bus.position = 1234
        self.controller.arm(True)
        self.assertEqual(self.bus.history, [('write', 1, 40, [0]), ('goal', 1, 1234, 171), ('write', 1, 40, [1])])
        self.assertEqual(self.controller.origin, 1234)

    def test_wheel_mode_refused_without_reconfiguring(self):
        self.bus.mode = 1
        with self.assertRaises(BusError):
            self.controller.arm(True)
        self.assertEqual(self.bus.history, [])

    def test_bad_voltage_temperature_position_refused(self):
        for attr, value in [('voltage', 8.5), ('voltage', 13), ('temperature', 60), ('position', -1)]:
            with self.subTest(attr=attr, value=value):
                bus = RecordingBus()
                setattr(bus, attr, value)
                controller = Controller(bus)
                controller.inspect(1)
                with self.assertRaises(BusError):
                    controller.arm(True)
                self.assertFalse(controller.armed)
                self.assertNotIn(('write', 1, 40, [1]), bus.history)

    def test_preload_mismatch_prevents_enable(self):
        self.bus.corrupt_goal = True
        with self.assertRaises(BusError):
            self.controller.arm(True)
        self.assertNotIn(('write', 1, 40, [1]), self.bus.history)

    def test_cancel_prevents_enable(self):
        self.controller.cancelled = lambda: True
        with self.assertRaises(BusError):
            self.controller.arm(True)
        self.assertNotIn(('write', 1, 40, [1]), self.bus.history)

    def test_window_and_speed_limits(self):
        self.controller.arm(True)
        self.controller.move(2105, 15)
        self.assertEqual(self.bus.history[-1], ('goal', 1, 2105, 171))
        with self.assertRaises(BusError):
            self.controller.move(3000, 15)
        with self.assertRaises(ValueError):
            self.controller.move(2048, 360)

    def test_window_clamps_encoder_edge(self):
        self.bus.position = 12
        self.controller.arm(True)
        self.assertEqual(self.controller.limits[0], 0)

    def test_270_degree_window_contains_present_position_at_edges(self):
        for position in (0, 12, 2048, 3235, 4095):
            bus = RecordingBus()
            bus.position = position
            controller = Controller(bus)
            controller.inspect(1)
            controller.arm(True, 270)
            low, high = controller.limits
            self.assertEqual(high - low, 3072)
            self.assertTrue(0 <= low <= position <= high <= 4095)
            self.assertEqual(bus.history[1], ('goal', 1, position, 171))

    def test_maximum_profile_removes_both_speed_and_acceleration_limits(self):
        self.controller.arm(True, 270)
        self.controller.move(3072, 'Maksimum')
        self.assertEqual(self.bus.goal_profiles[-1], (3072, 0, 0))

    def test_selecting_numeric_speed_restores_soft_acceleration(self):
        self.controller.arm(True, 270)
        self.controller.move(3072, 'Maksimum')
        self.controller.move(2048, 60)
        self.assertEqual(self.bus.goal_profiles[-1], (2048, 683, 10))

    def test_arming_still_preloads_current_position_with_soft_profile(self):
        self.bus.position = 3235
        self.controller.arm(True, 270)
        self.assertEqual(self.bus.goal_profiles, [(3235, 171, 10)])

    def test_invalid_travel_does_not_write(self):
        with self.assertRaises(ValueError):
            self.controller.arm(True, 360)
        self.assertEqual(self.bus.history, [])

    def test_cannot_select_another_motor_while_armed(self):
        self.controller.arm(True)
        with self.assertRaises(BusError):
            self.controller.inspect(2)

    def test_stop_disarms(self):
        self.controller.arm(True)
        self.controller.stop()
        self.assertFalse(self.controller.armed)
        self.assertEqual(self.bus.history[-1], ('write', 254, 40, [0]))

    def test_id_change_verified_and_locked(self):
        self.controller.change_id(4, True)
        self.assertEqual(self.controller.servo_id, 4)
        self.assertEqual(self.bus.motor_id, 4)
        self.assertEqual(self.bus.lock, 1)
        self.assertFalse(self.controller.armed)

    def test_id_invalid_or_unconfirmed_refused(self):
        for value in (0, 254, 256):
            with self.assertRaises(ValueError):
                self.controller.change_id(value, True)
        with self.assertRaises(BusError):
            self.controller.change_id(2, False)
        self.assertEqual(self.bus.history, [])

    def test_conflicting_id_refused(self):
        self.bus.ping = lambda servo_id: None
        with self.assertRaisesRegex(BusError, 'kullanımda'):
            self.controller.change_id(2, True)
        self.assertEqual(self.bus.motor_id, 1)


class WorkerTests(unittest.TestCase):
    def test_failed_read_does_not_change_torque(self):
        worker = Worker(demo=True)
        bus = RecordingBus()
        worker.controller = Controller(bus)
        worker.submit('inspect', 9)
        worker.start()
        deadline = time.monotonic() + 1
        seen_error = False
        while time.monotonic() < deadline:
            kind, value = worker.events.get(timeout=1)
            if kind == 'error':
                seen_error = True
                break
        # Snapshot before explicit application shutdown (shutdown releases torque).
        history = list(bus.history)
        worker.shutdown.set()
        worker.join(1)
        self.assertTrue(seen_error)
        self.assertEqual(history, [])

    def test_stop_clears_queued_arm_and_motion(self):
        worker = Worker(demo=True)
        bus = RecordingBus()
        worker.controller = Controller(bus)
        worker.controller.inspect(1)
        worker.submit('arm', True)
        worker.move(2200, 15)
        worker.request_stop()
        worker.start()
        deadline = time.monotonic() + 1
        while not bus.history and time.monotonic() < deadline:
            time.sleep(0.01)
        worker.shutdown.set()
        worker.join(1)
        self.assertTrue(bus.history)
        self.assertTrue(all(item == ('write', 254, 40, [0]) for item in bus.history))

    def test_motion_coalesces(self):
        worker = Worker(demo=True)
        worker.move(2100, 15)
        worker.move(2200, 30)
        self.assertEqual(worker.pending_move[:2], (2200, 30))

    def test_demo_connect_has_no_writes_and_no_auto_selection(self):
        worker = Worker(demo=True)
        worker.execute('connect', ('DEMO', 1000000))
        self.assertIsNone(worker.controller.servo_id)
        self.assertFalse(worker.controller.armed)
        self.assertEqual(worker.controller.bus.torque, 0)


if __name__ == '__main__':
    unittest.main()
