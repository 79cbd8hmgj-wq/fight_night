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

`0x0013DDC4` has direct debug-string xrefs that name five decision families:

- `TCC = MULTI KD`
- `TCC = POOR PERFORMANCE`
- `TCC = WASTED ENERGY`
- `TCC = BOXER DAMAGE`
- `TCC = BOXER RATING/STYLE`

Relocation-aware follow-up corrects the event identity: this routine does **not**
dispatch the generic event named `TCC`. It builds and dispatches the named
`NISAdvice` event. The `TCC = ...` strings are condition labels used while
constructing that advice payload. The exact expansion of the acronym `TCC`
remains unproven.

The actual named `TCC` event is emitted separately by the main AuSpeechManager
update routine at `0x0013B410`, with its dispatch site at `0x0013BBE0`.

This materially changes the audio RE picture: FNR3 PSP does not expose only a
commentary enable/disable toggle. The debug executable preserves explicit bank
routing plus separate `NISAdvice` and `TCC` event paths.


## Named event registry

The same relocation-aware pass resolves a contiguous event registry initialized
by `0x001106CC`.

Each static descriptor is an 8-byte pair:

`{ name pointer, 32-bit name hash }`

and is bound through `func_003E4A94` to an 8-byte event-handle object.
`func_003E5860` then dispatches a caller payload through that resolved handle.

The apparent pre-relocation handle addresses such as `0x00020FB0` are **not
literal code addresses**. Their PSP HI16/LO16 relocation records use program
segment 1 as the target base. With segment-1 vaddr `0x0058A8A8`, the NISAdvice
handle resolves to:

`0x0058A8A8 + 0x00020FB0 = 0x005AB858`

which lies in BSS.

The recovered registry includes:

| Runtime handle | Descriptor | Name | Hash |
| --- | --- | --- | --- |
| `0x005AB850` | `0x0055AAC8` | RefCountDown | `0x761C4C54` |
| `0x005AB858` | `0x0055AAD0` | **NISAdvice** | `0x08654C54` |
| `0x005AB860` | `0x0055AAD8` | OnplayAdvice | `0x38FE4C54` |
| `0x005AB868` | `0x0055AAE0` | **TCC** | `0x74184C54` |
| `0x005AB870` | `0x0055AAE8` | StartOfRound | `0x7A4F4C54` |
| `0x005AB878` | `0x0055AAF0` | RefClinch | `0x1DD04C54` |
| `0x005AB880` | `0x0055AAF8` | RefStoppage | `0x089E4C54` |
| `0x005AB888` | `0x0055AB00` | BlockedPunch | `0x20216F4F` |
| `0x005AB890` | `0x0055AB08` | BoxerDamage | `0x5EFA6F4F` |
| `0x005AB898` | `0x0055AB10` | CelebrationSequence | `0x39806F4F` |
| `0x005AB8A0` | `0x0055AB18` | LackOfAction | `0x36F06F4F` |
| `0x005AB8A8` | `0x0055AB20` | MissedPunch | `0x09A46F4F` |
| `0x005AB8B0` | `0x0055AB28` | PunchCombos | `0x0E526F4F` |
| `0x005AB8B8` | `0x0055AB30` | PunchLanded | `0x324F6F4F` |
| `0x005AB848` | `0x0055AB38` | Replay | `0x28D86F4F` |
| `0x005AB8C0` | `0x0055AB40` | UpdateStatus | `0x1FD36F4F` |
| `0x005AB8C8` | `0x0055AB48` | BoxerFatigue | `0x49406F4F` |
| `0x005AB8D0` | `0x0055AB50` | TauntingResult | `0x59AB6F4F` |
| `0x005AB8D8` | `0x0055AB58` | FeintingResult | `0x70046F4F` |
| `0x005AB8E0` | `0x0055AB60` | ClinchingResult | `0x13716F4F` |
| `0x005AB8E8` | `0x0055AB68` | Trapped | `0x32496F4F` |
| `0x005AB8F0` | `0x0055AB70` | BoxerRoundHistory | `0x1ED36F4F` |
| `0x005AB8F8` | `0x0055AB78` | CareerMode | `0x185A6F4F` |
| `0x005AB900` | `0x0055AB80` | Knockdown | `0x69746F4F` |
| `0x005AB908` | `0x0055AB88` | IllegalBlows | `0x738A6F4F` |
| `0x005AB910` | `0x0055AB90` | RAFightIntroFlyIn | `0x2F7621D9` |
| `0x005AB918` | `0x0055AB98` | RAFightIntroSegment4 | `0x1EA821D9` |
| `0x005AB920` | `0x0055ABA0` | RAFightIntroSegment5 | `0x05EA21D9` |
| `0x005AB928` | `0x0055ABA8` | RAFightResultSegment1 | `0x1B8521D9` |
| `0x005AB930` | `0x0055ABB0` | RAFightResultSegment2 | `0x324C21D9` |

