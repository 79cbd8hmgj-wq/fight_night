# FNR3 in-game telemetry design

## User goal

The telemetry system must require no external monitor process during normal
play. The user should launch the modded Fight Night Round 3 ISO in PPSSPP (or,
where compatible, on PSP hardware), play Career Mode normally, and obtain a
telemetry log automatically.

The external PPSSPP Career Monitor design remains useful for targeted research
mode, but it is not the default user experience.

## Chosen architecture

Use a small injected PSP module:

```text
PSP_GAME/USRDIR/FNR3TLM.PRX
```

and a minimal, revision-guarded startup hook in `BOOT.BIN`.

Startup path:

```text
FNR3 BOOT.BIN
    -> proven startup hook
    -> sceKernelLoadModule("disc0:/PSP_GAME/USRDIR/FNR3TLM.PRX")
    -> sceKernelStartModule(...)
    -> normal game startup continues
```

The telemetry module then owns:

- log-buffer allocation;
- bounded memory sampling;
- runtime instrumentation hooks;
- event encoding;
- buffered file output;
- periodic/explicit flush;
- shutdown cleanup.

This keeps most instrumentation code out of the original executable and limits
the permanent BOOT.BIN modification to a small bootstrap trampoline.

## Why PRX instead of embedding the full logger in BOOT.BIN

The current overhaul builder supports guarded same-size byte patches only. A
full logger would require substantial code space, strings, state and file I/O.

A PRX gives us:

- independent code/data space;
- normal C/C++/assembly development;
- easier iteration;
- clear versioning;
- easier disable/remove path;
- reusable hooks for later overhaul systems;
- far less pressure to find a large executable code cave.

A BOOT-only fallback may be investigated if loading an added PRX proves
incompatible, but it is not the preferred design.

## Required build-pipeline change

The current `rebuild_image()` preserves the original ISO layout and only
supports same-length replacement inside existing files. It cannot add
`FNR3TLM.PRX`.

Add a second build mode for intentionally layout-changing mod images.

Suggested API:

```python
ModBuildPlan(
    revision_id=...,
    patches=(...),
    additions=(
        IsoAddition(
            source=...,
            destination="PSP_GAME/USRDIR/FNR3TLM.PRX",
        ),
    ),
)
```

Requirements:

- still verify the exact source ISO and workspace first;
- byte-guard every BOOT.BIN bootstrap patch;
- never mutate the reference ISO;
- emit a complete build report;
- record added-file hashes;
- deterministic ISO construction where practical;
- clearly distinguish a layout-preserving baseline build from a mod-image
  build.

## Telemetry output

Default path:

```text
ms0:/PSP/FNR3MOD/telemetry/
```

Session files:

```text
session-<counter>.tlm
session-<counter>.meta
```

The logger should not write into the game's normal savedata directory. Career
savedata remains independent from telemetry and can therefore be deleted,
copied or compared without mixing mod files into the save payload.

PPSSPP maps `ms0:` into its configured Memory Stick directory, so these files
will be directly accessible after play.

## File format

Use a compact binary journal during gameplay rather than text.

Header:

```text
magic      "F3TL"
version    u16
flags      u16
build_id   u32
session_id u32
```

Fixed event header:

```text
type       u16
size       u16
sequence   u32
tick       u64
```

Payload follows per event type.

Advantages:

- very low formatting overhead;
- bounded writes;
- deterministic parsing;
- no string-formatting dependency in hot paths;
- resilient recovery if a session ends unexpectedly.

A repository-side parser converts `.tlm` into JSON/JSONL after the session.

## Buffering

Do not call file I/O on every combat event.

Use an in-memory ring/staging buffer, initially 64 KiB.

Normal path:

```text
instrumented event
    -> append compact record to RAM buffer
    -> return to game
```

Flush when:

- buffer exceeds a high-water mark;
- a fight ends;
- Career transitions back to the hub;
- a save completes;
- an explicit shutdown hook runs;
- a low-frequency timer requests a flush.

Avoid synchronous file writes in punch/per-frame hooks.

If a flush fails, mark the session as degraded and keep gameplay running.
Telemetry must never intentionally crash or block the game.

## First telemetry events

Version 1 should be deliberately narrow and overhaul-focused.

### Session/lifecycle

- game/module startup;
- Career state/profile observed;
- fight-session creation;
- round start;
- round end;
- fight result;
- Career hub return;
- save begin/end where the boundary is proven.

### Known boxer/session state

- selected boxer IDs for both corners;
- venue;
- fight/session mode;
- proven fight-stat counters when sampled at low frequency or lifecycle
  boundaries.

### Career values

Seed only values with existing runtime evidence:

- money/bank;
- first-name buffer;
- last-name buffer;
- record/KO candidate fields, retaining candidate labels in the decoded output
  until resolved.

### Research hooks promoted into the game

