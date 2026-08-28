# Task 9E Runtime Recovery Design

## Purpose

Restore a reproducible live Fight Night Round 3 runtime path for Checkpoint 9E without requiring the monolithic retail ISO to be re-uploaded or re-provisioned for every capture.

The repository already contains the extracted game payload that was used during earlier reverse-engineering work. The PPSSPP debugger bundle is treated as the known-good runtime implementation for this experiment. The recovery work therefore focuses on rebuilding a bootable temporary PSP runtime image from the repository payload, generating the save/state artifacts needed by Task 9E, and feeding those artifacts into the already-merged dual-control runtime adapter.

## Scope

This design changes only the Fight Night runtime preparation path used by Task 9E and later title-specific PPSSPP experiments.

It does not reopen the general PSP Disassembly Toolkit roadmap, redefine the locked retail revision, or weaken the existing Task 9E semantic evidence gate.

## Locked identity

The canonical retail identity remains:

- revision: `ULUS10066-v1.00`
- disc ID: `ULUS10066`
- disc version: `1.00`
- PSP system version: `2.60`
- title: `EA SPORTS™ FIGHT NIGHT Round 3`
- retail ISO size: `1137737728`
- retail ISO SHA-256: `b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2`
- `BOOT.BIN` SHA-256: `906f0c019ede4cd5d845272dfffe8291e45ce3da948c8e0607a61138854086f9`

The retail ISO hash remains provenance evidence. A reconstructed runtime image is not required to match the retail ISO byte-for-byte because Task 9E observes save/load code execution rather than physical UMD sector layout.

## Primary design decision

Task 9E gains a second accepted game-source mode:

1. **retail ISO mode** — existing behavior, requiring the exact locked retail ISO;
2. **repository runtime-image mode** — new behavior, producing a deterministic temporary ISO from a committed repository payload manifest.

The two modes share the same revision, executable, PPSSPP bundle, breakpoint plan, payload-lifetime contract, save/state capture logic, and evidence normalization.

Repository runtime-image mode never promotes the reconstructed ISO hash to the retail ISO identity. Evidence records both the locked retail provenance identity and the actual runtime-image SHA-256 used for the capture.

## Repository payload manifest

A new committed manifest defines exactly which repository files are retail game payload and where they belong in the PSP disc filesystem.

Proposed path:

```text
config/runtime/ulus10066-repository-payload.json
```

The manifest contains:

- schema version;
- revision ID;
- locked `BOOT.BIN` SHA-256;
- required repository source path;
- destination PSP disc path;
- expected byte size;
- expected SHA-256;
- file role such as executable, game data, metadata, padding, or generated metadata.

The manifest is an explicit allowlist. Runtime image creation must not infer payload membership by scanning arbitrary repository files or by excluding known source-code directories. This prevents docs, tests, analysis outputs, tooling, or later mod files from silently entering the disc image.

The initial manifest is derived from the currently committed extracted Fight Night payload and the already-confirmed retail inventory. Runtime preparation fails if a listed source file is missing, symlinked, wrong-sized, or hash-mismatched.

## Disc filesystem materialization

The temporary disc tree uses normal PSP locations:

```text
PSP_GAME/
  PARAM.SFO
  SYSDIR/
    BOOT.BIN
    EBOOT.BIN
  USRDIR/
    ...Fight Night game payload...
```

Repository files that correspond to retail `USRDIR` content are copied exactly as bytes into `PSP_GAME/USRDIR` according to the manifest.

`BOOT.BIN` and `EBOOT.BIN` are copied into `PSP_GAME/SYSDIR` and are identity-checked before image creation.

Small PSP metadata files that are not currently retained as standalone repository payload may be generated deterministically only when all of their semantic fields are already locked by committed revision evidence. Generated metadata is described explicitly in the runtime payload manifest and receives its own deterministic SHA-256 in the runtime-image report.

Generated metadata must not be presented as byte-identical retail metadata unless an exact retail copy and hash are available.

## Runtime ISO builder

A Fight Night-specific runtime image builder creates a temporary ISO9660 PSP image from the materialized disc tree.

Properties:

