# PSP Disassembly Toolkit Integration Design

Date: 2026-08-27

## Purpose

Integrate the standalone `79cbd8hmgj-wq/PSP-disassembly-tool` into the Fight Night Round 3 PSP reverse-engineering workflow as a reusable static-analysis evidence producer.

The Fight Night repository remains game-specific and evidence-first. The PSP toolkit remains a separate reusable project. Raw ISO contents, original executables, extracted assets, generated assembly, and other copyrighted payloads remain in the validated external workspace and are never added by this integration to Git.

## Locked toolkit baseline

The first supported toolkit baseline is:

- repository: `79cbd8hmgj-wq/PSP-disassembly-tool`
- revision: `b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a`
- package version: `0.9.0`
- completed scope: Phase 7G

This revision exposes the public APIs required by the adapter, including executable analysis, Allegrex/VFPU disassembly, relocated load views, module placement, module linking, NID support, and project generation.

The Fight Night integration must record the toolkit repository, revision, and package version in every normalized analysis manifest. A mismatched or provenance-unknown toolkit may be used only when explicitly allowed for exploratory local work; its results are not revision-locked evidence and must be labeled accordingly.

## Existing project constraints

The integration must preserve the existing Fight Night architecture:

1. `workspace/original/` is the authoritative byte-exact extracted image.
2. `workspace/working/` is for decoded, generated, or reconstructed analysis material.
3. `workspace/modified/` is reserved for intentional later edits.
4. Existing legacy root-level `BOOT.BIN`, `EBOOT.BIN`, archives, and assets are not authoritative inputs for new work.
5. Only tools, schemas, tests, reconstructed source, normalized evidence, and documentation may be newly committed.
6. Runtime addresses, module-relative addresses, ELF virtual addresses, file offsets, archive offsets, ISO offsets, and LBAs remain distinct types.
7. Static analysis cannot silently satisfy the repository's functional-reconstruction gate.

## Recommended architecture

Use an external-workspace adapter inside `fnr3-re`.

```text
validated Fight Night ISO
        |
        v
existing fnr3-re workspace builder
        |
        v
workspace/original/
        |
        v
fnr3-re PSP analysis adapter
        |
        +--> PSP-disassembly-tool public APIs
        |
        +--> full local analysis
        |      workspace/working/pspdisasm/
        |
        +--> normalized static evidence candidate
               workspace/manifests/pspdisasm-module-evidence.json
```

The adapter does not copy PSP-disassembly-tool source into `fight_night`, does not fork the toolkit, and does not treat the legacy committed game binaries as normal analysis inputs.

## Why the adapter consumes the extracted workspace

`fight_night` already has exact-image validation and a deterministic ISO workspace. Re-running a second independent ISO extraction path would create two competing authorities for file identity and offsets.

The adapter therefore consumes files already listed in `manifests/workspace.json`. This preserves the Fight Night revision lock, ISO LBA/offset metadata, and file hashes while allowing the PSP toolkit to analyze executable bytes through its public single-module APIs.

The integration will not use the toolkit's `generate_game_project()` as the primary entry point for this milestone because that API starts from an ISO/CSO image. The Fight Night workspace is the authoritative input boundary. Instead, the adapter orchestrates the toolkit's public executable/module APIs over the validated extracted files.

## CLI contract

Add a new command:

```bash
fnr3-re analyze-psp-modules /path/to/fnr3-workspace
```

Optional controls:

```bash
fnr3-re analyze-psp-modules /path/to/fnr3-workspace \
  --nid-db /path/to/psp_nids.csv \
  --allow-unpinned-toolkit
```

Default behavior is strict. The command must:

1. verify the workspace before analysis;
2. verify the locked Fight Night revision;
3. verify the PSP toolkit package version and, when available from installation provenance, the exact VCS revision;
4. refuse repository-root legacy executables as authoritative input;
5. discover executable candidates from the workspace manifest and validated file contents;
6. analyze candidates independently so one malformed or encrypted module cannot destroy the full run;
7. plan whole-game module placement for usable decrypted modules;
8. apply relocated load views consistently before address-sensitive disassembly/linking;
9. write detailed generated material only under `workspace/working/pspdisasm/`;
10. write a deterministic normalized evidence candidate under `workspace/manifests/`.

`--allow-unpinned-toolkit` permits exploratory analysis when exact toolkit provenance cannot be proven. The normalized manifest must then set `toolchain_revision_locked` to `false`, and the output cannot be used as confirmation evidence without a later locked rerun.

## Executable discovery

Candidate discovery is driven by the authoritative workspace manifest, not by repository files.

The first implementation supports:

