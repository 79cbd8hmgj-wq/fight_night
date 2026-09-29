# FNR3 Career Monitor design

## Goal

Add a long-running PPSSPP telemetry mode that records normalized, revision-locked
Fight Night Round 3 Career Mode evidence while the user plays normally.

The monitor must be useful for overhaul reverse engineering without changing
gameplay behavior by default. It should turn normal play into structured
runtime evidence: known career-field changes, function hits, selected register
context, bounded memory diffs, fight/career lifecycle markers, and candidate
unknown fields.

The initial target is ULUS10066-v1.00 and the repository's existing verified
PPSSPP debugger bundle.

## Existing foundation

The repository already provides:

- `PpssppDebuggerClient` with loopback-only WebSocket transport, ticket
  correlation, unsolicited-event queuing, register reads, bounded memory reads,
  execution breakpoints, resume, and backtraces;
- an identity-locked PPSSPP bundle and SDL/headless launch wrappers;
- revision/workspace/ISO verification;
- normalized runtime-evidence conventions from Task 9E;
- typed address/provenance models;
- existing controlled-career runtime findings.

The Career Monitor extends these pieces rather than creating a separate
debugger implementation.

## Modes

### Play mode

Default mode. Designed to remain usable while Career Mode is played normally.

Use:

- periodic bounded memory sampling for known/candidate career regions;
- log-only execution breakpoints on proven functions;
- PPSSPP's spontaneous `log` WebSocket events;
- diff-only journal output;
- no pausing breakpoints;
- no register-write breakpoints;
- no broad memory watchpoints.

The game should not be modified by the monitor.

### Research mode

Explicit opt-in mode for short targeted investigations.

Adds:

- memory change/read/write breakpoints;
- optional pausing execution breakpoints;
- register/backtrace capture at a hit;
- interpreter-mode launch when memory/register breakpoint reliability is
  required.

Research mode is for questions such as "which instruction writes stamina?" and
is not the normal all-session Career logger.

## PPSSPP debugger extensions

Extend `src/fnr3_re/ppsspp_debugger.py` without breaking existing Task 9E
callers.

### Execution breakpoints

Add a richer helper equivalent to:

```python
add_exec_breakpoint(
    address,
    *,
    pause=True,
    log=False,
    condition=None,
    log_format=None,
)
```

Existing `add_exec_breakpoint(address)` behavior remains equivalent to
`pause=True, log=False`.

PPSSPP supports `cpu.breakpoint.add` with independent `enabled` (pause) and
`log` controls, plus `condition` and `logFormat`. The Career Monitor uses
`enabled=False, log=True` for passive function probes.

### Memory breakpoints

Add:

- `add_memory_breakpoint(...)`
- `update_memory_breakpoint(...)`
- `remove_memory_breakpoint(...)`
- optional list helpers for cleanup/verification.

Expose read/write/change, pause/log, condition, and log-format parameters.

Do not use memory breakpoints in default play mode. PPSSPP documents JIT
limitations for memory breakpoints, so research mode should force or require
the interpreter when these probes are active.

### Event polling

Add a bounded nonblocking/short-timeout event primitive so one owner loop can
service both debugger requests and unsolicited events.

The client already queues unsolicited events by name. The new primitive should
support at least:

- `log`
- `cpu.stepping`
- game/lifecycle events that are already emitted by PPSSPP

without introducing a second socket-reading thread.

PPSSPP broadcasts logs as spontaneous JSON events named `log` with timestamp,
header, message, level, and channel. Log-only breakpoint output therefore can
be consumed without pausing emulation.

## Monitor profile

Add a revision-locked machine-readable profile, initially:

`analysis/runtime/career-monitor-ulus10066.json`

The profile contains only bounded evidence targets, each with confidence and
provenance.

Suggested target kinds:

- scalar field;
- fixed string/buffer;
- bounded memory region;
- execution probe;
- memory probe (research-only);
- lifecycle anchor.

Each target records:

- id;
- address type and address/expression;
- width/type;
- sampling cadence or trigger;
- semantic label if proven;
- confidence;
- evidence source;
- whether changes may be promoted automatically or must remain unknown.

Unknown/candidate addresses must remain explicitly candidate. The monitor may
never promote a semantic name merely because a value changes in a plausible
way.

## Initial ULUS10066 profile

Seed only evidence already recovered in this project.

Career runtime fields from the controlled career captures:

- bank at runtime `0x08D98574`;
- last-name buffer at `0x08D9AA42`;
- first-name buffer at `0x08D9AA62`;
- record/KO candidates at `0x08D98504` and `0x08D98506`, retaining
  candidate labels until their distinction is proven.

Also seed proven executable-side anchors where runtime relocation can be
resolved safely:

- fight-session singleton accessor;
- boxer-selection setter;
- venue/session-mode setters;
- fight-stat accessor;
- known save/load functions;
- known career/training handlers as they become proven.

Do not hardcode speculative function names.

## Monitor engine

Add `src/fnr3_re/career_monitor.py`.

Use a single deterministic event loop.

Responsibilities:

1. verify revision, workspace, ISO, bundle and profile;
2. launch PPSSPPSDL through the verified bundle or attach only to an explicitly
   verified local debugger;
3. install passive probes;
4. sample bounded fields/regions on monotonic deadlines;
5. consume spontaneous log/lifecycle events;
6. decode only known-safe log marker formats;
7. emit normalized events only when something changes or a probe fires;
8. periodically checkpoint summary state;
9. remove probes and close the debugger cleanly on exit.

