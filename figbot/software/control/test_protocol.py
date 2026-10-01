import pytest

from software.control.protocol import Frame, ProtocolError, decode_frame, encode_frame


def test_round_trip():
    frame = Frame("MOVE", 42, ("10", "-20", "30", "0", "8000", "12000"))
    assert decode_frame(encode_frame(frame)) == frame


def test_crc_rejects_mutation():
    wire = bytearray(encode_frame(Frame("ARM", 1)))
    wire[0] = ord("X")
    with pytest.raises(ProtocolError, match="CRC mismatch"):
        decode_frame(wire)


def test_reserved_character_is_rejected():
    with pytest.raises(ProtocolError):
        encode_frame(Frame("MOVE", 1, ("bad,field",)))