When a safe runtime hook has been proven for an overhaul blocker, add compact
events for:

- stamina writer/input values;
- damage/stun writer/input values;
- knockdown/KO/TKO decision;
- AI action decision;
- round scoring/judging;
- training result;
- contract/progression updates.

Do not instrument every known function simply because it is available.

## Runtime hook mechanism

The telemetry PRX should install only revision-verified hooks.

Each hook definition records:

- runtime target address;
- expected original instructions;
- overwritten byte/instruction count;
- trampoline address;
- preserved registers;
- displaced instructions;
- continuation address;
- telemetry event type;
- confidence/provenance.

Hook installation must fail closed for a mismatched instruction sequence.

Pseudo-flow:

```text
verify target instructions
    -> build trampoline
    -> write jump/call patch
    -> flush data/instruction caches
    -> mark hook active
```

If verification fails, leave that hook disabled and record a diagnostic event.
Do not patch an unexpected build.

## Bootstrap hook

The only required BOOT.BIN patch for the base telemetry build is a startup
bootstrap.

Selection criteria:

- reached once during game initialization;
- before Career gameplay begins;
- after PSP module APIs are usable;
- not performance-critical;
- enough displaced instructions for a safe trampoline;
- caller/callee context fully understood;
- verified in ULUS10066-v1.00.

The hook must:

1. preserve all required game registers/state;
2. execute displaced instructions;
3. load/start `FNR3TLM.PRX`;
4. return to the original startup path;
5. tolerate module-load failure and continue the uninstrumented game.

No bootstrap address is to be committed as safe until the instruction-level
boundary is proven.

## PSP APIs

The bootstrap requires the existing module-management interface already
present in FNR3's PSP imports.

The telemetry PRX needs normal PSP user APIs for:

- module entry/start/stop;
- file open/write/close;
- directory creation;
- time/tick acquisition;
- memory/cache management where required for runtime patching.

Prefer normal imported PSP APIs over custom PPSSPP-only behavior so the same
instrumented build is not emulator-specific.

## Telemetry parser

Add repository-side:

```text
src/fnr3_re/telemetry.py
```

Responsibilities:

- validate header/version/build identity;
- stream-decode records;
- reject malformed/truncated lengths safely;
- retain unknown event types as opaque metadata rather than crashing;
- convert known events to normalized JSONL;
- calculate session summaries;
- optionally correlate candidate field changes.

CLI:

```text
fnr3-re decode-telemetry session-0001.tlm --jsonl session-0001.jsonl
```

## Configuration

Keep logging enabled by default for the development/overhaul build.

A tiny config file on the Memory Stick may later allow:

```text
enabled=1
level=normal
```

but version 1 should not depend on a config file. Missing configuration means
normal telemetry enabled.

Release builds can ship with telemetry disabled or omit the PRX entirely.

## Failure behavior

Telemetry is subordinate to gameplay.

On any logger/module/file/hook failure:

- do not abort FNR3;
- disable only the failed telemetry feature;
- preserve already-buffered evidence when safe;
- continue the original game path.

The bootstrap itself must similarly fall back to normal game startup if the PRX
cannot load.

## Implementation milestones

### Milestone 1: build and parser infrastructure

- add layout-changing mod ISO build support;
- add telemetry binary format definitions and Python decoder;
- add synthetic tests;
- add PRX source/build skeleton;
- no BOOT hook yet.

### Milestone 2: self-starting logger

- recover and prove a one-time startup hook;
- identify retail ModuleMgrForUser import stubs needed for load/start;
- add bootstrap trampoline;
- package `FNR3TLM.PRX` into the ISO;
- prove that booting the ISO automatically creates a telemetry session file.

This is the milestone that satisfies "boot the game and it works."

### Milestone 3: overhaul-critical probes

Add only high-value proven instrumentation:

1. fight lifecycle;
2. stamina;
3. damage/stun/KO/TKO;
4. AI decision loop;
5. judging;
6. career progression/save;
7. roster/division limits.

Each new probe requires instruction-level hook evidence before enabling it.

### Milestone 4: use telemetry to wire the overhaul

The same runtime hooks become candidate integration boundaries for the actual
overhaul replacement logic.

Where appropriate, replace:

```text
hook -> log -> original function
```

with:

```text
hook -> overhaul implementation -> optional log -> continuation
```

This means the telemetry project directly builds the runtime injection
infrastructure needed by the playable overhaul rather than creating a
throwaway debugger.

## Relationship to external Career Monitor

The earlier external Career Monitor remains valuable for discovering the first
safe writer/hook addresses because it can use PPSSPP breakpoints before the game
contains any injected code.

Once an address is proven, promote it into the in-game PRX.

Normal user workflow becomes only:

```text
boot FNR3 Overhaul ISO
play
copy/upload telemetry file when analysis is wanted
```