### NISAdvice vs TCC correction

`0x0013DDC4` dispatches through the relocated `NISAdvice` handle
`0x005AB858`, with fallback registration using descriptor `0x0055AAD0`.
Its `TCC = MULTI KD`, `POOR PERFORMANCE`, `WASTED ENERGY`,
`BOXER DAMAGE`, and `BOXER RATING/STYLE` diagnostics therefore describe
conditions used to produce **NISAdvice**, not proof that this function is the
TCC-event producer.

The actual `TCC` event uses handle `0x005AB868`. The main AuSpeechManager
update path beginning at `0x0013B410` builds a three-word payload at
`sp+0xAC` and dispatches it at `0x0013BBE0`. The three words are directly
observed, but their semantic field names remain intentionally unresolved.


## AEMS-to-speech request ABI

The producer side of the AuSpeechManager request is now statically recovered.

During AuSpeechManager initialization, `0x00498260` installs
`0x00137888` as a callback into the generic AEMS/event subsystem. The
generic decoder at `0x0049A5C0` later constructs a request at `sp+0x10`
and invokes that callback directly.

The request is at least **0x20 bytes**:

| Offset | Recovered meaning |
| --- | --- |
| `+0x00` | event ID consumed by the selected speech bank |
| `+0x04` | relative byte offset within the event's canonical speech-data entry |
| `+0x08` | byte length/span of the decoded AEMS range |
| `+0x0C` | 16-bit subtype/flag |
| `+0x0E` | associated signed 16-bit source field |
| `+0x10` | bank category: 0=com, 1=anc, 2=trn |
| `+0x14` | AEMS-derived 16-bit field; semantics still open |
| `+0x18` | AEMS-derived byte field; semantics still open |
| `+0x1C` | first-request boolean; first emitted request gets bit 5 of source byte +0x0A, later requests get 0 |

The category field comes from a descriptor selected by `0x00497090`; it is
therefore assigned by the generic AEMS/event mapping before AuSpeechManager is
called.

### Byte-range decoder

`0x0049B480` is now bounded as a byte-range decoder.

Its input object uses:

- `+0x05` as entry count
- low 7 bits of `+0x04` to derive entry stride:
  `(value & 0x7F) + 2`
- `+0x07` to derive byte scale:
  `(value + 1) << 8`
- `+0x08` as the final/end position for the last entry
- variable-size entries beginning at `+0x0C`, each starting with a
  big-endian 16-bit position

For entry N it produces:

```text
start_bytes = entry[N].position_units * block_scale
length_bytes = next_position_bytes - start_bytes
```

For the final entry, the object-level `+0x08` value supplies the ending
position. The caller can additionally add source `+0x06 * block_scale` to
the start.

This proves request `+0x04` is a **relative byte offset** and request
`+0x08` is a **byte length**, not an abstract sample number.

### Final speech-file offset

The bank record's `+0x04` field is likewise a **base byte offset**. The bank
loader canonicalizes each event record name:

```text
name
-> strip "_Clone"
-> append ".dat"
-> lookup in comdat.big / ancdat.big / trndat.big
-> store returned base byte offset
```

AuSpeechManager computes:

```text
final_bank_byte_offset =
    event_record.base_data_offset +
    aems_request.relative_byte_offset
```

and sends the selected bank pathname plus that offset through
`0x00483AAC -> 0x004837A4 -> 0x004C242C/0x004C254C`.

The lower file/audio layer copies the pathname into its resource object and
stores the offset at object `+0x118`; the alternate path adjusts the same
offset while walking segmented file extents. This independently confirms the
byte-offset interpretation.


### Replay-handle ordering correction

The event initializer at `0x001106CC` is authoritative. It deliberately
registers `Replay` at raw handle `0x20FA0` / runtime `0x005AB848`,
*before* `RefCountDown` at raw `0x20FA8`. The normal increasing sequence
continues through `PunchLanded` at `0x21010`, then resumes with
`UpdateStatus` at `0x21018`.

Therefore event handles must be taken from the initializer's actual
handle/descriptor pairs, not computed by descriptor-table index alone.
