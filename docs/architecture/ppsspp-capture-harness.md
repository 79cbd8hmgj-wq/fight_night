# PPSSPP Runtime Capture Harness

## Purpose

The PPSSPP harness makes emulator-side reverse-engineering captures deterministic, attributable, and verifiable. It records the exact emulator binary, exact rebuilt ISO, controlled scenario, input trace, process outcome, produced artifacts, memory comparisons, and breakpoint evidence.

The harness does not assume undocumented PPSSPP command-line flags or a particular debugger transport. Launch arguments are supplied explicitly by the researcher after the selected PPSSPP build has been probed and its supported interface has been confirmed.

## Emulator discovery and probe

`discover_ppsspp()` resolves an executable in this order:

1. Explicit path supplied by the caller.
2. `PPSSPP_EXECUTABLE` from the selected environment.
3. Known headless or SDL executable names on the selected search path.

The selected path must be a regular executable file. `probe_ppsspp()` then records:

- resolved executable path;
- executable size and SHA-256;
- exact `--version` output and return code;
- exact `--help` output, hash, and return code;
- capability references found in the executable name or help output.

A probe is evidence about one exact binary. A capture refuses to run if that executable's hash changes afterward.

## Controlled input traces

`InputTrace` records a canonical, hash-stable sequence of PSP controller states. Each event contains:

- frame number;
- sorted, unique button names;
- signed analog X and Y values.

Frames must be strictly increasing. Unknown buttons, duplicate buttons, invalid analog values, and noncanonical ordering are rejected. The trace SHA-256 is embedded in the scenario and checked when the capture plan is constructed.

The trace format records intended deterministic input. Delivery to PPSSPP remains transport-specific and must be supplied by an explicit, verified launch or debugger adapter.

## Capture plans

A `CapturePlan` binds together:

- exact emulator probe;
- controlled scenario metadata;
- exact input trace;
- explicit process arguments;
- explicit environment additions;
- finite timeout;
- expected artifact paths;
- destination capture directory.

The only argument placeholders expanded by the generic runner are:

- `{iso}` — absolute path to the verified rebuilt ISO;
- `{capture}` — absolute path to the transaction's temporary capture directory.

Unresolved placeholders and NUL bytes are rejected. The generic harness does not invent PPSSPP flags.

## Transactional capture bundle

`run_capture()` verifies the current emulator and ISO hashes before launch. It writes into a temporary directory and atomically replaces the requested destination only after the process result and artifact inventory have been recorded.

A bundle contains:

```text
capture-plan.json
input-trace.json
stdout.log
stderr.log
capture-result.json
<declared capture artifacts>
```

The result records:

- plan, emulator, and ISO hashes;
- return code or timeout;
- stdout and stderr hashes;
- every declared artifact's presence, size, and hash;
- missing required artifacts;
- overall validity.

Nonzero exit, timeout, or a missing required artifact produces an invalid result without guessing success. Existing destinations require an explicit force operation and are replaced transactionally.

`verify_capture_bundle()` independently checks required files, log hashes, artifact paths, sizes, and hashes. It rejects symlinks and path traversal.

## Memory snapshots and comparisons

`MemorySnapshot` binds raw bytes to:

- snapshot ID;
- source revision;
- module;
- typed address.

`compare_memory()` supports aligned comparisons as:

- unsigned bytes;
- little-endian halfwords;
- little-endian words;
- little-endian single-precision floats.

Before/after comparisons require matching revision, module, base address, and size. When no initial snapshot exists, values are labeled `unknown_initial` rather than treated as changed or inferred.

## Breakpoint journal

`BreakpointJournal` stores normalized evidence for each breakpoint or watchpoint hit:

- typed breakpoint address;
- execute/read/write access classification;
- width and hit count;
- typed program counter;
- register values;
- reconstructed call stack;
- relevant memory snapshots;
- bounded researcher note;
- exact emulator hash and source revision.

Raw debugger transcripts remain local. Only normalized evidence should be committed.

## Required controlled scenarios

The wider reverse-engineering program should maintain reproducible saves or states for at least:

- exhibition fighter selection;
- opening bell;
- low stamina;
- stunned fighter;
- knockdown sequence;
- end of round;
- judges' decision;
- career hub;
- training selection;
- weight change;
- title fight;
- created-boxer save/load.

Each research checkpoint should answer one evidence question.

## Current boundary

The deterministic data model, process runner, memory diff, breakpoint journal, bundle verification, timeout handling, and hash guards are implemented and unit-tested.

A live PPSSPP executable is not installed in the current execution environment. Therefore this task does not claim:

- a live retail-game boot;
- a working PPSSPP debugger automation transport;
- deterministic controller injection into a real PPSSPP process;
- a reproduced watchpoint trace from Fight Night Round 3.

Those claims require an exact PPSSPP research build and a configured adapter using only interfaces confirmed for that build. The harness is designed to record and verify those captures once the transport is connected.
