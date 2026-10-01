"""CRC-protected ASCII protocol shared by Pi 5 and Pico 2.

Wire format: ``KIND,SEQ,FIELD...*CRC16\\n``. CRC is CCITT-FALSE over the
ASCII payload before ``*``. Human-readable frames keep first bring-up and
oscilloscope/terminal diagnosis practical.
"""

from __future__ import annotations

from dataclasses import dataclass


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class Frame:
    kind: str
    seq: int
    fields: tuple[str, ...] = ()


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def encode_frame(frame: Frame) -> bytes:
    kind = frame.kind.strip().upper()
    if not kind or any(ch in kind for ch in ",*\r\n"):
        raise ProtocolError("invalid frame kind")
    fields = tuple(str(field) for field in frame.fields)
    if any(any(ch in field for ch in ",*\r\n") for field in fields):
        raise ProtocolError("invalid field")
    payload = ",".join((kind, str(frame.seq), *fields)).encode("ascii")
    return payload + f"*{crc16_ccitt(payload):04X}\n".encode("ascii")


def decode_frame(raw: bytes | str) -> Frame:
    if isinstance(raw, str):
        raw = raw.encode("ascii")
    line = raw.strip()
    try:
        payload, checksum = line.rsplit(b"*", 1)
    except ValueError as exc:
        raise ProtocolError("missing checksum separator") from exc
    if len(checksum) != 4:
        raise ProtocolError("checksum must be four hexadecimal characters")
    try:
        received = int(checksum, 16)
    except ValueError as exc:
        raise ProtocolError("invalid checksum") from exc
    expected = crc16_ccitt(payload)
    if received != expected:
        raise ProtocolError(f"CRC mismatch: received {received:04X}; expected {expected:04X}")
    try:
        tokens = payload.decode("ascii").split(",")
        return Frame(tokens[0], int(tokens[1]), tuple(tokens[2:]))
    except (UnicodeError, ValueError, IndexError) as exc:
        raise ProtocolError("malformed payload") from exc
