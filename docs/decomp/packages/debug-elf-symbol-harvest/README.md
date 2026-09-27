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


## PocketDJ EATrax callback descriptor

The probable PocketDJ init/create routine at `0x00295788` constructs a
callback/config block at `sp+0x20..sp+0x5C` before the EATrax player is
created.

Function-pointer slots:

- `+0x20` -> `0x00295FD8`
- `+0x24` -> `0x00295FFC`
- `+0x28` -> `0x00296018`
- `+0x2C` -> `0x00296034`
- `+0x30..+0x3C` repeat the same four callbacks
- `+0x40` -> `0x00295CD0`
- `+0x44` -> `0x0029606C`
- `+0x48` -> `0x00296050`

The callback at `0x00295CD0` is a five-way switch. Its case-1 path invokes
the literal command `EATrax_GoToScreen` with `/_root` and `MAINMENU`.
The callback at `0x00296050` is a thin wrapper around `func_0026E674`; its
return value is consumed by `0x0029606C` as a two-bit 0..3 selector while
avoiding the current state. Exact public-facing names for these callbacks are
not promoted yet.

The descriptor also carries direct string/config pointers:

- `+0x4C`: `eatrax/`
- `+0x50`: `eavis`
- `+0x54`: `EATrax::Player`
- `+0x58`: `0.0f`
- `+0x5C`: `0x00064000`

After descriptor setup, the routine allocates `0x174` bytes, constructs the
player, stores the resulting pointer at global `0x00567124`, and performs the
source-attributed line-126 initialization assertion if the created player is
not valid.


## AuSpeechManager bank architecture

The debug build exposes the PSP speech system as three explicit bank families.
This is the first direct static bridge from gameplay state to the actual
commentary/announcer/training speech assets.

### Core functions

| Address | Evidence-backed role |
| --- | --- |
| `0x00137B34` | speech-manager singleton/factory path; allocates 0x1E8 bytes and calls the constructor |
| `0x0013AA94` | AuSpeechManager constructor |
| `0x00137BA0` | AuSpeechManager stream initialization; directly references the named `AuSpeechManager::InitStream()` failure diagnostic |
| `0x0013AC78` | main speech-bank initialization/setup path |
| `0x00137888` | public/request dispatch wrapper |
| `0x0013CCA4` | three-way speech-bank request router |
| `0x0013DDC4` | probable `AuSpeechManager_EvaluateTCC`; TCC gameplay-condition selector |

### Bank triples and category IDs

The initialization path passes three separate filename triples through the same
bank-loader helper at `0x0013A6D0`:

| Request category | Manager substructure | Data | Events | Header | Interpretation |
| ---: | --- | --- | --- | --- | --- |
| 0 | `+0x19C` | `comdat.big` | `comevt.evt` | `comhdr.big` | commentary |
| 1 | `+0x188` | `ancdat.big` | `ancevt.evt` | `anchdr.big` | announcer |
| 2 | `+0x1B0` | `trndat.big` | `trnevt.evt` | `trnhdr.big` | training |

The numeric routing is not inferred from file order. `0x0013CCA4` reads the
request's `+0x10` field and selects:

- `0` -> the `com*` bank and `manager+0x19C`
- `1` -> the `anc*` bank and `manager+0x188`
- `2` -> the `trn*` bank and `manager+0x1B0`
- values `>= 3` do not select one of these banks

Other request fields are used by the selected bank but remain conservatively
unnamed:

- `+0x00`: event/index-like value
- `+0x04`: additive offset/index after bank lookup
- `+0x0C`: 16-bit subtype/flag
- `+0x10`: confirmed three-way speech category selector

### TCC condition families

The large selector at `0x0013DDC4` has direct debug-string xrefs that name
five decision families:

- `TCC = MULTI KD`
- `TCC = POOR PERFORMANCE`
- `TCC = WASTED ENERGY`
- `TCC = BOXER DAMAGE`
- `TCC = BOXER RATING/STYLE`

The routine reads boxer/fight state and rating/stat values, derives event flags,
builds an event payload, and sends that payload through the generic event
dispatch layer. The exact expansion of the acronym `TCC` is not promoted
without further evidence, but its role as commentary/speech condition
selection is now directly bounded by the surrounding AuSpeechManager bank
architecture.

This materially changes the audio RE picture: FNR3 PSP does not expose only a
commentary enable/disable toggle. The debug executable preserves the bank
routing and multiple gameplay-context selectors that feed speech events.
