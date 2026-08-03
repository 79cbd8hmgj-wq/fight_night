from __future__ import annotations

import pytest

from fnr3_re.refpack import RefPackError, compress_refpack, decompress_refpack, is_refpack


def stream(size: int, commands: bytes) -> bytes:
    return b"\x10\xfb" + size.to_bytes(3, "big") + commands


def test_detects_supported_reference_header() -> None:
    assert is_refpack(stream(0, b"\xfc"))
    assert not is_refpack(b"")
    assert not is_refpack(b"\x11\xfb\x00\x00\x00")


def test_decodes_literal_and_stop_commands() -> None:
    assert decompress_refpack(stream(0, b"\xfc")) == b""
    assert decompress_refpack(stream(3, b"\xffXYZ")) == b"XYZ"
    assert decompress_refpack(stream(4, b"\xe0ABCD\xfc")) == b"ABCD"


def test_decodes_short_medium_and_long_backreferences() -> None:
    short = stream(8, b"\xe0ABCD\x04\x03\xfc")
    medium = stream(8, b"\xe0ABCD\x80\x00\x03\xfc")
    long = stream(10, b"\xe0ABCD\xc1\x00\x04\x00E\xfc")

    assert decompress_refpack(short) == b"ABCDABCD"
    assert decompress_refpack(medium) == b"ABCDABCD"
    assert decompress_refpack(long) == b"ABCDEABCDE"


def test_decodes_overlapping_backreference() -> None:
    encoded = stream(6, b"\x09\x00A\xfc")

    assert decompress_refpack(encoded) == b"AAAAAA"


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"A",
        b"ABC",
        b"ABCD",
        bytes(range(256)),
        b"A" * 4096,
        (b"abc123" * 1000) + bytes(range(64)),
        bytes((index * 37) & 0xFF for index in range(8192)),
    ],
)
def test_deterministic_encoder_round_trips(payload: bytes) -> None:
    first = compress_refpack(payload)
    second = compress_refpack(payload)

    assert first == second
    assert first.startswith(b"\x10\xfb")
    assert decompress_refpack(first) == payload


def test_encoder_uses_backreferences_for_repetitive_data() -> None:
    payload = b"FIGHTNIGHT" * 1000

    encoded = compress_refpack(payload)

    assert len(encoded) < len(payload) // 4
    assert decompress_refpack(encoded) == payload


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"", "header is truncated"),
        (b"\x10\xfb\x00", "header is truncated"),
        (b"\x11\xfb\x00\x00\x00", "unsupported RefPack signature"),
        (stream(4, b"\xe0ABC"), "literal run is truncated"),
        (stream(4, b"\x00"), "short command is truncated"),
        (stream(4, b"\x80\x00"), "medium command is truncated"),
        (stream(5, b"\xc0\x00\x00"), "long command is truncated"),
        (stream(4, b"\x04\x03\xfc"), "backreference exceeds produced output"),
        (stream(5, b"\xe0ABCD\xfc"), "decompressed size mismatch"),
        (stream(4, b"\xe0ABCD\xfcTRAIL"), "trailing bytes after RefPack stream"),
    ],
)
def test_decoder_rejects_malformed_streams(payload: bytes, message: str) -> None:
    with pytest.raises(RefPackError, match=message):
        decompress_refpack(payload)


def test_decoder_enforces_output_bound() -> None:
    encoded = stream(1024, b"\xfc")

    with pytest.raises(RefPackError, match="declared output exceeds limit"):
        decompress_refpack(encoded, max_output_size=100)


def test_decoder_can_report_embedded_stream_consumption() -> None:
    encoded = stream(4, b"\xe0ABCD\xfc") + b"NEXT"

    decoded, consumed = decompress_refpack(encoded, allow_trailing=True, return_consumed=True)

    assert decoded == b"ABCD"
    assert consumed == len(encoded) - 4
