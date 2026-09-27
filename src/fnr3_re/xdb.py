"""EA ``xdb*.adf`` table layout recovered from retail/debug static RE.

The tracked XDB family uses a 24-byte fixed header followed by a packed
2-bit-per-field type bitmap and a row-major matrix of 16-bit field tokens.
Pool offsets in the header then resolve non-inline token types.

Executable proof:
- ``func_001AD21C`` returns header word1 as the row/record count.
- ``func_001AD180`` bounds a row index by word1 and computes the row pointer
  from word0 * word1 * 2.
- ``func_001ACCAC`` bounds a field index by word0 and reads the 2-bit type
  code at payload+0x18+(field>>2).
- ``func_001ACD40`` resolves type 0 inline i16, type 1 byte/string-pool,
  type 2 int32-pool, and type 3 float-pool fields.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

_HEADER_SIZE = 24
_HEADER_FORMAT = "<6I"
_TYPE_BITMAP_OFFSET = 0x18


class XdbFormatError(ValueError):
    """Raised when decoded XDB bytes violate the recovered layout."""


def _align4(value: int) -> int:
    return (value + 3) & ~3


@dataclass(frozen=True, slots=True)
class XdbHeader:
    """Recovered XDB fixed header and deterministic layout helpers."""

    field_count: int
    record_count: int
    float_pool_offset: int
    int32_pool_offset: int
    string_pool_offset: int
    reserved_word5: int
    payload_size: int

    @property
    def word0(self) -> int:
        return self.field_count

    @property
    def word1(self) -> int:
        return self.record_count

    @property
    def section_size_a(self) -> int:
        return self.float_pool_offset

    @property
    def section_size_b(self) -> int:
        return self.int32_pool_offset

    @property
    def section_size_c(self) -> int:
        return self.string_pool_offset

    @property
    def word5(self) -> int:
        return self.reserved_word5

    @property
    def section_sizes_agree(self) -> bool:
        return (
            self.float_pool_offset
            == self.int32_pool_offset
            == self.string_pool_offset
        )

    @property
    def type_bitmap_offset(self) -> int:
        return _TYPE_BITMAP_OFFSET

    @property
    def type_bitmap_size(self) -> int:
        return (self.field_count + 3) // 4

    @property
    def row_matrix_offset(self) -> int:
        return _align4(self.type_bitmap_offset + self.type_bitmap_size)

    @property
    def row_stride(self) -> int:
        return self.field_count * 2

    @property
    def row_matrix_size(self) -> int:
        return self.row_stride * self.record_count

    @property
    def row_matrix_padded_end(self) -> int:
        return self.row_matrix_offset + _align4(self.row_matrix_size)

    @property
    def float_pool_size(self) -> int:
        return self.int32_pool_offset - self.float_pool_offset

    @property
    def int32_pool_size(self) -> int:
        return self.string_pool_offset - self.int32_pool_offset

    @property
    def string_pool_size(self) -> int:
        return self.payload_size - self.string_pool_offset

    @property
    def trailing_bytes(self) -> int:
        """Compatibility alias for the bytes at/after the string pool."""
        return self.string_pool_size

    def record_offset(self, record_index: int) -> int:
        if not 0 <= record_index < self.record_count:
            raise IndexError(record_index)
        return self.row_matrix_offset + record_index * self.row_stride

    def field_token_offset(self, record_index: int, field_index: int) -> int:
        if not 0 <= field_index < self.field_count:
            raise IndexError(field_index)
        return self.record_offset(record_index) + field_index * 2


def parse_xdb_header(decoded: bytes | bytearray | memoryview) -> XdbHeader:
    """Parse and validate the recovered six-word XDB header."""

    data = bytes(decoded)
    if len(data) < _HEADER_SIZE:
        raise XdbFormatError(
            f"xdb payload is smaller than the proven header: {len(data)} bytes"
        )

    words = struct.unpack_from(_HEADER_FORMAT, data, 0)
    header = XdbHeader(
        field_count=words[0],
        record_count=words[1],
        float_pool_offset=words[2],
        int32_pool_offset=words[3],
        string_pool_offset=words[4],
        reserved_word5=words[5],
        payload_size=len(data),
    )

    if not (
        header.row_matrix_offset
        <= header.float_pool_offset
        <= header.int32_pool_offset
        <= header.string_pool_offset
        <= header.payload_size
    ):
        raise XdbFormatError("xdb section offsets are not monotonic/in bounds")

    if header.row_matrix_padded_end != header.float_pool_offset:
        raise XdbFormatError(
            "xdb row matrix does not end at the declared float-pool offset: "
            f"{header.row_matrix_padded_end} != {header.float_pool_offset}"
        )

    return header


def xdb_field_type(decoded: bytes | bytearray | memoryview, field_index: int) -> int:
    """Return the recovered 2-bit field type code (0..3)."""

    data = bytes(decoded)
    header = parse_xdb_header(data)
    if not 0 <= field_index < header.field_count:
        raise IndexError(field_index)
    byte = data[header.type_bitmap_offset + (field_index >> 2)]
    shift = 6 - ((field_index & 3) * 2)
    return (byte >> shift) & 0x3
