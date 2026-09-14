# Static Reverse-Engineering Ceiling

## Purpose

This document answers one question for the whole verified `ULUS10066-v1.00`
corpus and the whole planned overhaul (not Task 10/11, not boxer data alone,
not any single archive or module): **how much of the complete planned Fight
Night Round 3 PSP overhaul can be understood, mapped, reconstructed, and
prepared using static evidence alone, before any runtime reverse engineering
is required?**

It is a bounded, machine-readable evidence-question inventory, not a
subjective estimate. Every number below is a count over
`analysis/reports/static-re-ceiling.json`'s `questions` array. No PPSSPP
execution, debugger session, save state, breakpoint, or gameplay experiment
was performed to produce it or any prior pass this project has run.

Governing documents: `Fight Night Round 3 PSP Reverse Engineering
Infrastructure Shell.txt`, `config/subsystem_registry.json`,
`docs/architecture/evidence-standard.md`, `docs/architecture/decompilation-gate.md`.

## Classification

Every bounded evidence question is placed in exactly one of four categories:

- **STATICALLY_RESOLVED** -- enough static/deterministic evidence exists that
  no runtime observation is required.
- **STATICALLY_SOLVABLE** -- not solved yet, but a concrete, named static
  avenue remains (specific files/functions/techniques). Never placed in the
  runtime backlog.
- **STATICALLY_AMBIGUOUS** -- static work has narrowed the answer to two or
  more remaining interpretations; runtime is considered only after the
  relevant static graph is exhausted.
- **RUNTIME_ESSENTIAL** -- the answer fundamentally depends on dynamic
  information no static evidence can supply. Per project policy, a question
  is never placed here merely because a function is hard to read, a decompile
  is poor, a string/xref is missing, a record is variable-sized, or one
  archive didn't reveal the answer -- every reasonable static technique must
  be attempted first.

## Overall totals

| Category | Count | Share of 57 |
|---|---|---|
| STATICALLY_RESOLVED | 25 | 43.9% |
| STATICALLY_SOLVABLE | 27 | 47.4% |
| STATICALLY_AMBIGUOUS | 5 | 8.8% |
| RUNTIME_ESSENTIAL | 0 | 0.0% |
| **Total bounded questions** | **57** | 100% |

## Static ceiling

**Static ceiling = STATICALLY_RESOLVED + STATICALLY_SOLVABLE = 25 + 27 = 52 of 57 questions (91.2%).**

This is a count-based projection, not a subjective guess: it is the number of
questions that either already have static evidence in hand, or have a
concrete, named static avenue that has not yet been walked. The remaining 5
questions (8.8%) are STATICALLY_AMBIGUOUS -- narrowed to specific named
alternatives, each with its own next disassembly step, not abandoned to
runtime.

## Runtime floor

**Runtime floor = 0 questions.**

