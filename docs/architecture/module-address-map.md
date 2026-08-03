# PSP module and address map

Task 7 establishes the static executable layout and an explicit boundary between address spaces. It does not infer runtime load bases, module ownership, or packed-container offsets from platform conventions.

## Executable forms

### Plain ELF32

`BOOT.BIN` is parsed as a little-endian 32-bit MIPS ELF. The parser validates:

- ELF class, endianness, identification version, machine, and header sizes;
- program-header and section-header table bounds;
- load-segment file and memory sizes;
- file-backed and BSS ranges;
- section-name string-table bounds;
- power-of-two alignments;
- ambiguous overlapping load segments.

The module map records each load segment and section, the ELF image base, entry point, object type, flags, file SHA-256, and ISO location when the file came from a verified workspace.

### Packed PSP container

`EBOOT.BIN` and packed PRX files begin with `~PSP`. The parser records only header fields that are structurally present:

- module name and version;
- module and compression attributes;
- header version and segment count;
- declared ELF and packed sizes;
- entry point and module-info offset;
- BSS size;
- declared segment alignments, addresses, and sizes.

A packed container is not treated as if its internal ELF offsets were directly available. Its map status remains:

```text
packed_container_requires_decrypted_elf
```

until a deterministic decrypted correspondence is captured.

## Address spaces

The project keeps these address types distinct:

| Type | Meaning |
|---|---|
| `runtime` | Address observed after the module is loaded |
| `module_relative` | Offset from the ELF image base |
| `elf_virtual` | ELF virtual address |
| `elf_file_offset` | Offset in the decrypted ELF file |
| `stored_prx_offset` | Offset in the stored module file |
| `archive_offset` | Offset within a containing archive; never inferred by this mapper |
| `iso_offset` | Absolute byte offset in the ISO image |
| `iso_lba` | Exact ISO sector number |

`AddressTranslator` requires the caller to supply each known base explicitly:

```python
AddressTranslator(
    module_id="main",
    elf=boot_elf,
    runtime_base=confirmed_runtime_base,
    stored_elf_offset=0,
    iso_file_offset=boot_iso_offset,
)
```

The translator supports lossless direct conversions between file, stored-module, and ISO offsets even for ELF headers. Runtime and module-relative conversions require a mapped ELF memory range. BSS addresses can map between ELF virtual, module-relative, and runtime spaces but cannot map to file offsets.

An ISO offset converts to `iso_lba` only when it is exactly sector-aligned. Archive offsets are rejected until a separate archive-member mapping is supplied. This prevents address types from being collapsed into one untyped integer.

## Module-map command

```bash
fnr3-re module-map /local/path/fnr3-workspace --json
fnr3-re module-map /local/path/fnr3-workspace \
  --output /local/path/modules.json
```

The workspace must pass its immutable-file verification first. The generated JSON preserves manifest order and records unresolved facts instead of filling them with assumptions.

## Confirmed tracked pair

The repository fixtures establish:

- `BOOT.BIN`: plain PSP ELF32 MIPS executable;
- `EBOOT.BIN`: packed `~PSP` container named `FightNight`;
- both declare entry point `0x0034DECC`;
- the packed container's declared ELF size equals the tracked `BOOT.BIN` size;
- no runtime base is confirmed by static parsing alone.

## Remaining runtime and full-image gates

The environment-gated retail-image test requires the exact workspace to expose:

- `PSP_GAME/SYSDIR/BOOT.BIN`;
- `PSP_GAME/SYSDIR/EBOOT.BIN`;
- six `.prx` modules;
- eight executable module records total;
- no invented runtime bases.

PPSSPP capture is still required to confirm:

- actual load base for every module;
- load and unload order;
- module owners and consumers;
- import and export resolution;
- relocation behavior;
- overlays or mutually exclusive modules;
- whether each packed PRX has a stable decrypted ELF correspondence.

No module is labeled complete merely because its static header parsed successfully.