- `PSP_GAME/SYSDIR/BOOT.BIN`;
- `PSP_GAME/SYSDIR/EBOOT.BIN`;
- `.PRX` files anywhere in the validated workspace;
- additional files whose content is recognized by the PSP toolkit as ELF/PRX/PSP executable containers.

The adapter deduplicates candidates by workspace path and SHA-256. Paths and hashes from the Fight Night workspace remain the primary identity; toolkit source names are secondary metadata.

Encrypted `~PSP` inputs remain recorded as `needs_decryption`. The adapter must not invent section, function, placement, or link evidence for an input that the toolkit cannot decrypt.

## Static analysis pipeline

For each usable module:

1. call the toolkit executable analyzer to obtain the normalized `ExecutableModel`;
2. preserve ELF/program/section/module/import/export/relocation structural records;
3. collect `ModulePlacementInput` records for all usable modules;
4. call `plan_module_placements()` once for the complete module set;
5. construct a relocated load view for relocatable modules using the planned load address;
6. run address-sensitive disassembly on the same planned address model;
7. run advanced analysis and data typing where supported;
8. run NID resolution when a database is supplied;
9. link imports/exports across modules using the same relocated address model;
10. write module-local generated output beneath `workspace/working/pspdisasm/modules/`.

The adapter must not implement a second PSP relocation engine, NID engine, or Allegrex decoder. Those remain toolkit responsibilities.

## Local output layout

```text
workspace/
├── original/
├── working/
│   └── pspdisasm/
│       ├── toolchain.json
│       ├── modules/
│       │   └── <safe-module-id>/
│       │       ├── executable.json
│       │       ├── placement.json
│       │       ├── disassembly.json
│       │       ├── advanced.json
│       │       └── typing.json
│       └── links/
│           ├── module_links.json
│           └── propagated_symbols.json
└── manifests/
    └── pspdisasm-module-evidence.json
```

Generated assembly, Splat workspaces, decompiler candidates, extracted resources, or other large derivative artifacts may be added beneath `workspace/working/pspdisasm/` later, but they remain local and ignored.

## Normalized evidence manifest

`workspace/manifests/pspdisasm-module-evidence.json` is the only first-milestone artifact designed for later promotion into Git.

It must be deterministic JSON with sorted keys, fixed indentation, UTF-8, and a terminal newline.

Top-level fields include:

- Fight Night revision ID and reference ISO SHA-256;
- workspace manifest hash;
- toolkit repository, package version, expected revision, observed provenance, and lock status;
- analysis timestamp exclusion: no wall-clock timestamps are written, preserving deterministic output;
- module inventory;
- placement inventory;
- cross-module link summary;
- warnings and unsupported/encrypted modules.

Each module record includes:

- workspace path;
- SHA-256 and file size;
- ISO LBA and ISO byte offset from the authoritative workspace manifest;
- toolkit input/executable kind;
- decryption state;
- ELF type and entry point where available;
- section and program-header structural summary;
- import/export/NID summary;
- relocation-family summary;
- placement kind, load address, original image base, image size, toolkit confidence, runtime-address-claim flag, and placement evidence;
- function/symbol/reference counts;
- warning list.

The manifest should summarize functions and symbols by identity/address/count in the first milestone rather than embedding megabytes of assembly text.

## Evidence and confidence mapping

Toolkit confidence and Fight Night evidence confidence are different concepts and must never be conflated.

`placement_confidence=0.95` from PSP-disassembly-tool means the toolkit has strong evidence for its placement policy. It does not satisfy Fight Night's `PROBABLE` or `CONFIRMED` semantic evidence requirements by itself.

Rules:

- exact parsed structural facts are stored as structural records, not promoted semantic claims;
- inferred functions, globals, data types, call relationships, and runtime placements begin as static-analysis candidates unless stronger Fight Night evidence already exists;
- toolkit numeric confidence is preserved in a separate `tool_confidence` field;
- `runtime_address_claim=true` is preserved as toolkit provenance, not translated automatically into a Fight Night confirmation label;
- a runtime base becomes `PROBABLE` or `CONFIRMED` only through the repository's existing PPSSPP/runtime or deterministic reconstruction standards;
- imported static evidence can narrow runtime experiments but cannot replace them.

## Address discipline

Every normalized address-bearing record identifies its address type explicitly.

At minimum the schema distinguishes:

- `iso_lba`;
- `iso_byte_offset`;
- `elf_file_offset`;
- `elf_vaddr`;
- `module_relative_vaddr`;
- `runtime_address`;
- `archive_member_offset` when later applicable.

Conversions are emitted only when the adapter has the exact revision-locked source module and the required mapping evidence. The adapter must never overwrite a module-relative address with a runtime address in place.

## Relationship to the existing tracked module map

