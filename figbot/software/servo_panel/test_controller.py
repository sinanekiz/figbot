import pytest

from software.servo_panel.controller import ServoController

BANNER = b"FIGBOT_SERVO_CHECK_V5 Pangle,speed c l r t x\n"


class FakeLink:
    def __init__(self, **kwargs):
        self.input = BANNER
        self.written = []
        self.closed = False

    @property
    def in_waiting(self):
        return len(self.input)

    def read(self, count):
        chunk, self.input = self.input[:count], self.input[count:]
        return chunk

    def write(self, data):
        self.written.append(data)

    def flush(self):
        pass

    def close(self):
        self.closed = True


def make_controller():
    controller = ServoController(factory=FakeLink, sleep=lambda _: None)
    controller.connect("COM_TEST")
    return controller


def test_connect_has_no_motion_but_explicit_position_rearms():
    controller = make_controller()
    assert controller.ready and not controller.active
    assert controller.link.written == []
    controller.send("l")
    assert not controller.active
    controller.handle_line("Small movement requested")
    assert controller.active
    controller.handle_line("Signal disabled")
    controller.send("c")
    assert not controller.active
    controller.handle_line("Centre: 1500us (actual angle unverified)")
    controller.send("l")
    assert controller.link.written == [b"l", b"c", b"l"]


def test_invalid_commands_never_reach_serial():
    controller = make_controller()
    for command in ("0", "180", "cc", "c\nl", "", "tt"):
        with pytest.raises(ValueError):
            controller.send(command)
    assert controller.link.written == []


def test_timeout_and_reset_show_signal_off():
    controller = make_controller()
    controller.handle_line("Centre: 1500us")
    controller.handle_line("Timeout: signal disabled")
    assert not controller.active
    controller.send("r")
    controller.handle_line("Small movement requested")
    assert controller.active
    controller.handle_line("Centre: 1500us")
    controller.handle_line(BANNER.decode().strip())
    assert not controller.active


def test_close_sends_disable_and_closes_port():
    controller = make_controller()
    link = controller.link
    controller.disconnect()
    assert link.written == [b"x"] and link.closed
    assert not controller.ready and controller.link is None


def test_fast_test_explicitly_rearms_and_end_disarms():
    controller = make_controller()
    controller.send("t")
    assert not controller.fast_running
    controller.handle_line("Fast test started: 3 cycles, 1000-2000us, angle unverified")
    assert controller.fast_running
    before = list(controller.link.written)
    controller.send("r")
    assert controller.link.written == before
    controller.handle_line("Fast test finished: signal disabled")
    assert not controller.fast_running and not controller.active


def test_logging_persists_card_acknowledgements(tmp_path):
    target = tmp_path / "serial.log"
    controller = ServoController(log_path=target)
    controller.handle_line(BANNER.decode().strip())
    controller.handle_line("Small movement requested")
    assert "Kart onayı" in target.read_text(encoding="utf-8")


def test_position_and_speed_validation_and_ack():
    controller = make_controller()
    for angle, speed in [(-1, 90), (181, 90), (90, 1), (90, 361), (90.5, 90), (True, 90), (90, "0")]:
        with pytest.raises(ValueError):
            controller.set_position(angle, speed)
    assert controller.link.written == []
    controller.set_position(120, 60)
    assert controller.link.written == [b"P120,60\n"]
    assert controller.target_angle is None
    controller.handle_line("Position: 120,60")
    assert controller.target_angle == 120 and controller.target_speed == 60 and controller.active
    controller.handle_line("Position: 999,60")
    assert controller.target_angle == 120


def test_previous_direction_firmware_not_accepted():
    controller = ServoController(factory=FakeLink)
    controller.handle_line("UNLOADED SERVO: c=enable/centre, l=1400us, r=1600us, x=disable")
    assert not controller.ready


def test_fragmented_ack():
    controller = make_controller()
    controller.link.input = b"Centre: 150"
    controller.poll()
    assert not controller.active
    controller.link.input = b"0us\r\n"
    controller.poll()
    assert controller.active


def test_unrecognized_firmware_never_receives_commands():
    tick = [0]
    def advance(_):
        tick[0] += 1
    link = FakeLink()
    link.input = b"Some other device\n"
    controller = ServoController(factory=lambda **_: link, clock=lambda: tick[0], sleep=advance)
    with pytest.raises(RuntimeError):
        controller.connect("COM_TEST")
    assert link.written == [] and link.closed
