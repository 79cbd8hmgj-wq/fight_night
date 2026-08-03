from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Literal, overload

_SIGNATURE_24_BIT = b"\x10\xfb"
_SIGNATURE_32_BIT = b"\x90\xfb"
_MAX_24_BIT_SIZE = 0xFFFFFF
_MAX_32_BIT_SIZE = 0xFFFFFFFF
_MAX_BACKREFERENCE = 0x20000
_MAX_MATCH_LENGTH = 1028
_MAX_LITERAL_RUN = 112
_MAX_CANDIDATES = 64
_DEFAULT_OUTPUT_LIMIT = 512 * 1024 * 1024


class RefPackError(ValueError):
    """Raised when a RefPack stream is malformed or unsupported."""


def is_refpack(payload: bytes | bytearray | memoryview) -> bool:
    view = memoryview(payload)
    return len(view) >= 2 and bytes(view[:2]) in {_SIGNATURE_24_BIT, _SIGNATURE_32_BIT}


@overload
def decompress_refpack(
    payload: bytes | bytearray | memoryview,
    *,
    max_output_size: int = _DEFAULT_OUTPUT_LIMIT,
    allow_trailing: bool = False,
    return_consumed: Literal[False] = False,
) -> bytes: ...


@overload
def decompress_refpack(
    payload: bytes | bytearray | memoryview,
    *,
    max_output_size: int = _DEFAULT_OUTPUT_LIMIT,
    allow_trailing: bool = False,
    return_consumed: Literal[True],
) -> tuple[bytes, int]: ...


def decompress_refpack(
    payload: bytes | bytearray | memoryview,
    *,
    max_output_size: int = _DEFAULT_OUTPUT_LIMIT,
    allow_trailing: bool = False,
    return_consumed: bool = False,
) -> bytes | tuple[bytes, int]:
    """Decode one bounded EA RefPack stream.

    The decoder accepts the reference headers used by the game: ``10 FB`` with a
    three-byte size and ``90 FB`` with a four-byte size. Other header variants are
    rejected until their additional fields are evidenced by the supported build.
    """

    if max_output_size < 0:
        raise ValueError("max_output_size must be non-negative")
    data = memoryview(payload).cast("B")
    declared_size, position = _parse_header(data)
    if declared_size > max_output_size:
        raise RefPackError(
            f"declared output exceeds limit: {declared_size} > {max_output_size}"
        )

    output = bytearray()
    terminated = False
    while position < len(data):
        first = data[position]
        if first < 0x80:
            _require(data, position, 2, "short command is truncated")
            second = data[position + 1]
            position += 2
            literal_count = first & 0x03
            copy_length = ((first & 0x1C) >> 2) + 3
            distance = ((first & 0x60) << 3) + second + 1
            position = _append_literals(
                data,
                position,
                literal_count,
                output,
                declared_size,
                "short command literal run is truncated",
            )
            _append_backreference(output, distance, copy_length, declared_size)
            continue

        if first < 0xC0:
            _require(data, position, 3, "medium command is truncated")
            second = data[position + 1]
            third = data[position + 2]
            position += 3
            literal_count = second >> 6
            copy_length = (first & 0x3F) + 4
            distance = ((second & 0x3F) << 8) + third + 1
            position = _append_literals(
                data,
                position,
                literal_count,
                output,
                declared_size,
                "medium command literal run is truncated",
            )
            _append_backreference(output, distance, copy_length, declared_size)
            continue

        if first < 0xE0:
            _require(data, position, 4, "long command is truncated")
            second = data[position + 1]
            third = data[position + 2]
            fourth = data[position + 3]
            position += 4
            literal_count = first & 0x03
            copy_length = ((first & 0x0C) << 6) + fourth + 5
            distance = ((first & 0x10) << 12) + (second << 8) + third + 1
            position = _append_literals(
                data,
                position,
                literal_count,
                output,
                declared_size,
                "long command literal run is truncated",
            )
            _append_backreference(output, distance, copy_length, declared_size)
            continue

        if first < 0xFC:
            position += 1
            literal_count = ((first & 0x1F) << 2) + 4
            position = _append_literals(
                data,
                position,
                literal_count,
                output,
                declared_size,
                "literal run is truncated",
            )
            continue

        position += 1
        trailing_literals = first & 0x03
        position = _append_literals(
            data,
            position,
            trailing_literals,
            output,
            declared_size,
            "stop literal run is truncated",
        )
        terminated = True
        break

    if not terminated:
        raise RefPackError("RefPack stream has no stop command")
    if len(output) != declared_size:
        raise RefPackError(
            f"decompressed size mismatch: expected {declared_size}, got {len(output)}"
        )
    if not allow_trailing and position != len(data):
        raise RefPackError("trailing bytes after RefPack stream")

    result = bytes(output)
    if return_consumed:
        return result, position
    return result


