import pytest
from tools.uno_paced_upload import Programmer, read_hex, APPLICATION_END


class Bootloader:
    def __init__(self, corrupt=False, signature=b'\x1e\x95\x0f'):
        self.memory = bytearray(b'\xff' * 32768)
        self.incoming = bytearray()
        self.reply = bytearray()
        self.address = 0
        self.corrupt = corrupt
        self.signature = signature
        self.writes = []

    def write(self, data):
        assert len(data) <= 16
        self.incoming.extend(data)
        n = 133 if self.incoming[0] == 0x64 else {0x55:4, 0x74:5}.get(self.incoming[0], 2)
        if len(self.incoming) == n:
            packet = bytes(self.incoming)
            assert packet[-1] == 0x20
            self.incoming.clear()
            cmd = packet[0]
            response = b''
            if cmd == 0x75:
                response = self.signature
            elif cmd == 0x55:
                self.address = 2 * int.from_bytes(packet[1:3], 'little')
            elif cmd == 0x64:
                assert packet[1:4] == b'\x00\x80F'
                self.memory[self.address:self.address+128] = packet[4:-1]
                self.writes.append(self.address)
                if self.corrupt:
                    self.memory[self.address] ^= 1
            elif cmd == 0x74:
                assert packet[1:4] == b'\x00\x80F'
                response = self.memory[self.address:self.address+128]
            else:
                assert cmd in (0x30, 0x50, 0x51)
            self.reply.extend(b'\x14' + response + b'\x10')
        return len(data)

    def flush(self): pass

    def read(self, size):
        # Exercise fragmented replies too.
        size = min(size, 9)
        value = bytes(self.reply[:size])
        del self.reply[:size]
        return value


def test_paced_upload_programs_exact_image_without_touching_bootloader():
    link = Bootloader()
    image = bytes(range(256)) + b'\x20\x14\x10\x64'
    assert Programmer(link, sleep=lambda _: None).upload(image) == image
    assert link.writes == [0, 128, 256]
    assert link.memory[384:] == b'\xff' * (32768-384)


def test_corrupt_flash_or_wrong_chip_never_claim_success():
    for link in (Bootloader(corrupt=True), Bootloader(signature=b'\x00\x00\x00')):
        with pytest.raises(IOError):
            Programmer(link, sleep=lambda _: None).upload(b'abcd')
        assert len(link.writes) <= 1


def test_hex_and_address_guards(tmp_path):
    p = tmp_path/'bad.hex'
    p.write_text(':0100000001FF\n:00000001FF\n')
    with pytest.raises(ValueError): read_hex(p)
    p.write_text(':0100000001FE\n:00000001FF\n')
    assert read_hex(p) == b'\x01'
    programmer = Programmer(Bootloader(), sleep=lambda _: None)
    for address in (-128, 1, APPLICATION_END):
        with pytest.raises(ValueError): programmer.address(address)
    with pytest.raises(ValueError): programmer.upload(b'\xff'*(APPLICATION_END+1))
