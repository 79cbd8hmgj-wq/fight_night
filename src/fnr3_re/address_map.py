from __future__ import annotations

from dataclasses import dataclass

from .elf32 import Elf32Error, Elf32Image
from .evidence import Address, AddressType


class AddressTranslationError(ValueError):
    """Raised when two address spaces cannot be mapped without losing information."""


@dataclass(frozen=True, slots=True)
class AddressTranslator:
    module_id: str
    elf: Elf32Image
    runtime_base: int | None
    stored_elf_offset: int
    iso_file_offset: int | None
    sector_size: int = 2048

    def __post_init__(self) -> None:
        if not self.module_id.strip():
            raise ValueError("module_id is required")
        if self.runtime_base is not None and self.runtime_base < 0:
            raise ValueError("runtime_base must be non-negative")
        if self.stored_elf_offset < 0:
            raise ValueError("stored_elf_offset must be non-negative")
        if self.iso_file_offset is not None and self.iso_file_offset < 0:
            raise ValueError("iso_file_offset must be non-negative")
        if self.sector_size <= 0:
            raise ValueError("sector_size must be positive")

    def translate(self, source: Address, target: AddressType) -> Address:
        if source.address_type is target:
            return source
        if source.address_type is AddressType.ARCHIVE_OFFSET:
            raise AddressTranslationError("unsupported address space: archive_offset")
        if target is AddressType.ARCHIVE_OFFSET:
            raise AddressTranslationError("unsupported address space: archive_offset")

        direct = self._translate_direct_offset(source, target)
        if direct is not None:
            return Address(target, direct)
        relative = self._to_module_relative(source)
        return Address(target, self._from_module_relative(relative, target))

    def _translate_direct_offset(
        self, source: Address, target: AddressType
    ) -> int | None:
        source_type = source.address_type
        value = source.value
        if source_type is AddressType.ISO_OFFSET and target is AddressType.ISO_LBA:
            if value % self.sector_size:
                raise AddressTranslationError(
                    f"ISO offset 0x{value:x} is not sector aligned"
                )
            return value // self.sector_size
        if source_type is AddressType.ISO_LBA and target is AddressType.ISO_OFFSET:
            return value * self.sector_size
        if source_type is AddressType.STORED_PRX_OFFSET and target is AddressType.ISO_OFFSET:
            return self._require_iso_file_offset() + value
        if source_type is AddressType.ISO_OFFSET and target is AddressType.STORED_PRX_OFFSET:
            iso_file_offset = self._require_iso_file_offset()
            if value < iso_file_offset:
                raise AddressTranslationError(
                    f"ISO offset 0x{value:x} is before module file offset "
                    f"0x{iso_file_offset:x}"
                )
            return value - iso_file_offset
        if source_type is AddressType.ELF_FILE_OFFSET and target is AddressType.STORED_PRX_OFFSET:
            self._validate_elf_file_offset(value)
            return self.stored_elf_offset + value
        if source_type is AddressType.STORED_PRX_OFFSET and target is AddressType.ELF_FILE_OFFSET:
            elf_offset = value - self.stored_elf_offset
            self._validate_elf_file_offset(elf_offset)
            return elf_offset
        if source_type is AddressType.ELF_FILE_OFFSET and target is AddressType.ISO_OFFSET:
            stored = self._translate_direct_offset(
                source, AddressType.STORED_PRX_OFFSET
            )
            if stored is None:
                raise AssertionError("ELF-to-stored translation unexpectedly failed")
            return self._require_iso_file_offset() + stored
        if source_type is AddressType.ISO_OFFSET and target is AddressType.ELF_FILE_OFFSET:
            stored = self._translate_direct_offset(
                source, AddressType.STORED_PRX_OFFSET
            )
            if stored is None:
                raise AssertionError("ISO-to-stored translation unexpectedly failed")
            return self._translate_direct_offset(
                Address(AddressType.STORED_PRX_OFFSET, stored),
                AddressType.ELF_FILE_OFFSET,
            )
        return None

    def _validate_elf_file_offset(self, value: int) -> None:
        if value < 0 or value >= self.elf.source_size:
            raise AddressTranslationError(
                f"ELF file offset 0x{value:x} is outside source file"
            )

    def _to_module_relative(self, source: Address) -> int:
        source_type = source.address_type
        value = source.value
        try:
            if source_type is AddressType.MODULE_RELATIVE:
                self._ensure_memory_mapped(self.elf.module_relative_to_virtual(value))
                return value
            if source_type is AddressType.ELF_VIRTUAL:
                self._ensure_memory_mapped(value)
                return self.elf.virtual_to_module_relative(value)
            if source_type is AddressType.ELF_FILE_OFFSET:
                virtual = self.elf.file_offset_to_virtual(value)
                return self.elf.virtual_to_module_relative(virtual)
            if source_type is AddressType.RUNTIME:
                runtime_base = self._require_runtime_base()
                if value < runtime_base:
                    raise AddressTranslationError(
                        f"runtime address 0x{value:x} is below runtime base "
                        f"0x{runtime_base:x}"
                    )
                relative = value - runtime_base
                self._ensure_memory_mapped(
                    self.elf.module_relative_to_virtual(relative)
                )
                return relative
            if source_type is AddressType.STORED_PRX_OFFSET:
                return self._stored_to_relative(value)
            if source_type is AddressType.ISO_OFFSET:
                iso_file_offset = self._require_iso_file_offset()
                if value < iso_file_offset:
                    raise AddressTranslationError(
                        f"ISO offset 0x{value:x} is before module file offset "
                        f"0x{iso_file_offset:x}"
                    )
                return self._stored_to_relative(value - iso_file_offset)
            if source_type is AddressType.ISO_LBA:
                return self._to_module_relative(
                    Address(AddressType.ISO_OFFSET, value * self.sector_size)
                )
        except Elf32Error as exc:
            raise AddressTranslationError(str(exc)) from exc
        raise AddressTranslationError(f"unsupported address space: {source_type.value}")

    def _from_module_relative(self, relative: int, target: AddressType) -> int:
        try:
            virtual = self.elf.module_relative_to_virtual(relative)
            self._ensure_memory_mapped(virtual)
            if target is AddressType.MODULE_RELATIVE:
                return relative
            if target is AddressType.ELF_VIRTUAL:
                return virtual
            if target is AddressType.RUNTIME:
                return self._require_runtime_base() + relative
            if target is AddressType.ELF_FILE_OFFSET:
                return self.elf.virtual_to_file_offset(virtual)
            if target is AddressType.STORED_PRX_OFFSET:
                return self.stored_elf_offset + self.elf.virtual_to_file_offset(virtual)
            if target is AddressType.ISO_OFFSET:
                return (
                    self._require_iso_file_offset()
                    + self.stored_elf_offset
                    + self.elf.virtual_to_file_offset(virtual)
                )
            if target is AddressType.ISO_LBA:
                iso_offset = self._from_module_relative(relative, AddressType.ISO_OFFSET)
                if iso_offset % self.sector_size:
                    raise AddressTranslationError(
                        f"ISO offset 0x{iso_offset:x} is not sector aligned"
                    )
                return iso_offset // self.sector_size
        except Elf32Error as exc:
            raise AddressTranslationError(str(exc)) from exc
        raise AddressTranslationError(f"unsupported address space: {target.value}")

    def _stored_to_relative(self, stored_offset: int) -> int:
        if stored_offset < self.stored_elf_offset:
            raise AddressTranslationError(
                f"stored offset 0x{stored_offset:x} is before embedded ELF offset "
                f"0x{self.stored_elf_offset:x}"
            )
        elf_offset = stored_offset - self.stored_elf_offset
        try:
            virtual = self.elf.file_offset_to_virtual(elf_offset)
            return self.elf.virtual_to_module_relative(virtual)
        except Elf32Error as exc:
            raise AddressTranslationError(str(exc)) from exc

    def _ensure_memory_mapped(self, virtual: int) -> None:
        matches = [
            segment
            for segment in self.elf.load_segments
            if segment.virtual_address <= virtual < segment.virtual_memory_end
        ]
        if len(matches) == 1:
            return
        if len(matches) > 1:
            raise AddressTranslationError(
                f"virtual address 0x{virtual:x} has ambiguous memory mappings"
            )
        raise AddressTranslationError(
            f"virtual address 0x{virtual:x} is not mapped by a load segment"
        )

    def _require_runtime_base(self) -> int:
        if self.runtime_base is None:
            raise AddressTranslationError("runtime base is unknown")
        return self.runtime_base

    def _require_iso_file_offset(self) -> int:
        if self.iso_file_offset is None:
            raise AddressTranslationError("ISO file offset is unknown")
        return self.iso_file_offset