- deterministic file ordering;
- deterministic timestamps or zero-normalized timestamps where supported;
- fixed volume identifier for the reconstructed runtime image;
- no network access;
- no mutation of repository payload files;
- no output inside tracked repository paths by default;
- complete input/output hash report;
- transactional output replacement;
- symlink and traversal rejection.

The builder does not attempt to reproduce original LBAs, original directory-record byte layout, UMD padding, or the retail ISO SHA-256. Exact-sector reconstruction remains a separate concern from Task 9E runtime execution.

## Runtime-image identity report

Each reconstructed image has a normalized report containing:

- revision ID;
- retail provenance ISO SHA-256;
- repository payload manifest SHA-256;
- `BOOT.BIN` SHA-256;
- `EBOOT.BIN` SHA-256;
- generated metadata hashes;
- every included source path and destination path;
- actual runtime ISO byte size;
- actual runtime ISO SHA-256;
- builder version/schema;
- deterministic-build flag.

Task 9E records the actual runtime ISO hash from this report while retaining the retail provenance hash separately.

## PPSSPP bundle role

The pinned PPSSPP debugger bundle remains the required runtime implementation.

The existing bundle verifier continues to lock:

- PPSSPP revision;
- `PPSSPPSDL` SHA-256;
- `PPSSPPHeadless` SHA-256;
- bundled support executable identities;
- local debugger configuration;
- debugger host and port expectations.

Runtime recovery does not replace or weaken bundle verification.

## Runtime bootstrap

A new bootstrap workflow prepares the exact runtime artifacts Task 9E needs from the reconstructed image.

The bootstrap has two responsibilities:

1. boot the reconstructed Fight Night image in the verified PPSSPP bundle;
2. produce a real Fight Night savedata slot and a compatible `.ppst` state representing a successful load path suitable for the existing Task 9E breakpoint sequence.

The bootstrap may use the repository-owned PPSSPP debugger client and controlled input delivery. It must use PPSSPP's own runtime save/state mechanisms rather than synthesizing Fight Night savedata bytes or fabricating a `.ppst` container.

The resulting save slot and state remain local runtime artifacts and are never committed.

## Savedata routing correction

The current Task 9E adapter hashes the selected savedata slot but does not explicitly redirect PPSSPP to a per-control memstick root. That is insufficient for the corrupted-copy experiment.

Runtime recovery therefore introduces an explicit per-control PPSSPP memstick root:

```text
successful/
  PSP/SAVEDATA/<slot>/...
corrupted/
  PSP/SAVEDATA/<slot>/...
```

Each control launches PPSSPP with a configuration/root that resolves `ms0:/PSP/SAVEDATA/<slot>` to that control's own copied memstick directory.

The successful control receives the untouched bootstrap save.

The corrupted control receives the deterministic one-byte mutation already defined by Task 9E.

The adapter must verify after launch that the runtime is using the intended memstick root before interpreting any divergence as save-validation evidence.

This removes the existing risk that both controls silently read the same PPSSPP save directory.

## State handling

The bootstrap-created `.ppst` is tied to:

- reconstructed runtime-image SHA-256;
- PPSSPP bundle identity;
- savedata inventory identity;
- revision ID.

Task 9E preflight verifies those identities before use.

A state created for one runtime-image hash must not be silently reused with a different reconstructed image.

## Task 9E preflight changes

`Task9ECaptureInputs` is extended to describe the runtime image provenance rather than assuming `iso_sha256 == retail_iso_sha256`.

For retail ISO mode, existing exact retail validation remains unchanged.

For repository runtime-image mode, preflight requires:

- valid locked revision;
- exact locked `BOOT.BIN` identity;
- valid repository payload manifest;
- valid runtime-image report;
- actual ISO hash matching the runtime-image report;
- runtime-image report retail provenance matching the locked revision;
- verified PPSSPP bundle;
- compatible bootstrap state;
- explicit savedata slot;
- explicit per-control memstick root.

The Task 9E plan and payload-lifetime artifacts remain authoritative and unchanged unless runtime evidence later justifies a separate semantic update.

## CLI shape

A new preparation command is introduced for repository runtime-image mode:

```bash
fnr3-re prepare-fnr3-runtime REPOSITORY_ROOT OUTPUT_ROOT \
  --bundle BUNDLE \
  --payload-manifest config/runtime/ulus10066-repository-payload.json
```

It produces local runtime artifacts under `OUTPUT_ROOT`, including the reconstructed ISO and runtime-image report.

A bootstrap command prepares save/state inputs:

```bash
fnr3-re bootstrap-save-9e RUNTIME_ROOT \
  --bundle BUNDLE
```

The existing `capture-save-9e` command gains runtime-image provenance support and per-control memstick routing. Retail ISO mode remains supported for users who have the exact original image locally.

No command uploads, commits, or transmits the reconstructed ISO, save slot, state, or raw runtime capture.

## Evidence model

Existing Task 9E normalized evidence remains the semantic boundary.

Repository runtime-image captures add provenance fields for:

- source mode;
- retail provenance ISO SHA-256;
- runtime ISO SHA-256;
- runtime payload manifest SHA-256;
- bootstrap state SHA-256;
- savedata inventory SHA-256 or normalized inventory;
- memstick-root identity for each control without recording machine-specific absolute paths.

Raw runtime files, local paths, save bytes, state bytes, ISO bytes, screenshots, debugger transcripts, and broad memory dumps remain excluded from committed evidence.

## Failure handling

Runtime preparation fails closed on:

- missing manifest source file;
- unexpected source hash or size;
- symlinked payload input;
- invalid PSP destination path;
- duplicate destination path;
- metadata generation from unlocked fields;
- nondeterministic rebuild result from identical inputs;
- wrong `BOOT.BIN` identity;
- wrong revision provenance;
- wrong PPSSPP bundle identity;
- state/runtime-image mismatch;
- savedata mutation of the source slot;
- inability to prove per-control memstick routing;
- missing expected Task 9E breakpoint sequence.

A failed preparation or capture must not replace a previously valid runtime report or normalized evidence pair.

## Testing strategy

### Unit tests

Cover:

- strict payload-manifest parsing;
- safe source/destination path validation;
- duplicate destination rejection;
- source size/hash validation;
- deterministic metadata generation;
- deterministic ISO construction from synthetic fixtures;
- runtime-image report validation;
- retail provenance versus runtime-image hash separation;
- per-control memstick root generation;
- successful/corrupted save routing;
- state/runtime-image identity checks;
- CLI error handling;
- raw-artifact exclusion from normalized evidence.

### Repository integration tests

Use the committed Fight Night payload manifest to verify every listed repository source exists and matches its expected size/hash.

These tests do not create or publish a complete copyrighted runtime ISO in CI artifacts.

### Live environment-gated test

When a verified PPSSPP bundle is available locally, the live gate may:

1. build the runtime ISO into temporary storage;
2. boot Fight Night;
3. prepare or reuse an identity-matched bootstrap save/state;
4. launch the successful and corrupted controls with separate memstick roots;
5. require the fixed Task 9E breakpoint sequence;
6. write only normalized Task 9E evidence.

A skipped live gate remains non-evidence.

## Non-goals

This change does not:

- reproduce the retail ISO SHA-256 from extracted files;
- recover original UMD padding or exact LBAs;
- store the reconstructed ISO in Git;
- store Fight Night savedata or `.ppst` states in Git;
- infer new save-field semantics from static code alone;
- redesign the general PSP toolkit;
- replace the PPSSPP debugger bundle;
- claim successful Task 9E runtime evidence until a real live capture completes.

## Success criteria

Runtime recovery is complete when:

1. the repository payload manifest identity-locks the extracted Fight Night files needed to boot;
2. those files deterministically produce a temporary bootable PSP runtime image;
3. the verified PPSSPP bundle boots that image;
4. a real Fight Night savedata slot and compatible `.ppst` can be prepared locally;
5. successful and corrupted controls are routed through separate verified memstick roots;
6. the existing Task 9E breakpoint/callback capture executes against those controls;
7. normalized evidence records the reconstructed runtime-image provenance without confusing it with the retail ISO identity;
8. no ISO, save, state, or raw runtime payload is committed to the repository.