The first integration does not automatically rewrite `analysis/modules/tracked-module-map.json`.

Instead it produces the normalized evidence candidate described above. This prevents a large static-analysis run from silently replacing manually curated or runtime-supported evidence.

A later explicit promotion step may merge accepted fields into the tracked module map after review. The promotion logic must prefer stronger existing evidence over weaker static inference and must preserve contradictory observations rather than hiding them.

This separation is intentional: analysis generation and evidence acceptance are different operations.

## Toolchain dependency model

`pspdisasm` is an optional research dependency, not a mandatory runtime dependency of every `fnr3-re` command.

The implementation should add a dedicated optional dependency group pinned to the Phase 7G Git revision. Normal workspace, revision, codec, rebuild, save, and PPSSPP tooling must continue working without the PSP disassembly extra installed.

If the optional dependency is absent, `analyze-psp-modules` exits with a concise installation instruction and no partial output.

## Error handling

The command is transactional at the run level.

- Build analysis in a temporary sibling directory.
- Do not replace the prior `working/pspdisasm/` result until the new normalized run completes.
- A malformed secondary module is recorded as failed and does not abort unrelated modules.
- Failure of the selected boot module, workspace verification, revision verification, or toolchain verification aborts the run.
- Encrypted modules are successful inventory records with `needs_decryption`, not parser failures.
- Path traversal, symlink escape, or manifest/file hash mismatch aborts the run.
- The final evidence manifest records deterministic warnings in stable order.

## Copyright and repository safety

No new test may use Fight Night executable bytes, extracted archive members, assets, saves, RAM dumps, screenshots, or audio.

Tests use synthetic ELF/PRX fixtures constructed specifically for the repository test suite. Generated local analysis paths must be covered by ignore rules if they can appear under a developer checkout.

The integration never stages, copies, or commits anything from `workspace/original/` or `workspace/working/`.

## Testing strategy

Implementation is test-driven.

Required test groups:

### Workspace/input tests

- rejects an unverified workspace;
- rejects a wrong revision;
- refuses legacy repository-root `BOOT.BIN`/`EBOOT.BIN` as authoritative inputs;
- resolves candidates only from the workspace manifest;
- detects manifest/file hash drift;
- prevents symlink/path escape.

### Toolchain tests

- clear failure when `pspdisasm` is absent;
- accepts the pinned package/revision provenance;
- rejects mismatched provenance in strict mode;
- allows an explicitly unpinned exploratory run while marking evidence unlocked.

### Analysis tests

- synthetic fixed `ET_EXEC` module preserves fixed placement;
- synthetic relocatable boot receives evidence-backed placement;
- secondary relocatable PRX receives analysis-only placement;
- stricter later `PT_LOAD` alignment is honored;
- encrypted synthetic PSP container is isolated as `needs_decryption`;
- malformed secondary module does not destroy valid module analysis;
- cross-module import/export linking uses relocated addresses consistently.

### Evidence tests

- deterministic byte-identical manifest across repeated runs;
- explicit address types are present;
- toolkit confidence remains separate from Fight Night confidence;
- no assembly bodies or original bytes leak into the normalized manifest;
- output ordering is stable;
- existing manually curated module map is not modified by analysis generation.

### Regression gate

All existing `fnr3-re` tests, Ruff checks, and strict mypy checks continue to pass.

## First success criterion

The integration milestone is complete when a developer with the exact ULUS10066 v1.00 ISO can:

```bash
python tools/build_reference_workspace.py "/path/to/Fight Night Round 3 (USA).iso" /local/fnr3-workspace
fnr3-re analyze-psp-modules /local/fnr3-workspace
```

and receive:

1. a verified local PSP static-analysis workspace;
2. deterministic module placement/linking output;
3. a normalized static-evidence manifest tied to the exact Fight Night revision and exact PSP toolkit baseline;
4. no new copyrighted game payloads in Git;
5. no automatic claim that static disassembly has satisfied the Fight Night functional-reconstruction gate.

The immediate research payoff is to replace unresolved static module-placement gaps, such as `runtime_base: null`, with explicit toolkit placement candidates and evidence that can then be confirmed or rejected through the existing PPSSPP runtime harness.

## Non-goals for this milestone

This integration does not:

- add gameplay or overhaul behavior;
- decrypt encrypted retail PSP modules;
- reconstruct every Fight Night function into C;
- auto-confirm semantic function names from strings or decompiler output;
- modify the existing no-change rebuild pipeline;
- replace the PPSSPP runtime evidence harness;
- automatically overwrite curated Fight Night evidence;
- add game-specific proprietary archive parsers to PSP-disassembly-tool;
- commit generated Splat, assembly, resource, or decompiler payloads.
