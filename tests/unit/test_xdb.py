from __future__ import annotations

import struct

import pytest

from fnr3_re.xdb import XdbFormatError, parse_xdb_header, xdb_field_type


def _xdb_bytes(
    *,
    field_count: int = 121,
    record_count: int = 37,
    float_pool_offset: int = 9012,
    int32_pool_offset: int = 9012,
    string_pool_offset: int = 9012,
    reserved_word5: int = 0,
    total_size: int = 9704,
) -> bytes:
    header = struct.pack(
        "<6I",
        field_count,
        record_count,
        float_pool_offset,
        int32_pool_offset,
        string_pool_offset,
        reserved_word5,
    )
    return header + bytes(total_size - len(header))


def test_parses_recovered_xdbboxr_layout() -> None:
    header = parse_xdb_header(_xdb_bytes())

    assert header.field_count == 121
    assert header.record_count == 37
    assert header.word0 == 121
    assert header.word1 == 37
    assert header.type_bitmap_offset == 0x18
    assert header.type_bitmap_size == 31
    assert header.row_matrix_offset == 0x38
    assert header.row_stride == 0xF2
    assert header.row_matrix_padded_end == 9012
    assert header.float_pool_size == 0
    assert header.int32_pool_size == 0
    assert header.string_pool_size == 692
    assert header.field_token_offset(0, 0x14) == 0x60


def test_parses_xdbtrain_float_pool() -> None:
    header = parse_xdb_header(
        _xdb_bytes(
            field_count=11,
            record_count=239,
            float_pool_offset=5288,
            int32_pool_offset=7200,
            string_pool_offset=7200,
            total_size=8032,
        )
    )

    assert header.row_matrix_offset == 0x1C
    assert header.row_stride == 22
    assert header.row_matrix_padded_end == 5288
    assert header.float_pool_size == 1912
    assert header.int32_pool_size == 0
    assert header.string_pool_size == 832


def test_decodes_two_bit_field_type_map_msb_first() -> None:
    data = bytearray(_xdb_bytes())
    # fields 0..3 -> 0, 1, 2, 3
    data[0x18] = 0b00011011
    assert [xdb_field_type(data, i) for i in range(4)] == [0, 1, 2, 3]


def test_rejects_payload_smaller_than_the_proven_header() -> None:
    with pytest.raises(XdbFormatError, match="smaller than the proven header"):
        parse_xdb_header(b"\x00" * 16)


def test_rejects_nonmatching_row_matrix_end() -> None:
    with pytest.raises(XdbFormatError, match="row matrix"):
        parse_xdb_header(_xdb_bytes(float_pool_offset=9008))


def test_record_and_field_bounds() -> None:
    header = parse_xdb_header(_xdb_bytes())
    with pytest.raises(IndexError):
        header.record_offset(37)
    with pytest.raises(IndexError):
        header.field_token_offset(0, 121)