No question in this pass's 57-question inventory was found to be genuinely
RUNTIME_ESSENTIAL. The one candidate drafted during this pass -- whether the
career save format (`program-16-05`, "does the save format have unused/reserved
space for Career Mode 2.0 / Amateur Career fields") -- was re-examined against
the project's anti-premature-classification rule and reclassified
`STATICALLY_SOLVABLE`: the maximum length the career-payload serializer can
ever write is a static, code-determined fact (sum of fixed-size field writes
plus variable-length writes bounded by other statically-provable maxima),
not something that requires observing a real played-in save file. See
`analysis/resources/runtime-minimum-backlog.json` (schema_version 3, empty)
and `analysis/resources/static-re-backlog.json` entry `program-16-05` for the
named next step.

## Breakdown by Program

| Program | Subsystem | Resolved | Solvable | Ambiguous | Runtime | Total |
|---|---|---|---|---|---|---|
| program-00 | Intake | 2 | 0 | 0 | 0 | 2 |
| program-01 | Build/Rebuild | 1 | 1 | 0 | 0 | 2 |
| program-03 | Modules | 3 | 1 | 0 | 0 | 4 |
| program-04 | Boxers | 3 | 2 | 2 | 0 | 7 |
| program-05 | Fight | 1 | 2 | 0 | 0 | 3 |
| program-06 | Punches | 1 | 2 | 0 | 0 | 3 |
| program-07 | Stamina | 1 | 2 | 0 | 0 | 3 |
| program-08 | Damage | 2 | 2 | 0 | 0 | 4 |
| program-09 | Defense | 1 | 1 | 0 | 0 | 2 |
| program-10 | Medical | 1 | 2 | 0 | 0 | 3 |
| program-11 | Judging | 1 | 1 | 1 | 0 | 3 |
| program-12 | AI | 1 | 1 | 1 | 0 | 3 |
| program-13 | Weights | 1 | 2 | 0 | 0 | 3 |
| program-16 | Career/save | 2 | 3 | 0 | 0 | 5 |
| program-28 | UI/commentary | 1 | 2 | 1 | 0 | 4 |
| program-29 | Budgets | 3 | 1 | 0 | 0 | 4 |
| interface-audio | Audio | 0 | 1 | 0 | 0 | 1 |
| interface-renderer | Renderer | 0 | 1 | 0 | 0 | 1 |

Every entry's identity, evidence, source addresses/functions, and remaining
static work are in `analysis/reports/static-re-ceiling.json`'s `questions`
array (`counts_by_program` block has the same table in machine-readable form).

## Breakdown by planned overhaul feature

Each question may tag more than one planned feature, so these columns do not
sum to 57.

| Feature | Resolved | Solvable | Ambiguous | Runtime |
|---|---|---|---|---|
| combat | 10 | 14 | 2 | 0 |
| career-2 | 10 | 9 | 3 | 0 |
| roster | 9 | 8 | 4 | 0 |
| amateur | 9 | 6 | 2 | 0 |
| generated-boxers | 8 | 2 | 2 | 0 |
| divisions | 8 | 6 | 1 | 0 |
| career-health | 7 | 7 | 0 | 0 |
| legacy | 2 | 0 | 0 | 0 |

`combat` (the core punch/stamina/damage/defense/AI/judging overhaul) has the
largest STATICALLY_SOLVABLE count -- expected, since it spans the most
individual Programs (05/06/07/08/09/12) and none of those programs' internal
formulas (stamina cost, damage/stun thresholds, hit-detection convergence,
AI decision loop) were disassembled to completion in this pass, only located
by name/string evidence and handed a concrete next disassembly target.

## Major findings this pass

- **6 weight divisions are confirmed in executable code**, not inferred from
  data alone: `INFO_Division_1` through `INFO_Division_6` plus an explicit
  `INFO_Division_Unknown` fallback, appearing at 4 separate string-table
  locations, each consumed by a distinct function
  (`func_0019527C`, `func_001B798C`, `T_001E9A58`, `T_00202170`/`T_00201BB4`).
  This is direct evidence relevant to the planned Bantamweight/Cruiserweight
  roster-expansion feature.
- **A 3-judge, per-boxer, per-round scorecard model is proven**: 6 named
  fields (`aJudge1Boxer1Score` .. `aJudge3Boxer2Score`) under one function
  (`T_001F7248`).
- **A named, per-player-slot AI tuning-category system is proven**: 6
  `ai/mods/p%d/...` debug-path strings (misc offense, defense, bag-o-tricks,
  attack power, energy and health, phys damage), two of which are consumed by
  two distinct functions.
- **A generic localization indirection is proven**: `s_pfnGetLocalizedString`,
  a named function-pointer variable, referenced by `T_000CE8A0`.
- Named-but-unresolved evidence for stamina (`iStamina`, two consuming
  functions), knockdowns/TKO (`strKnockdowns*`, `astrTKOTime`, the
  `M_3_Knockdown_Rule`), the cutman economy (`strCutmanRate`/`strCutmanAmount`),
  and career/training accessors (`GetCareerMode`/`SetCareerMode`,
  `GetTrainingInfo`/`SetTrainingInfo`) -- each STATICALLY_SOLVABLE with a
  named next disassembly target, not RUNTIME_ESSENTIAL.

## Questions previously at risk of premature runtime classification

`program-16-05` (career save reserved space) is the only question in this
pass that was drafted as RUNTIME_ESSENTIAL before being re-examined and
reclassified STATICALLY_SOLVABLE per the project's explicit rule that a
question is not runtime-essential merely because a value has not yet been
traced through code. See "Runtime floor" above.

No prior-pass runtime-classified questions needed re-examination in this
pass: the prior PR #31 passes already drove
`analysis/resources/runtime-minimum-backlog.json` to empty
(schema_version 2) before this pass began; this pass's own corpus-wide sweep
did not surface any new evidence contradicting that.

## Discipline confirmation

- No PPSSPP execution, debugger session, save state, breakpoint, or gameplay
  experiment was performed in this pass.
- No overhaul gameplay behavior (combat, stamina, damage, AI, judging,
  Career Mode 2.0, Amateur Career, save expansion, ratings, generated
  fighters, training, world simulation) was implemented.
- No new copyrighted retail payload (ISO, extracted binary, reconstructed
  archive) was committed; all evidence is normalized JSON, hashes, schemas,
  and documentation referencing hash-verified samples already tracked by the
  repository's existing precedent.

## Related artifacts

- `analysis/reports/static-re-ceiling.json` -- the full 57-question machine-readable matrix, counts, static ceiling, and runtime floor.
- `analysis/resources/static-re-backlog.json` -- the 32 STATICALLY_SOLVABLE/STATICALLY_AMBIGUOUS questions' named remaining static avenues, corpus-wide.
- `analysis/resources/runtime-minimum-backlog.json` -- empty (schema_version 3).
- `analysis/resources/static-discovery-backlog.json` -- the earlier Task 10/11-scoped backlog (boxer/resource-loader detail), preserved unmodified.
- `docs/decomp/packages/resource-loaders/README.md`, `docs/decomp/packages/xdb-schema/README.md`, `docs/decomp/packages/save-system/README.md` -- the narrative packages this inventory draws on.