def compress_refpack(payload: bytes | bytearray | memoryview) -> bytes:
    """Encode bytes as a deterministic reference RefPack stream.

    Match selection is greedy and deterministic. Equal candidates prefer the longer
    match, then the shorter command, then the nearest prior source position.
    """

    source = bytes(payload)
    source_size = len(source)
    if source_size > _MAX_32_BIT_SIZE:
        raise RefPackError(f"input is too large for RefPack: {source_size}")

    output = bytearray(_encode_header(source_size))
    positions_by_prefix: dict[bytes, list[int]] = defaultdict(list)
    indexed_until = 0
    literal_start = 0
    position = 0

    while position + 3 <= source_size:
        while indexed_until < position:
            if indexed_until + 3 <= source_size:
                positions_by_prefix[source[indexed_until : indexed_until + 3]].append(
                    indexed_until
                )
            indexed_until += 1

        match = _find_match(source, position, positions_by_prefix)
        if match is None:
            position += 1
            continue

        match_distance, match_length, command_size = match
        pending = source[literal_start:position]
        remaining_literals = _emit_literal_prefix(output, pending)
        output.extend(
            _encode_copy_command(
                distance=match_distance,
                length=match_length,
                literal_count=len(remaining_literals),
                command_size=command_size,
            )
        )
        output.extend(remaining_literals)
        position += match_length
        literal_start = position

    pending = source[literal_start:]
    trailing_literals = _emit_literal_prefix(output, pending)
    output.append(0xFC + len(trailing_literals))
    output.extend(trailing_literals)
    return bytes(output)


def _parse_header(data: memoryview) -> tuple[int, int]:
    if len(data) < 2:
        raise RefPackError("RefPack header is truncated")
    signature = bytes(data[:2])
    if signature == _SIGNATURE_24_BIT:
        if len(data) < 5:
            raise RefPackError("RefPack header is truncated")
        return int.from_bytes(data[2:5], "big"), 5
    if signature == _SIGNATURE_32_BIT:
        if len(data) < 6:
            raise RefPackError("RefPack header is truncated")
        return int.from_bytes(data[2:6], "big"), 6
    raise RefPackError(f"unsupported RefPack signature: {signature.hex()}")


def _require(data: memoryview, position: int, size: int, message: str) -> None:
    if position < 0 or size < 0 or position + size > len(data):
        raise RefPackError(message)


def _append_literals(
    data: memoryview,
    position: int,
    count: int,
    output: bytearray,
    declared_size: int,
    truncated_message: str,
) -> int:
    _require(data, position, count, truncated_message)
    if len(output) + count > declared_size:
        raise RefPackError("decompressed output exceeds declared size")
    output.extend(data[position : position + count])
    return position + count


def _append_backreference(
    output: bytearray,
    distance: int,
    length: int,
    declared_size: int,
) -> None:
    if distance <= 0 or distance > len(output):
        raise RefPackError(
            f"backreference exceeds produced output: distance {distance}, output {len(output)}"
        )
    if len(output) + length > declared_size:
        raise RefPackError("decompressed output exceeds declared size")
    for _ in range(length):
        output.append(output[-distance])


