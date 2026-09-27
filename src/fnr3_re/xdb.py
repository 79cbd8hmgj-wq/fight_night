"""EA ``xdb*.adf`` table structure recovered from executable consumers.

The common 32-byte prefix is eight little-endian ``uint32`` words. Follow-up
static RE of ``func_001AD180``, ``func_001ACCAC``, and ``func_001ACD40``
resolves the two leading words and the record/field descriptor matrix:

* ``word0`` = field/column count.
* ``word1`` = record/row count.
* packed 2-bit field-type codes begin at payload ``+0x18``.
* one signed 16-bit descriptor exists for every (record, field) pair.
* the descriptor matrix ends at ``section_size_a`` and is row-major.

Field type 0 is an inline signed 16-bit value, type 1 indexes the string pool
at ``section_size_c``, type 2 indexes the int32 pool at ``section_size_b``,
and type 3 indexes the float32 pool at ``section_size_a``.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum

_HEADER_SIZE = 32
_HEADER_FORMAT = "<8I"
_FIELD_TYPE_OFFSET = 0x18


class XdbFormatError(ValueError):
    """Raised when decoded xdb bytes do not match the recovered structure."""


class XdbFieldType(IntEnum):
    """Two-bit field storage class used by the native XDB accessor."""

    INLINE_I16 = 0
    STRING = 1
    INT32 = 2
    FLOAT32 = 3


def _align4(value: int) -> int:
    return (value + 3) & ~3


@dataclass(frozen=True, slots=True)
class XdbHeader:
    """Recovered common XDB header.

    ``word0``/``word1`` remain available for backward compatibility with
    older analysis artifacts; ``field_count`` and ``record_count`` are the
    now-proven semantic aliases.
    """

    word0: int
    word1: int
    section_size_a: int
    section_size_b: int
    section_size_c: int
    word5: int
    word6: int
    word7: int
    payload_size: int

    @property
    def field_count(self) -> int:
        return self.word0

    @property
    def record_count(self) -> int:
        return self.word1

    @property
    def field_type_bytes(self) -> int:
        return (self.field_count + 3) // 4

    @property
    def record_descriptor_stride(self) -> int:
        return self.field_count * 2

    @property
    def record_descriptor_matrix_size(self) -> int:
        return _align4(self.record_descriptor_stride * self.record_count)

    @property
    def record_descriptor_matrix_offset(self) -> int:
        return self.section_size_a - self.record_descriptor_matrix_size

    @property
    def section_sizes_agree(self) -> bool:
        return self.section_size_a == self.section_size_b == self.section_size_c

    @property
    def trailing_bytes(self) -> int:
        return self.payload_size - self.section_size_c


def parse_xdb_header(decoded: bytes | bytearray | memoryview) -> XdbHeader:
    """Parse and structurally validate the recovered XDB header."""

    data = bytes(decoded)
    if len(data) < _HEADER_SIZE:
        raise XdbFormatError(
            f"xdb payload is smaller than the recovered header: {len(data)} bytes"
        )
    words = struct.unpack_from(_HEADER_FORMAT, data, 0)
    section_size_a, section_size_b, section_size_c = words[2:5]
    if not (section_size_a <= section_size_b <= section_size_c <= len(data)):
        raise XdbFormatError(
            "xdb section offsets are not monotonic/in-bounds: "
            f"{section_size_a}, {section_size_b}, {section_size_c}, size={len(data)}"
        )
    header = XdbHeader(
        word0=words[0],
        word1=words[1],
        section_size_a=section_size_a,
        section_size_b=section_size_b,
        section_size_c=section_size_c,
        word5=words[5],
        word6=words[6],
        word7=words[7],
        payload_size=len(data),
    )
    matrix_offset = header.record_descriptor_matrix_offset
    type_table_end = _FIELD_TYPE_OFFSET + header.field_type_bytes
    if matrix_offset < _align4(type_table_end):
        raise XdbFormatError(
            "xdb descriptor matrix overlaps the field-type table: "
            f"matrix=0x{matrix_offset:X}, type_end=0x{type_table_end:X}"
        )
    return header


def xdb_field_type(
    decoded: bytes | bytearray | memoryview, field_id: int
) -> XdbFieldType:
    """Return the native two-bit storage class for ``field_id``."""

    data = bytes(decoded)
    header = parse_xdb_header(data)
    if not 0 <= field_id < header.field_count:
        raise XdbFormatError(
            f"field_id {field_id} outside field count {header.field_count}"
        )
    packed = data[_FIELD_TYPE_OFFSET + (field_id >> 2)]
    shift = 6 - ((field_id & 3) * 2)
    return XdbFieldType((packed >> shift) & 0x3)


def xdb_record_field_descriptor_offset(
    decoded: bytes | bytearray | memoryview, record_index: int, field_id: int
) -> int:
    """Return the payload offset of one record/field signed-i16 descriptor."""

    header = parse_xdb_header(decoded)
    if not 0 <= record_index < header.record_count:
        raise XdbFormatError(
            f"record_index {record_index} outside record count {header.record_count}"
        )
    if not 0 <= field_id < header.field_count:
        raise XdbFormatError(
            f"field_id {field_id} outside field count {header.field_count}"
        )
    return (
        header.record_descriptor_matrix_offset
        + record_index * header.record_descriptor_stride
        + field_id * 2
    )


def xdb_inline_i16(
    decoded: bytes | bytearray | memoryview, record_index: int, field_id: int
) -> int:
    """Read a type-0 inline signed 16-bit field exactly as the game does."""

    data = bytes(decoded)
    field_type = xdb_field_type(data, field_id)
    if field_type is not XdbFieldType.INLINE_I16:
        raise XdbFormatError(
            f"field {field_id} is {field_type.name}, not INLINE_I16"
        )
    offset = xdb_record_field_descriptor_offset(data, record_index, field_id)
    return struct.unpack_from("<h", data, offset)[0]
