"""Explicit user-authorized replacement: ID6 becomes ID4, without motion.

Feetech SDK register map: ID5, volatile torque40, EEPROM lock55.
https://github.com/ftservo/FTServo_Python/blob/main/scservo_sdk/sms_sts.py
Calibration's separate READ-only packet guard is unchanged.
"""
from dataclasses import asdict

from ._reference_protocol import Bus, BusError, BusTimeout


class ReplacementBus(Bus):
    """Only READ and a single, phase-authorized 6-to-4 replacement transaction."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_write = None
        self.used_writes = set()

    def transact(self, servo_id, instruction, data=b'', response_size=None):
        if type(servo_id) is not int or servo_id not in range(1, 7):
            raise BusError('Replacement rejects broadcast and non-arm IDs.')
        if instruction == 2:
            if len(data) != 2 or not 0 <= data[0] <= 70 or not 1 <= data[1] <= 40 or data[0] + data[1] > 71:
                raise BusError('Invalid replacement READ range.')
        elif instruction == 3:
            command = (servo_id, bytes(data))
            permitted = {(6, b'\x28\x00'), (6, b'\x37\x00'), (6, b'\x05\x04'),
                         (4, b'\x37\x00'), (4, b'\x37\x01'), (6, b'\x37\x01')}
            if command != self.allowed_write or command not in permitted or command in self.used_writes:
                raise BusError('Only the single authorized replacement write is permitted.')
            self.used_writes.add(command)  # an uncertain acknowledgment never permits a replay
            self.allowed_write = None
        else:
            raise BusError('Replacement rejects ping/action/reset/sync and other instructions.')
        return super().transact(servo_id, instruction, data, response_size)

    def write_once(self, motor, address, value):
        self.allowed_write = (motor, bytes([address, value]))
        try:
            self.write(motor, address, bytes([value]))
        finally:
            self.allowed_write = None

    def sync_goal(self, profiles):
        raise BusError('Replacement never sends movement.')

    def sync_positions(self, positions):
        raise BusError('Replacement never sends movement.')


def replace_wrist_id(bus, report):
    """Require a replying ID6 and empty ID4; never guess or repeat an ID write."""
    report.update(status='READ_PREFLIGHT', source_id=6, destination_id=4, writes=[])
    before = bus.read(6, 0, 40)
    report['source_registers_before'] = before.hex()
    if before[5] != 6 or int.from_bytes(before[3:5], 'little') != 777 or before[33] != 0:
        raise ValueError('ID6 model/ID/position-mode readback differs; no ID write.')
    for _ in range(2):
        try:
            bus.read(4, 0, 40)
        except BusTimeout:
            continue
        raise ValueError('ID4 already replies; do not create duplicate motor IDs.')
    feedback, torque = bus.feedback_state(6)
    report['source_feedback'] = {**asdict(feedback), 'torque': torque}
    if feedback.moving or abs(feedback.speed) > 5:
        raise ValueError('ID6 must be stationary before changing its ID.')
    original_lock = bus.read(6, 55, 1)[0]
    if original_lock not in (0, 1):
        raise ValueError('EEPROM lock state is unknown.')
    report['original_lock'] = original_lock

    def write_once(motor, address, value):
        item = {'motor': motor, 'address': address, 'value': value}
        report['writes'].append(item)
        try:
            bus.write_once(motor, address, value)
            item['acknowledged'] = True
        except BusTimeout as exc:
            item.update(acknowledged=False, error=str(exc))
            # ID-change acknowledgment may carry the new ID. Confirm by READ.

    if torque:
        write_once(6, 40, 0)
    if bus.read(6, 40, 1) != b'\0':
        raise BusError('ID6 torque release was not confirmed; no EEPROM write.')
    if feedback.temperature > 45:
        raise ValueError('Replacement motor must cool to45C or below; torque remains off.')
    report['status'] = 'REPLACEMENT_STARTED'
    relock_id = 6
    unlocked = False
    try:
        if original_lock == 1:
            unlocked = True  # even an unanswered unlock may have reached the servo
            write_once(6, 55, 0)
            if bus.read(6, 55, 1) != b'\0':
                raise BusError('EEPROM unlock not verified.')
        write_once(6, 5, 4)
        relock_id = None
        try:
            after = bus.read(4, 0, 40)
            relock_id = 4
        except BusTimeout:
            # Determine where the motor still lives before restoring its lock.
            if bus.read(6, 5, 1) == b'\6':
                relock_id = 6
            raise
        expected = bytearray(before); expected[5] = 4
        if after != bytes(expected):
            raise BusError('Registers other than ID changed; replacement unverified.')
        report['destination_registers_after'] = after.hex()
    finally:
        if unlocked and relock_id is not None:
            write_once(relock_id, 55, original_lock)
            if bus.read(relock_id, 55, 1) != bytes([original_lock]):
                raise BusError('EEPROM relock was not verified.')
        elif unlocked:
            report['lock_restore_unconfirmed'] = True
    try:
        bus.read(6, 5, 1)
    except BusTimeout:
        pass
    else:
        raise BusError('Old ID6 still replies; replacement not verified.')
    feedback, torque = bus.feedback_state(4)
    if torque != 0:
        raise BusError('Replacement completed but torque-off readback differs.')
    report.update(status='VERIFIED_ID_6_TO_4', destination_feedback={**asdict(feedback), 'torque': torque},
                  motion_commands_sent=False, old_home_valid=False)
    return report


def main():
    import argparse
    import serial
    from .common import ROOT, new_run, save_json, load_json
    parser = argparse.ArgumentParser(description='User-authorized wrist replacement, ID6 -> ID4.')
    parser.add_argument('--port', required=True)
    args = parser.parse_args()
    run, report = new_run('wrist_id_replacement'), {}
    try:
        with serial.Serial(args.port, 1000000, timeout=.02, write_timeout=.2) as connection:
            replace_wrist_id(ReplacementBus(connection), report)
        hardware_path = ROOT / 'configs/virtual_leader.hardware.json'
        hardware = load_json(hardware_path)
        hardware['replacement'] = {'source_id': 6, 'destination_id': 4,
                                   'status': report['status'], 'evidence': str(run / 'replacement.json')}
        save_json(hardware_path, hardware)
    except Exception as exc:
        report.update(status='FAILED_OR_UNCONFIRMED', error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        save_json(run / 'replacement.json', report)
        print(run)


if __name__ == '__main__':
    main()
