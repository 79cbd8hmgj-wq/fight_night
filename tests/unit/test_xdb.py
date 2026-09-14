from __future__ import annotations

import struct

import pytest

from fnr3_re.xdb import XdbFormatError, parse_xdb_header


def _header_bytes(
    *,
    word0: int = 121,
    word1: int = 37,
    section_size_a: int = 9012,
    section_size_b: int = 9012,
    section_size_c: int = 9012,
    word5: int = 0,
    word6: int = 0,
    word7: int = 0,
    total_size: int = 9704,
) -> bytes:
    header = struct.pack(
        "<8I",
        word0,
        word1,
        section_size_a,
        section_size_b,
        section_size_c,
        word5,
        word6,
        word7,
    )
    return header + bytes(total_size - len(header))


def test_parses_observed_xdbboxr_header_shape() -> None:
    header = parse_xdb_header(_header_bytes())

    assert header.word0 == 121
    assert header.word1 == 37
    assert header.section_size_a == header.section_size_b == header.section_size_c == 9012
    assert header.section_sizes_agree
    assert header.payload_size == 9704
    assert header.trailing_bytes == 692


def test_detects_disagreeing_section_sizes_like_xdbtrain() -> None:
    header = parse_xdb_header(
        _header_bytes(
            section_size_a=5288, section_size_b=7200, section_size_c=7200, total_size=8032
        )
    )

    assert not header.section_sizes_agree
    assert header.trailing_bytes == 832


def test_rejects_payload_smaller_than_the_proven_header() -> None:
    with pytest.raises(XdbFormatError, match="smaller than the proven header"):
        parse_xdb_header(b"\x00" * 16)


def test_rejects_section_size_larger_than_payload() -> None:
    with pytest.raises(XdbFormatError, match="larger than the payload"):
        parse_xdb_header(_header_bytes(section_size_c=99999, total_size=9704))
