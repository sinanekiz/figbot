"""UNO-only STK500v1 upload with paced USB writes and full readback verification.

Use only with motor power disconnected and the mechanism supported. Programs
application flash only, never fuses, EEPROM or bootloader. No motion commands.
Protocol reference: Optiboot optiboot.c STK_LOAD_ADDRESS/PROG_PAGE/READ_PAGE.
"""
import argparse
import hashlib
from pathlib import Path
import time

PAGE = 128
APPLICATION_END = 0x7E00


def read_hex(path):
    memory = {}
    ended = False
    for line in Path(path).read_text(encoding='ascii').splitlines():
        if not line:
            continue
        if ended or not line.startswith(':'):
            raise ValueError('Invalid Intel HEX record')
        record = bytes.fromhex(line[1:])
        if len(record) < 5 or len(record) != record[0] + 5 or sum(record) & 255:
            raise ValueError('Invalid HEX length/checksum')
        address = int.from_bytes(record[1:3], 'big')
        kind = record[3]
        if kind == 1 and record[0] == 0:
            ended = True
        elif kind == 0:
            for offset, value in enumerate(record[4:-1]):
                at = address + offset
                if at >= APPLICATION_END or at in memory:
                    raise ValueError('Overlapping record or bootloader write')
                memory[at] = value
        else:
            raise ValueError('Only UNO data/EOF records supported')
    if not ended or not memory or set(memory) != set(range(max(memory) + 1)):
        raise ValueError('Expected contiguous application image from address zero')
    return bytes(memory[i] for i in range(len(memory)))


class Programmer:
    def __init__(self, link, sleep=time.sleep):
        self.link, self.sleep = link, sleep

    def command(self, payload, size=0):
        packet = payload + b'\x20'
        # Small USB transfers avoid the large transmit burst; baud stays 115200.
        for offset in range(0, len(packet), 16):
            piece = packet[offset:offset + 16]
            if self.link.write(piece) != len(piece):
                raise IOError('Short serial write')
            self.link.flush()
            self.sleep(.004)
        response = bytearray()
        while len(response) < size + 2:
            part = self.link.read(size + 2 - len(response))
            if not part:
                raise IOError('Bootloader response timeout')
            response.extend(part)
        if response[0] != 0x14 or response[-1] != 0x10:
            raise IOError('Invalid STK500 response framing')
        return bytes(response[1:-1])

    def address(self, address):
        if address % PAGE or not 0 <= address < APPLICATION_END:
            raise ValueError('Application page alignment/bounds')
        self.command(b'\x55' + (address // 2).to_bytes(2, 'little'))

    def read_page(self, address):
        self.address(address)
        return self.command(b'\x74\x00\x80F', PAGE)

    def upload(self, image, progress=lambda message: None):
        if not image or len(image) > APPLICATION_END:
            raise ValueError('Invalid application size')
        if self.command(b'\x75', 3) != b'\x1e\x95\x0f':
            raise IOError('Not the expected ATmega328P; refusing write')
        self.command(b'\x50')
        padded = image + b'\xff' * (-len(image) % PAGE)
        for address in range(0, len(padded), PAGE):
            page = padded[address:address + PAGE]
            self.address(address)
            self.command(b'\x64\x00\x80F' + page)
            if self.read_page(address) != page:
                raise IOError(f'Page verification failed at {address:#x}; keep motor power off')
            if address % 1024 == 0:
                progress(f'Verified page at {address:#06x}')
        readback = b''.join(self.read_page(a) for a in range(0, len(padded), PAGE))
        if readback != padded:
            raise IOError('Complete readback mismatch; keep motor power off')
        self.command(b'\x51')
        return readback[:len(image)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--hex', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--motor-power-disconnected', action='store_true', required=True)
    args = parser.parse_args()
    if hashlib.sha256(args.hex.read_bytes()).hexdigest() != args.expected_sha256:
        raise ValueError('Release artifact checksum mismatch')
    image = read_hex(args.hex)
    import serial
    with serial.Serial(args.port, 115200, timeout=1, write_timeout=1) as link:
        link.dtr = False
        time.sleep(.15)
        link.reset_input_buffer()
        link.dtr = True
        time.sleep(.15)
        programmer = Programmer(link)
        for attempt in range(3):
            try:
                programmer.command(b'\x30')
                break
            except IOError:
                if attempt == 2:
                    raise
                link.reset_input_buffer()
        verified = programmer.upload(image, lambda s: print(s, flush=True))
    print(f'VERIFIED {len(verified)} application bytes; SHA256 {hashlib.sha256(verified).hexdigest()}')


if __name__ == '__main__':
    main()
