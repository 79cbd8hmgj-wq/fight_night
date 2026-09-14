"""EA APT UI-script ``.const`` constant-pool parsing.

Delta-pass static evidence: every ``.const`` member found inside this
session's 10 newly-added ``.big`` UI-screen archives (``debugmenu.big``,
``optionsettings.big``, ``selectboxer.big``, and 7 others) opens with the
identical 20-byte signature ``b"Apt constant file\\x1a\\x00\\x00"``, followed
by three little-endian ``uint32`` words (an unidentified size/pool field, an
entry ``count``, and a ``header_len`` that was observed as exactly 32 in
every sample), followed by ``count`` ``(tag, string_offset)`` pairs (every
observed ``tag`` was ``1``), followed by a flat NUL-terminated string pool.
Each entry's ``string_offset`` is an absolute offset into the same file and
resolves to one identifier/constant name referenced by the paired ``.apt``
compiled UI-script bytecode -- e.g. native-function names such as
``GetSelectBoxerInfo`` or literal UI-string constants such as ``$O_Easy``.

Only this constant-name table is proven here. The paired ``.apt`` bytecode
format itself (the actual compiled script, including literal numeric/array
values such as the companion ``m_arrValues`` array observed alongside a
decoded difficulty-enum ``m_arrText``) is not decoded by this module.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

_SIGNATURE = b"Apt constant file\x1a\x00\x00"
_SIGNATURE_LEN = len(_SIGNATURE)
_ENTRY_FORMAT = "<II"
_ENTRY_SIZE = 8


class AptConstFormatError(ValueError):
    """Raised when decoded ``.const`` bytes do not match the proven shape."""


@dataclass(frozen=True, slots=True)
class AptConstFile:
    """The proven constant-pool structure of one decoded ``.const`` member."""

    field_a: int
    entry_count: int
    header_len: int
    names: tuple[str, ...]


def parse_apt_const(decoded: bytes | bytearray | memoryview) -> AptConstFile:
    """Parse the proven constant-name table from one decoded ``.const`` member.

    Raises :class:`AptConstFormatError` if the signature does not match or
    any entry's string offset falls outside the file -- both are structural
    sanity checks proven across all 10 samples decoded this pass, not a
    claim about the paired ``.apt`` bytecode's own semantics.
    """

    data = bytes(decoded)
    if data[:_SIGNATURE_LEN] != _SIGNATURE:
        raise AptConstFormatError(
            f"missing 'Apt constant file' signature: {data[:_SIGNATURE_LEN]!r}"
        )
    field_a, entry_count, header_len = struct.unpack_from(
        "<III", data, _SIGNATURE_LEN
    )
    if header_len < _SIGNATURE_LEN + 12 or header_len > len(data):
        raise AptConstFormatError(f"invalid header_len: {header_len}")

    offset = header_len
    names: list[str] = []
    for _ in range(entry_count):
        if offset + _ENTRY_SIZE > len(data):
            raise AptConstFormatError("constant-entry table is truncated")
        _tag, string_offset = struct.unpack_from(_ENTRY_FORMAT, data, offset)
        if string_offset > len(data):
            raise AptConstFormatError(
                f"constant entry string offset out of range: {string_offset}"
            )
        end = data.find(b"\x00", string_offset)
        if end < 0:
            raise AptConstFormatError("constant name is not NUL-terminated")
        names.append(data[string_offset:end].decode("latin1"))
        offset += _ENTRY_SIZE

    return AptConstFile(
        field_a=field_a,
        entry_count=entry_count,
        header_len=header_len,
        names=tuple(names),
    )