No full 32 MiB RAM polling.

## Passive breakpoint log format

Career Monitor-owned log breakpoints should use a unique prefix so PPSSPP's
ordinary emulator logs are not mistaken for telemetry.

Example:

```text
FNR3CM|fight_session_ctor|pc={pc}|a0={a0}|a1={a1}|ra={ra}
```

The parser accepts only the exact monitor prefix and expected key set for that
probe. Unrecognized log lines stay diagnostics, not evidence.

High-frequency functions should not receive log-only breakpoints in play mode;
the PPSSPP log broadcaster has a bounded ring buffer and can report dropped log
messages if a source produces more entries than the WebSocket loop can drain.

## Sampling

Default play-mode cadence should be low overhead, configurable per target.

Recommended starting policy:

- proven scalar fields: 4 Hz;
- short strings/buffers: 1 Hz;
- small candidate regions: 1 Hz;
- larger bounded snapshots: only on lifecycle/probe triggers.

Keep the previous value in memory and emit an event only on change.

For candidate regions, compute aligned byte/halfword/word changes through the
existing memory comparison utilities rather than recording whole raw dumps in
the normalized journal.

## Event model

Add immutable normalized event dataclasses.

Minimum event families:

- `session_start`
- `session_end`
- `field_change`
- `function_hit`
- `memory_probe_hit`
- `region_diff`
- `save_or_state_event`
- `diagnostic`

Every evidence event contains:

- monotonic sequence number;
- wall-clock timestamp;
- source revision;
- exact PPSSPP/bundle identity;
- event type;
- target/probe id;
- typed address where relevant;
- previous/new value or bounded register context;
- confidence/provenance;
- whether the semantic interpretation is confirmed or candidate.

Raw PSP memory bytes are local-only unless a separate explicit export is
requested.

## Output

Default output:

```text
workspace/working/runtime/career-monitor/<session-id>/
  session.json
  events.jsonl
  summary.json
  diagnostics.log
  local-raw/
```

`local-raw/` remains untracked and can contain optional temporary bounded raw
snapshots.

Repository-safe promotion is a separate operation. A Career Monitor run must
not automatically commit gameplay/save/runtime payloads.

A later command can promote reviewed normalized findings into
`analysis/runtime/` evidence.

## Correlation engine

Add `src/fnr3_re/career_correlation.py` after the basic monitor is working.

The first version should be deterministic, not ML-based.

For each candidate address/field, track:

- number of observed changes;
- which lifecycle/probe events bracketed the change;
- persistence across later samples;
- correlation with already-known fields;
- whether it changes only during UI/transient periods;
- whether the same change recurs across multiple sessions.

Example classifications:

- persistent career-state candidate;
- contract-correlated candidate;
- training-correlated candidate;
- fight-result-correlated candidate;
- ranking/progression candidate;
- transient UI/timer/noise candidate.

Correlation never upgrades semantics to CONFIRMED automatically.

## CLI

Add:

```text
fnr3-re monitor-career WORKSPACE \
  --bundle BUNDLE \
  --iso ISO \
  --mode play \
  [--profile analysis/runtime/career-monitor-ulus10066.json] \
  [--session-id ID] \
  [--json]
```

Research mode:

```text
fnr3-re monitor-career WORKSPACE \
  --bundle BUNDLE \
  --iso ISO \
  --mode research \
  --research-target stamina
```

The first implementation should launch the verified SDL build so the user can
play normally. A later attach mode may be added only if it can preserve the
same identity/revision guarantees.

## Testing

Unit tests must not require a commercial ISO.

Use fake debugger transports/clients to test:

- log-only execution breakpoint request shape;
- memory breakpoint request shape;
- unsolicited `log` event queuing;
- bounded polling and diff suppression;
- field/string decoding;
- journal ordering;
- candidate/confirmed provenance preservation;
- cleanup after exceptions;
- profile validation;
- high-frequency log-drop diagnostics;
- deterministic correlation classifications.

Add one environment-gated live integration test using the same external
reference inputs already required by the PPSSPP runtime harness.

## Implementation sequence

### Milestone 1 — passive logger

Implement debugger helpers, profile schema/loader, monitor loop, JSONL journal,
known-career-field polling and passive function probes.

Success criterion: the user can play an ordinary Career session and obtain a
valid session containing known field changes and function hits without
interruption.

### Milestone 2 — targeted research probes

Add memory breakpoints, interpreter research mode, register/backtrace capture,
and bounded triggered snapshots.

Success criterion: given a candidate runtime field, the monitor can identify
the instruction/function that changes it without requiring manual savestate
comparison.

### Milestone 3 — automatic correlation

Add persistent/transient filtering and action-correlated candidate ranking.

Success criterion: repeated Career sessions produce a shortlist of unknown
fields grouped by contract/training/fight-result/progression correlation.

## Relationship to the overhaul

This is reverse-engineering infrastructure, not a side project.

The monitor's highest-priority use is to close the blockers that prevent
`config/overhaul/alpha1/build_plan.json` from containing real PSP patches:

- fight lifecycle;
- stamina;
- damage/stun/KO/TKO;
- AI decision loop;
- judging;
- career serializer/state;
- roster/save limits.

Audio/commentary probes are intentionally lower priority unless they become
necessary for a concrete overhaul feature.
