"""EA ``xdb*.adf`` table header parsing (the ``preload/db.viv`` family).

Task 10 static evidence: every decoded member of ``preload/db.viv`` (ten
``xdbNNNN.adf`` tables, including ``xdbboxr.adf``) opens with the same
eight little-endian ``uint32`` words. Only that shared header is proven
here -- the per-record field layout for any individual table remains open
(see ``docs/decomp/packages/xdb-schema/README.md``) and must not be
inferred from this header alone.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

_HEADER_SIZE = 32
_HEADER_FORMAT = "<8I"


class XdbFormatError(ValueError):
    """Raised when decoded xdb table bytes do not match the proven header shape."""


@dataclass(frozen=True, slots=True)
class XdbHeader:
    """The eight-word header observed at the start of every decoded xdb table.

    Field names are deliberately neutral: static evidence proves the shape
    (two small leading counts, three usually-equal section-size words, three
    trailing words that are usually zero) but not which count is "records"
    versus "fields", or what the trailing words mean when non-zero.
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
    def section_sizes_agree(self) -> bool:
        return self.section_size_a == self.section_size_b == self.section_size_c

    @property
    def trailing_bytes(self) -> int:
        return self.payload_size - self.section_size_c


def parse_xdb_header(decoded: bytes | bytearray | memoryview) -> XdbHeader:
    """Parse the proven eight-word header from one decoded (decompressed) xdb table.

    Raises :class:`XdbFormatError` if the payload is too small or the
    declared primary section size exceeds the payload -- both are structural
    sanity checks proven across every observed ``preload/db.viv`` member,
    not a claim about record layout.
    """

    data = bytes(decoded)
    if len(data) < _HEADER_SIZE:
        raise XdbFormatError(
            f"xdb payload is smaller than the proven header: {len(data)} bytes"
        )
    words = struct.unpack_from(_HEADER_FORMAT, data, 0)
    section_size_c = words[4]
    if section_size_c > len(data):
        raise XdbFormatError(
            f"xdb header declares a section size larger than the payload: "
            f"{section_size_c} > {len(data)}"
        )
    return XdbHeader(
        word0=words[0],
        word1=words[1],
        section_size_a=words[2],
        section_size_b=words[3],
        section_size_c=section_size_c,
        word5=words[5],
        word6=words[6],
        word7=words[7],
        payload_size=len(data),
    )
