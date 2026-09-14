from __future__ import annotations

import struct

import pytest

from fnr3_re.apt_const import AptConstFormatError, parse_apt_const

_SIGNATURE = b"Apt constant file\x1a\x00\x00"


def _const_bytes(names: list[str], *, field_a: int = 100) -> bytes:
    header_len = len(_SIGNATURE) + 12
    entry_table_size = len(names) * 8
    pool_start = header_len + entry_table_size

    pool = b""
    offsets = []
    for name in names:
        offsets.append(pool_start + len(pool))
        pool += name.encode("latin1") + b"\x00"

    entries = b"".join(struct.pack("<II", 1, off) for off in offsets)
    header = _SIGNATURE + struct.pack("<III", field_a, len(names), header_len)
    return header + entries + pool


def test_parses_synthetic_constant_pool() -> None:
    names = ["totalSliders", "GetSelectBoxerInfo", "iStamina", ""]

    parsed = parse_apt_const(_const_bytes(names, field_a=1184))

    assert parsed.field_a == 1184
    assert parsed.entry_count == 4
    assert parsed.header_len == len(_SIGNATURE) + 12
    assert parsed.names == tuple(names)


def test_rejects_missing_signature() -> None:
    with pytest.raises(AptConstFormatError, match="missing 'Apt constant file'"):
        parse_apt_const(b"not an apt const file" + b"\x00" * 32)


def test_rejects_truncated_entry_table() -> None:
    data = _const_bytes(["a", "b", "c"])
    header_len = len(_SIGNATURE) + 12
    truncated = data[:header_len]  # header claims 3 entries but none are present

    with pytest.raises(AptConstFormatError, match="truncated"):
        parse_apt_const(truncated)


def test_rejects_string_offset_out_of_range() -> None:
    data = bytearray(_const_bytes(["a"]))
    header_len = len(_SIGNATURE) + 12
    # Corrupt the single entry's string offset to point past the file.
    struct.pack_into("<II", data, header_len, 1, len(data) + 100)

    with pytest.raises(AptConstFormatError, match="out of range"):
        parse_apt_const(bytes(data))
