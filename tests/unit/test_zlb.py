from __future__ import annotations

import struct
import zlib

import pytest

from fnr3_re.zlb import ZlbError, compress_zlb, decompress_zlb, is_zlb


def _zlb_bytes(payload: bytes, *, declared_size: int | None = None) -> bytes:
    size = len(payload) if declared_size is None else declared_size
    return struct.pack("<I", size) + zlib.compress(payload, 9)


def test_decodes_observed_beload_zlb_shape() -> None:
    payload = b"Fight Night Round 3 boot-load screen data" * 50
    encoded = _zlb_bytes(payload)

    assert is_zlb(encoded)
    assert decompress_zlb(encoded) == payload


def test_round_trip_via_this_codecs_own_encoder() -> None:
    payload = bytes(range(256)) * 17

    encoded = compress_zlb(payload)

    assert decompress_zlb(encoded) == payload


def test_rejects_declared_size_exceeding_limit() -> None:
    encoded = _zlb_bytes(b"small payload")

    with pytest.raises(ZlbError, match="exceeds limit"):
        decompress_zlb(encoded, max_output_size=1)


def test_rejects_size_mismatch() -> None:
    encoded = _zlb_bytes(b"payload", declared_size=999)

    with pytest.raises(ZlbError, match="size mismatch"):
        decompress_zlb(encoded)


def test_rejects_truncated_header() -> None:
    with pytest.raises(ZlbError, match="truncated"):
        decompress_zlb(b"\x01\x02")


def test_rejects_malformed_zlib_stream() -> None:
    encoded = struct.pack("<I", 10) + b"not a zlib stream"

    with pytest.raises(ZlbError, match="malformed zlib stream"):
        decompress_zlb(encoded)


def test_is_zlb_rejects_arbitrary_bytes() -> None:
    assert not is_zlb(b"BIGF" + b"\x00" * 20)
    assert not is_zlb(b"\x00\x00\x00\x00")
