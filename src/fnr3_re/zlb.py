"""EA ``.zlb`` codec: a 4-byte declared-size prefix over standard zlib deflate.

Distinct from the RefPack codec (``src/fnr3_re/refpack.py``) used by the
``.adf``/``.fnc``/``.csv`` family: every ``.zlb`` sample found in the verified
corpus (26/26: the two boot-load screens plus 12 paired venue/environment
assets under ``enviro/``) is a plain little-endian ``uint32`` declared
uncompressed size followed by a standard zlib (RFC 1950) stream, decodable
with the Python standard library's ``zlib`` module with no vendor-specific
framing beyond that size prefix.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

_HEADER_SIZE = 4
_DEFAULT_OUTPUT_LIMIT = 512 * 1024 * 1024


class ZlbError(ValueError):
    """Raised when a ``.zlb`` stream is malformed, unsupported, or exceeds a bound."""


@dataclass(frozen=True, slots=True)
class ZlbFile:
    declared_size: int
    data: bytes


def is_zlb(payload: bytes | bytearray | memoryview) -> bool:
    """Best-effort probe: the declared size prefix, then a valid zlib header.

    Unlike RefPack's fixed two-byte signature, ``.zlb`` has no unique magic of
    its own -- its only distinguishing feature is the standard zlib header
    byte pair immediately after the 4-byte size prefix. This can false-positive
    on arbitrary bytes; callers with a stronger identity signal (e.g. a known
    ``.zlb`` extension from a trusted archive directory) should prefer that.
    """

    view = memoryview(payload)
    if len(view) < _HEADER_SIZE + 2:
        return False
    header = bytes(view[_HEADER_SIZE : _HEADER_SIZE + 2])
    # RFC 1950: CMF low nibble must be 8 (deflate), and the 16-bit header
    # must be a multiple of 31 -- the standard cheap zlib-header validity check.
    if (header[0] & 0x0F) != 8:
        return False
    return (header[0] * 256 + header[1]) % 31 == 0


def decompress_zlb(
    payload: bytes | bytearray | memoryview,
    *,
    max_output_size: int = _DEFAULT_OUTPUT_LIMIT,
) -> bytes:
    """Decode one ``.zlb`` stream: a declared size prefix plus zlib deflate.

    Raises :class:`ZlbError` on a truncated header, a declared size exceeding
    ``max_output_size``, a malformed zlib stream, or a decoded length that
    disagrees with the declared size -- the same fail-closed posture as
    ``refpack.decompress_refpack``.
    """

    if max_output_size < 0:
        raise ZlbError("max_output_size must be non-negative")
    data = bytes(payload)
    if len(data) < _HEADER_SIZE:
        raise ZlbError("zlb header is truncated")
    declared_size = struct.unpack_from("<I", data, 0)[0]
    if declared_size > max_output_size:
        raise ZlbError(f"declared output exceeds limit: {declared_size} > {max_output_size}")
    try:
        decoded = zlib.decompress(data[_HEADER_SIZE:])
    except zlib.error as exc:
        raise ZlbError(f"malformed zlib stream: {exc}") from exc
    if len(decoded) != declared_size:
        raise ZlbError(
            f"decompressed size mismatch: expected {declared_size}, got {len(decoded)}"
        )
    return decoded


def compress_zlb(payload: bytes | bytearray | memoryview, *, level: int = 9) -> bytes:
    """Encode bytes as a ``.zlb`` stream: declared size prefix plus zlib deflate.

    Deterministic for a fixed ``level`` (Python's ``zlib.compress`` has no
    randomized state). Does not claim to reproduce the original EA encoder's
    exact compressed bytes -- only decode-equivalence, matching the RefPack
    codec's own documented standard (``docs/architecture/resource-codecs.md``).
    """

    data = bytes(payload)
    if not 0 <= level <= 9:
        raise ZlbError("level must be between 0 and 9")
    compressed = zlib.compress(data, level)
    return struct.pack("<I", len(data)) + compressed