def _encode_header(source_size: int) -> bytes:
    if source_size <= _MAX_24_BIT_SIZE:
        return _SIGNATURE_24_BIT + source_size.to_bytes(3, "big")
    return _SIGNATURE_32_BIT + source_size.to_bytes(4, "big")


def _find_match(
    source: bytes,
    position: int,
    positions_by_prefix: dict[bytes, list[int]],
) -> tuple[int, int, int] | None:
    candidates = positions_by_prefix.get(source[position : position + 3], ())
    best: tuple[int, int, int, int] | None = None
    for candidate in reversed(candidates[-_MAX_CANDIDATES:]):
        distance = position - candidate
        if distance <= 0:
            continue
        if distance > _MAX_BACKREFERENCE:
            break
        actual_length = _match_length(source, candidate, position)
        encoded = _best_command_for_match(distance, actual_length)
        if encoded is None:
            continue
        length, command_size = encoded
        score = length - command_size
        proposed = (score, length, -command_size, -distance)
        if best is None or proposed > best:
            best = proposed
    if best is None:
        return None
    _score, length, negative_command_size, negative_distance = best
    return -negative_distance, length, -negative_command_size


def _match_length(source: bytes, candidate: int, position: int) -> int:
    maximum = min(_MAX_MATCH_LENGTH, len(source) - position)
    length = 0
    while length < maximum and source[candidate + length] == source[position + length]:
        length += 1
    return length


def _best_command_for_match(distance: int, actual_length: int) -> tuple[int, int] | None:
    choices: list[tuple[int, int]] = []
    if distance <= 0x400 and actual_length >= 3:
        choices.append((min(actual_length, 10), 2))
    if distance <= 0x4000 and actual_length >= 4:
        choices.append((min(actual_length, 67), 3))
    if distance <= _MAX_BACKREFERENCE and actual_length >= 5:
        choices.append((min(actual_length, _MAX_MATCH_LENGTH), 4))
    if not choices:
        return None
    return max(choices, key=lambda choice: (choice[0] - choice[1], choice[0], -choice[1]))


def _emit_literal_prefix(output: bytearray, pending: Sequence[int]) -> bytes:
    position = 0
    remaining = len(pending)
    while remaining > 3:
        literal_length = min(
            _MAX_LITERAL_RUN,
            ((remaining - 3) // 4) * 4,
        )
        if literal_length < 4:
            break
        output.append(0xE0 + ((literal_length - 4) // 4))
        output.extend(pending[position : position + literal_length])
        position += literal_length
        remaining -= literal_length
    return bytes(pending[position:])


def _encode_copy_command(
    *,
    distance: int,
    length: int,
    literal_count: int,
    command_size: int,
) -> bytes:
    if literal_count not in range(4):
        raise AssertionError("copy commands can carry at most three literals")
    encoded_distance = distance - 1
    if command_size == 2:
        if not (distance <= 0x400 and 3 <= length <= 10):
            raise AssertionError("invalid short RefPack command")
        first = (
            ((encoded_distance >> 8) << 5)
            | ((length - 3) << 2)
            | literal_count
        )
        return bytes((first, encoded_distance & 0xFF))
    if command_size == 3:
        if not (distance <= 0x4000 and 4 <= length <= 67):
            raise AssertionError("invalid medium RefPack command")
        first = 0x80 | (length - 4)
        second = (literal_count << 6) | ((encoded_distance >> 8) & 0x3F)
        return bytes((first, second, encoded_distance & 0xFF))
    if command_size == 4:
        if not (distance <= _MAX_BACKREFERENCE and 5 <= length <= _MAX_MATCH_LENGTH):
            raise AssertionError("invalid long RefPack command")
        encoded_length = length - 5
        first = (
            0xC0
            | (((encoded_distance >> 16) & 0x01) << 4)
            | (((encoded_length >> 8) & 0x03) << 2)
            | literal_count
        )
        return bytes(
            (
                first,
                (encoded_distance >> 8) & 0xFF,
                encoded_distance & 0xFF,
                encoded_length & 0xFF,
            )
        )
    raise AssertionError(f"unsupported RefPack command size: {command_size}")
