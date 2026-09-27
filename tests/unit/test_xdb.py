from __future__ import annotations

import struct

import pytest

from fnr3_re.xdb import (
    XdbFieldType,
    XdbFormatError,
    parse_xdb_header,
    xdb_field_type,
    xdb_inline_i16,
    xdb_record_field_descriptor_offset,
)


def _header_bytes(
    *,
    word0: int = 121,
    word1: int = 37,
    section_size_a: int = 9012,
    section_size_b: int = 9012,
    section_size_c: int = 9012,
    word5: int = 0,
    word6: int = 21,
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

    assert header.word0 == header.field_count == 121
    assert header.word1 == header.record_count == 37
    assert header.section_size_a == header.section_size_b == header.section_size_c == 9012
    assert header.section_sizes_agree
    assert header.payload_size == 9704
    assert header.trailing_bytes == 692
    assert header.field_type_bytes == 31
    assert header.record_descriptor_stride == 242
    assert header.record_descriptor_matrix_size == 8956
    assert header.record_descriptor_matrix_offset == 0x38


def test_detects_disagreeing_section_sizes_like_xdbtrain() -> None:
    header = parse_xdb_header(
        _header_bytes(
            word0=11,
            word1=239,
            section_size_a=5288,
            section_size_b=7200,
            section_size_c=7200,
            total_size=8032,
        )
    )

    assert not header.section_sizes_agree
    assert header.record_descriptor_matrix_offset == 0x1C
    assert header.trailing_bytes == 832


def test_rejects_payload_smaller_than_the_recovered_header() -> None:
    with pytest.raises(XdbFormatError, match="smaller than the recovered header"):
        parse_xdb_header(b"\x00" * 16)


def test_rejects_section_size_larger_than_payload() -> None:
    with pytest.raises(XdbFormatError, match="not monotonic/in-bounds"):
        parse_xdb_header(_header_bytes(section_size_c=99999, total_size=9704))


def test_field_type_and_descriptor_matrix_helpers() -> None:
    # Four fields with native type codes 0/1/2/3, two records.
    data = bytearray(
        _header_bytes(
            word0=4,
            word1=2,
            section_size_a=44,
            section_size_b=48,
            section_size_c=52,
            word6=0x1B000000,
            word7=0,
            total_size=64,
        )
    )
    # Header word6 is little-endian at +0x18, so put the packed type byte
    # directly where the native accessor reads it.
    data[0x18] = 0x1B
    struct.pack_into("<h", data, 0x1C, -123)

    assert [xdb_field_type(data, i) for i in range(4)] == [
        XdbFieldType.INLINE_I16,
        XdbFieldType.STRING,
        XdbFieldType.INT32,
        XdbFieldType.FLOAT32,
    ]
    assert xdb_record_field_descriptor_offset(data, 0, 0) == 0x1C
    assert xdb_record_field_descriptor_offset(data, 1, 3) == 0x2A
    assert xdb_inline_i16(data, 0, 0) == -123
