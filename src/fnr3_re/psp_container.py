from __future__ import annotations

from dataclasses import dataclass

_HEADER_SIZE = 100
_MAX_SEGMENTS = 4


class PspContainerError(ValueError):
    """Raised when a packed PSP executable header is malformed."""


@dataclass(frozen=True, slots=True)
class PspContainer:
    module_name: str
    module_attributes: int
    compression_attributes: int
    module_version: tuple[int, int]
    header_version: int
    segment_count: int
    elf_size: int
    psp_size: int
    entry_point: int
    module_info_offset: int
    bss_size: int
    segment_alignments: tuple[int, ...]
    segment_addresses: tuple[int, ...]
    segment_sizes: tuple[int, ...]


def parse_psp_container(payload: bytes | bytearray | memoryview) -> PspContainer:
    data = bytes(payload)
    if len(data) < _HEADER_SIZE:
        raise PspContainerError("PSP executable header is truncated")
    if data[0:4] != b"~PSP":
        raise PspContainerError("PSP executable magic is invalid")

    module_name = _decode_module_name(data[10:38])
    segment_count = data[39]
    if segment_count > _MAX_SEGMENTS:
        raise PspContainerError(f"PSP segment count exceeds four: {segment_count}")
    elf_size = _u32(data, 40)
    psp_size = _u32(data, 44)
    if psp_size != len(data):
        raise PspContainerError(
            f"PSP size mismatch: header declares {psp_size}, file has {len(data)}"
        )
    if elf_size <= 0 or elf_size > psp_size:
        raise PspContainerError(
            f"ELF size is outside packed executable: {elf_size} > {psp_size}"
        )

    alignments = tuple(_u16(data, 60 + index * 2) for index in range(segment_count))
    addresses = tuple(_u32(data, 68 + index * 4) for index in range(segment_count))
    sizes = tuple(_u32(data, 84 + index * 4) for index in range(segment_count))
    for index, alignment in enumerate(alignments):
        if alignment not in {0, 1} and alignment & (alignment - 1):
            raise PspContainerError(
                f"PSP segment {index} alignment is not a power of two"
            )
    for index, size in enumerate(sizes):
        if size > elf_size:
            raise PspContainerError(
                f"PSP segment {index} size exceeds declared ELF size"
            )

    module_info_offset = _u32(data, 52)
    if module_info_offset >= elf_size:
        raise PspContainerError("module info offset is outside declared ELF")

    return PspContainer(
        module_name=module_name,
        module_attributes=_u16(data, 4),
        compression_attributes=_u16(data, 6),
        module_version=(data[8], data[9]),
        header_version=data[38],
        segment_count=segment_count,
        elf_size=elf_size,
        psp_size=psp_size,
        entry_point=_u32(data, 48),
        module_info_offset=module_info_offset,
        bss_size=_u32(data, 56),
        segment_alignments=alignments,
        segment_addresses=addresses,
        segment_sizes=sizes,
    )


def _decode_module_name(encoded: bytes) -> str:
    value = encoded.split(b"\x00", 1)[0]
    if not value:
        raise PspContainerError("PSP module name is empty")
    try:
        return value.decode("ascii")
    except UnicodeDecodeError as exc:
        raise PspContainerError("PSP module name is not ASCII") from exc


def _u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "little")


def _u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")
