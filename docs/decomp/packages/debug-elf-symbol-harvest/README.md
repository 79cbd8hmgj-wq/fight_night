# ULES00270 debug ELF symbol harvest

## Scope

This package records symbol-recovery evidence derived from the user-supplied
Fight Night Round 3 PSP review/debug `BOOT.BIN` (ULES00270). The executable
itself is **not** tracked.

The goal is to turn development leftovers in this ELF into evidence-backed
function/source attribution that can be cross-applied to the retail
ULUS10066 reverse-engineering map.

## Binary identity

- SHA-256: `8ff90a628346c67c929ff9f494a3806ef1bcfb41788db9330885348eda49f1b4`
- Size: 7,270,752 bytes
- Format: ELF32 little-endian MIPS/Allegrex, PSP processor-specific executable
- Entry: `0x0034DF24`
- Module name: `FightNight`
- ELF section count: 62

The executable has no conventional `.symtab`, `.strtab`, or DWARF
`.debug_*` sections. Its useful development metadata instead comes from
relocations, assert/source strings, module/import metadata, and direct code
references to those strings.

## Relocation inventory

The ELF retains **178,126** relocation records:

| Section | Records |
| --- | ---: |
| `.rel.text` | 152,464 |
| `.rel.lib.ent` | 1 |
| `.rel.lib.stub` | 84 |
| `.rel.rodata.sceModuleInfo` | 4 |
| `.rel.rodata.sceResident` | 5 |
| `.rel.rodata` | 8,232 |
| `.rel.data` | 13,791 |
| `.rel.eh_frame` | 1 |
| `.rel.cplinit` | 536 |
| `.rel.psp_lib_markimport_` | 5 |
| `.rel.linkonce.d` | 3,003 |

These relocations should be treated as first-class reference evidence when
recovering globals, tables, and code/data relationships.

## Fight Night source paths recovered

### AIP

`E:\\muon\\boxing\\main\\game\\source\\boxing\\AIP\\aip.cpp`

- Source-path/string xref in `T_000CE8A0`
- Assert line: **1492**
- Assert expression: `s_pfnGetLocalizedString`
- This directly source-attributes the existing localization-indirection lead
  to the AIP implementation.

### Front end player

`E:\\muon\\boxing\\main\\game\\source\\boxing\\fe\\feplayer.cpp`

- Xref inside `func_001C6658` (boundary probable)
- Assert line: **3270**
- Assert expression: `texture_file`

### PSP front-end animation

`E:\\muon\\boxing\\main\\game\\source\\boxing\\fe_psp\\aptextobj\\source\\Animation\\AnimationUtils.h`

Four routines share the line-74 `myPointer` assertion:

- `func_0022284C`
- `func_00222998`
- `func_00222AE4`
- `func_00222C4C`

### HUD / FUI

`E:\\muon\\boxing\\main\\game\\source\\boxing\\hud\\fui\\fuitccgame.cpp`

- `func_002412BC` — line **554**, assert `damageText`
- `func_002414B8` — line **623**, assert `layout`

### PocketDJ

`E:\\muon\\boxing\\main\\game\\source\\boxing\\pocketdj\\PocketDJFightNight.cpp`

Recovered source-attributed lifecycle anchors:

| Address | Evidence-backed interpretation | Source evidence |
| --- | --- | --- |
| `0x00295788` | probable PocketDJ player init/create | line 126, assert `!"pocketdj not inited!"` |
| `0x0029594C` | probable PocketDJ shutdown/destroy | complementary shutdown call path; clears player global |
| `0x0029598C` | **PocketDJ player/singleton getter** | leaf getter for global `0x00567124` |
| `0x00295E24` | **PocketDJ suspend** | line 182, assert `player`; called after literal suspend diagnostic |
| `0x00295EF0` | **PocketDJ resume** | line 225, assert `player`; called after literal resume diagnostic |

The containing PSP callback service routine is now directly named:

- `0x00341768` — **ServiceSceCallbacks**

It materializes all four diagnostics:

- `ServiceSceCallbacks() -> Suspending PocketDJ`
- `ServiceSceCallbacks() -> Unlocking volatile memory!`
- `ServiceSceCallbacks() -> Resuming PocketDJ`
- `ServiceSceCallbacks() -> Locking volatile memory!`

The suspend message is immediately followed by a call to `0x00295E24`; the
resume message is immediately followed by `0x00295EF0`. This makes the
suspend/resume semantics confirmed, not just inferred from code proximity.

## APT middleware source bands

Two full APT middleware paths remain in the ELF:

- `E:/MyWork/Perforce/depot/project/Apt/5.02.01-250/source/AptAuxEAGLREAL/AptAuxEAGLREAL.cpp`
- `E:/MyWork/Perforce/depot/project/Apt/5.02.01-250/source/AptAuxEAGLREAL/aptrealfont.cpp`

The first has 25 direct source-path xrefs across approximately
`0x003DDD78-0x003E1D9C`; the second has 9 across approximately
`0x003E2058-0x003E392C`.

This gives us a reliable middleware attribution band and prevents APT/EAGLREAL
support code from being mistaken for Fight Night gameplay logic.

## PSP import libraries

The debug ELF names these PSP libraries directly:

`Kernel_Library`, `InterruptManager`, `sceNetResolver`, `sceNetApctl`,
`sceNetInet`, `scePower`, `sceNetAdhocctl`, `sceNetAdhoc`, `sceMpeg`,
`sceAtrac3plus`, `sceAudio`, `sceSasCore`, `sceGe_user`, `sceCtrl`,
`sceSuspendForUser`, `UtilsForUser`, `ThreadManForUser`,
`SysMemUserForUser`, `StdioForUser`, `ModuleMgrForUser`,
`LoadExecForUser`, `IoFileMgrForUser`, `sceNet`, `sceWlanDrv`,
`sceUtility`, `sceRtc`, `sceUmdUser`, and `sceDisplay`.

## Function-boundary corrections

Three stale PocketDJ references were interior instructions, not function
entries:

- `0x00295738` is in the epilogue of the function beginning at
  `0x00295448`.
- `0x00295DD4` is inside the function beginning at `0x00295CD0`.
- `0x00295EA0` is inside the confirmed PocketDJ suspend function beginning at
  `0x00295E24`.

Any downstream evidence should use the corrected function starts.

## Provenance and confidence

- Full binary bytes are never committed.
- Addresses/string offsets are derived from the supplied debug ELF.
- Source-path xrefs were recovered from direct Allegrex address construction.
- Assert line numbers were recovered from the argument setup immediately
  preceding the debug/assert call.
- Function boundaries labeled *probable* were bounded conservatively from
  standard MIPS negative-stack prologues and surrounding epilogues.
- The machine-readable source of truth is
  `analysis/resources/debug-build-aip-dispatch.json`.
