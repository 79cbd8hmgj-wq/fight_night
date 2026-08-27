# PSP static-analysis workflow

This workflow connects the Fight Night Round 3 reverse-engineering repository to the standalone PSP Disassembly Toolkit without making that toolkit part of the core project or weakening the project's evidence rules.

## Supported baseline

Fight Night analysis is revision-locked to:

- Fight Night Round 3 PSP USA revision: `ULUS10066-v1.00`
- Reference ISO SHA-256: `b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2`
- PSP Disassembly Toolkit repository: `https://github.com/79cbd8hmgj-wq/PSP-disassembly-tool.git`
- PSP Disassembly Toolkit revision: `b3a07f4d0880b7933f87a9557b5e0aa3f364fa5a`
- PSP Disassembly Toolkit package version: `0.9.0`

The toolkit is an optional research dependency. The base `fnr3-re` package remains usable without it.

Install the analysis tooling with:

```bash
python -m pip install -e '.[psp-analysis,dev]'
```

The strict loader checks both package version and the VCS commit recorded by the installed distribution. A different or unverifiable toolkit revision is rejected unless the operator explicitly opts into exploratory mode with `--allow-unpinned-toolkit`.

## Authoritative input boundary

New PSP analysis consumes only a verified local workspace:

```text
<workspace>/original/
<workspace>/manifests/workspace.json
```

Create that workspace outside the Git repository:

```bash
python tools/build_reference_workspace.py "/path/to/Fight Night Round 3 (USA).iso" /local/fnr3-workspace
```

Then analyze its PSP modules:

```bash
fnr3-re analyze-psp-modules /local/fnr3-workspace
```

Optional external NID databases can be supplied repeatedly:

```bash
fnr3-re analyze-psp-modules /local/fnr3-workspace \
  --nid-db /path/to/psp_nids.csv
```

Repository-root legacy `BOOT.BIN`, `EBOOT.BIN`, archives, extracted assets, or other historical payloads are not authoritative inputs for this workflow. Candidate executable discovery is driven by the verified workspace manifest and the corresponding files under `original/`.

Before discovery, `fnr3-re` verifies the workspace contents and requires the exact supported Fight Night revision, ISO hash, and ISO size. Hash drift, path escape, and symlinked original content are rejected.

## Analysis pipeline

For each candidate executable, the adapter:

1. inventories ELF/PRX or encrypted `~PSP` content from the verified workspace;
2. parses usable modules through the toolkit public analysis API;
3. plans all usable module placements in one pass;
4. disassembles relocatable modules at their planned analysis/runtime view and preserves fixed executable addressing;
5. runs public advanced analysis;
6. constructs relocated models for cross-module linking;
7. performs structural linking even without an external NID database; and
8. optionally resolves more names when one or more `--nid-db` inputs are supplied.

Encrypted modules are retained in the inventory with `needs_decryption` status. This integration does not decrypt PSP executables. A malformed secondary module is recorded as failed without discarding successful analysis of other modules; a boot-module analysis failure aborts the run.

The current adapter does not synthesize data typing through private toolkit internals. `typing.json` is marked unavailable unless a supported analysis path has supplied typing data.

## Placement semantics

The toolkit's Phase 7G placement model is preserved rather than reinterpreted by Fight Night tooling:

- fixed `ET_EXEC` modules keep declared load addresses;
- the selected relocatable boot module may use the PSP low-allocation boot inference;
- secondary relocatable PRXs receive deterministic analysis placement when their exact runtime position cannot be proven statically.

A placement's numeric confidence is toolkit confidence only. It is serialized as `tool_confidence` and **does not** become Fight Night `CANDIDATE`, `PROBABLE`, or `CONFIRMED` evidence.

Similarly, `runtime_address_claim` is preserved as a toolkit placement property. A deterministic analysis address is not silently promoted into a claim that the retail game loaded that module at that exact address.

## Address domains

Address-like values remain typed by domain. Do not compare or substitute them without an explicit mapping:

- `iso_lba` — ISO logical block address;
- `iso_byte_offset` — byte offset in the disc image;
- `elf_virtual_address` — address in the executable's original ELF view;
- `runtime_address` — address in a relocated runtime/analysis load view;
- module-relative addresses, executable file offsets, archive offsets, and resource offsets remain separate domains when encountered elsewhere in the project.

The compact PSP evidence manifest uses explicit `{ "type": ..., "value": ... }` records for address fields it exports.

## Local output

A successful run replaces two workspace-local outputs transactionally:

```text
<workspace>/working/pspdisasm/
<workspace>/manifests/pspdisasm-module-evidence.json
```

The detailed tree is local research output:

```text
working/pspdisasm/toolchain.json
working/pspdisasm/modules/<safe-id>/executable.json
working/pspdisasm/modules/<safe-id>/placement.json
working/pspdisasm/modules/<safe-id>/disassembly.json
working/pspdisasm/modules/<safe-id>/advanced.json
working/pspdisasm/modules/<safe-id>/typing.json
working/pspdisasm/links/module_links.json
working/pspdisasm/links/propagated_symbols.json
```

Encrypted or failed modules receive inventory/error JSON instead of fabricated analysis products. Module directory IDs are deterministic from normalized workspace path plus the first 12 hexadecimal characters of the source SHA-256.

The writer stages both the detailed tree and evidence manifest before replacement. If generation or replacement fails, the previous successful outputs are restored. Symlinked or resolved-outside-workspace output paths are rejected.

These generated files belong to the local workspace. Do not copy detailed disassembly, extracted payloads, or other copyrighted workspace products into the Git repository.

## Compact evidence manifest

`manifests/pspdisasm-module-evidence.json` is deliberately smaller than the detailed run tree. It records deterministic static facts and provenance such as:

- Fight Night revision and reference ISO hash;
- SHA-256 of the authoritative workspace manifest;
- exact toolkit repository/version/revision state;
- source workspace paths, source hashes, sizes, ISO locations, and module status;
- ELF and placement summaries with typed address domains;
- import/export, relocation, function, symbol, reference, and advanced-analysis counts;
- cross-module link/resolution counts and warnings.

It intentionally excludes generated assembly bodies, instruction words, raw executable bytes, extracted resources, timestamps, saves, RAM captures, screenshots, and audio.

The manifest is deterministic for identical inputs. Static-tool output is research evidence, not an automatic semantic confirmation. Promotion into the project's tracked Fight Night evidence requires the normal evidence workflow and its independent confirmation requirements.

## Exploratory unpinned mode

For controlled experimentation only:

```bash
fnr3-re analyze-psp-modules /local/fnr3-workspace --allow-unpinned-toolkit
```

This permits a nonmatching or unverifiable toolkit installation to run, but the resulting provenance records `revision_locked: false`. Such output must not be treated as revision-locked Fight Night evidence until reproduced with the approved toolkit baseline.
