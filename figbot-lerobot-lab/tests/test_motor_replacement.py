import pytest
from figbot_lab._reference_protocol import Bus, BusError, BusTimeout, Feedback
from figbot_lab.motor_replacement import ReplacementBus, replace_wrist_id


class ReplacementFixture:
    def __init__(self, *, occupied=False, uncertain=False):
        self.registers = bytearray(40); self.registers[3:5] = (777).to_bytes(2, 'little'); self.registers[5] = 6
        self.id, self.lock, self.torque = 6, 1, 1
        self.occupied, self.uncertain = occupied, uncertain
        self.writes = []
    def read(self, motor, address, size):
        if motor == 4 and self.occupied: return bytes(self.registers)
        if motor != self.id: raise BusTimeout('fixture absent ID')
        if address == 0: return bytes(self.registers)
        return bytes([{5: self.id, 40: self.torque, 55: self.lock}[address]])
    def feedback_state(self, motor):
        if motor != self.id: raise BusTimeout('fixture absent ID')
        return Feedback(1234, 0, 12.2, 30, 0, False), self.torque
    def write_once(self, motor, address, value):
        assert motor == self.id
        self.writes.append((motor, address, value))
        if address == 40: self.torque = value
        elif address == 55: self.lock = value
        elif address == 5:
            self.id = value; self.registers[5] = value
            if self.uncertain: raise BusTimeout('new ID acknowledgment unavailable')
        else: raise AssertionError('unexpected register')


@pytest.mark.parametrize('uncertain', [False, True])
def test_single_id_change_verifies_new_id_relocks_and_preserves_other_rom(uncertain):
    bus, report = ReplacementFixture(uncertain=uncertain), {}
    before = bytes(bus.registers)
    replace_wrist_id(bus, report)
    assert bus.id == 4 and bus.torque == 0 and bus.lock == 1
    assert bus.writes == [(6, 40, 0), (6, 55, 0), (6, 5, 4), (4, 55, 1)]
    assert bytes(bus.registers[:5] + bus.registers[6:]) == before[:5] + before[6:]
    assert report['status'] == 'VERIFIED_ID_6_TO_4' and not report['motion_commands_sent']


def test_occupied_destination_prevents_every_write():
    bus = ReplacementFixture(occupied=True)
    with pytest.raises(ValueError, match='already replies'): replace_wrist_id(bus, {})
    assert bus.writes == []


def test_absent_source_prevents_every_write():
    bus = ReplacementFixture(); bus.id = 1
    with pytest.raises(BusTimeout): replace_wrist_id(bus, {})
    assert bus.writes == []


def test_packet_guard_rejects_goal_other_ids_and_unapproved_or_repeated_writes(monkeypatch):
    sent = []
    monkeypatch.setattr(Bus, 'transact', lambda self, *args: sent.append(args) or b'')
    bus = ReplacementBus(object())
    for motor, instruction, data in [(254, 2, b'\5\1'), (1, 3, b'\5\4'), (6, 3, b'\x29\1'), (6, 6, b''), (6, 3, b'\5\4')]:
        with pytest.raises(BusError): bus.transact(motor, instruction, data)
    assert not sent
    bus.write_once(6, 5, 4)
    with pytest.raises(BusError): bus.write_once(6, 5, 4)
    assert len(sent) == 1
