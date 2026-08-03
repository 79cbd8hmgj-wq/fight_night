# Fight Night Round 3 PSP Functional Reverse Engineering

This repository is being converted into an evidence-first functional reverse-engineering project for **Fight Night Round 3 PSP (USA, ULUS10066, revision 1.00)**.

## Project rule

No overhaul feature may begin until every affected system, and every system that owns or consumes its data, reaches a verified replacement boundary. The exact gate is defined in [`docs/architecture/decompilation-gate.md`](docs/architecture/decompilation-gate.md).

## Current phase

**Phase I — overhaul-scope functional reverse engineering**

Phase I permits discovery, instrumentation, neutral replacement tests, codecs, rebuild tooling, and original-behavior reconstruction. It prohibits new gameplay behavior, roster additions, new divisions, Career Mode 2.0 behavior, and Amateur Career 2.0 behavior.

The machine-readable scope and dependency graph is stored in [`config/subsystem_registry.json`](config/subsystem_registry.json). Evidence requirements are defined in [`docs/architecture/evidence-standard.md`](docs/architecture/evidence-standard.md).

## Supported reference build

- Disc ID: `ULUS10066`
- Region: USA
- Disc version: `1.00`
- Reference ISO SHA-256: `b11da5afe208d9791eecd9f6a44d0f57946f7d9de165b7d8dd22f5ee740f4ee2`

Exact image validation is implemented in Task 3. Until then, these values are locked project metadata rather than an executable verification claim.

## Repository state

The existing repository began as a partial extraction of EA resources plus PSP executables and audit reports. It is not a compilable source decompilation and has no proven no-change rebuild pipeline. Legacy copyrighted payloads already present in repository history must not be treated as acceptable project inputs going forward. New work must commit only tools, schemas, reconstructed source, normalized evidence, tests, and documentation—not ROMs, original executables, extracted assets, saves, RAM dumps, screenshots, or recorded audio.

## Evidence policy

- Decompiler output alone cannot establish a confirmed semantic claim.
- Runtime, exact-binary, deterministic reconstruction, or controlled input/output evidence is required.
- Runtime addresses, module-relative addresses, ELF offsets, archive offsets, and ISO offsets are distinct types.
- Every patch or neutral replacement must be revision-locked and guarded by expected original bytes or records.
- Every research checkpoint answers one bounded evidence question.

## Source documents

- Fight Night Round 3 PSP Reverse-Engineering and System-Overhaul Master Plan
- Fight Night Round 3 PSP Overhaul-Scope Functional Reverse Engineering Implementation Plan
- Fight Night Round 3 PSP System Overhaul, including Career Mode 2.0 and Amateur Career 2.0

## Immediate execution order

1. Governance and subsystem registry
2. Evidence schemas and package validator
3. Exact revision lock
4. ISO workspace
5. Resource codecs
6. No-change rebuild
7. Module and address map
8. PPSSPP harness
9. Save architecture
10. Resource loaders
11. Boxer and roster package

Fight-engine reconstruction remains blocked until Tasks 1–11 establish stable inputs, rebuilds, runtime evidence, save contracts, and boxer-data ownership.
