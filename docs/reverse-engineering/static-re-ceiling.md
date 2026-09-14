# Static Reverse-Engineering Ceiling

## Purpose

This document answers one question for the verified `ULUS10066-v1.00`
corpus enumerated so far and the whole planned overhaul: **how much of the
complete planned Fight Night Round 3 PSP overhaul can be understood, mapped,
reconstructed, and prepared using static evidence alone, before any runtime
reverse engineering is required?**

It is a bounded, machine-readable evidence-question inventory, not a
subjective estimate. Every number below is a count over
`analysis/reports/static-re-ceiling.json`'s `questions` array. No PPSSPP
execution, debugger session, save state, breakpoint, or gameplay experiment
was performed to produce it or any prior pass this project has run.

Governing documents: `Fight Night Round 3 PSP Reverse Engineering
Infrastructure Shell.txt`, `config/subsystem_registry.json`,
`docs/architecture/evidence-standard.md`, `docs/architecture/decompilation-gate.md`.

## Revision history

- **Base pass** (PR #32): built the original 57-question corpus-wide
  inventory.
- **Delta pass** (this revision): a *delta-only* static investigation of 11
  newly-added retail files -- `debugmenu.big`, `genericbackground.big`,
  `internetmainmenu.big`, `mainmenu.big`, `tutorialoverlay.big`,
  `adhocrivals.big`, `careerfighthistory.big`, `recordbooks.big`,
  `fnhud.hud`, `optionsettings.big`, `selectboxer.big` -- evaluated
  specifically against the 5 previously STATICALLY_AMBIGUOUS questions and
  the wider STATICALLY_SOLVABLE backlog. It did **not** repeat the base
  pass's corpus-wide sweep and does not claim full-ISO completeness (see
  `analysis/resources/corpus-resource-index.json`'s `delta_passes` block).
  The inventory grew from 57 to 63 questions.
- **Overhaul Alpha 1** (this revision): the first implementation tranche
  (Core Boxer + Fight Systems, `src/fnr3_re/overhaul/`) is not a static-RE
  assessment pass and did not re-sweep the corpus. It performed the
  *minimum focused static RE* its own implementation work required (per
  its own methodology: "targeted static RE -> establish replacement
  boundary -> implement -> validate statically"), which resolved
  `program-04-04` (func_00186464's linked list, see
  `analysis/resources/overhaul-alpha1-evidence.json` entry `alpha1-03`)
  and partially advanced `program-11-03` (judge weighting, entry
  `alpha1-06`) as a direct byproduct. These two updates are recorded here
  for consistency, not as a renewed broad-assessment effort.

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

| Category | Count | Share of 63 |
|---|---|---|
| STATICALLY_RESOLVED | 29 | 46.0% |
| STATICALLY_SOLVABLE | 30 | 47.6% |
| STATICALLY_AMBIGUOUS | 4 | 6.3% |
| RUNTIME_ESSENTIAL | 0 | 0.0% |
| **Total bounded questions** | **63** | 100% |

## Static ceiling

**Static ceiling = STATICALLY_RESOLVED + STATICALLY_SOLVABLE = 29 + 30 = 59 of 63 questions (93.7%).**

Up from 52/57 (91.2%) before the delta pass, then 58/63 (92.1%) after it,
then 59/63 (93.7%) as a byproduct of Overhaul Alpha 1's own targeted RE.
This project does not optimize for this number -- it is reported here only
because a real, evidence-backed question was genuinely resolved along the
way. This is a count-based projection, not a subjective guess.

## Runtime floor

**Runtime floor = 0 questions** (unchanged).

No question surfaced by this delta pass -- including several genuinely new
structural findings (the shared native-function-registration mechanism, the
packed options bitfield, `fnhud.hud`'s component-tag container) -- was found
to be genuinely RUNTIME_ESSENTIAL. Each was classified STATICALLY_SOLVABLE
or left STATICALLY_AMBIGUOUS with named next steps.
`analysis/resources/runtime-minimum-backlog.json` remains empty
(schema_version 4).

## Breakdown by Program

| Program | Subsystem | Resolved | Solvable | Ambiguous | Runtime | Total |
|---|---|---|---|---|---|---|
| program-00 | Intake | 2 | 0 | 0 | 0 | 2 |
| program-01 | Build/Rebuild | 1 | 1 | 0 | 0 | 2 |
| program-03 | Modules | 3 | 2 | 0 | 0 | 5 |
| program-04 | Boxers | 4 | 2 | 1 | 0 | 7 |
| program-05 | Fight | 1 | 3 | 0 | 0 | 4 |
| program-06 | Punches | 1 | 2 | 0 | 0 | 3 |
| program-07 | Stamina | 1 | 2 | 0 | 0 | 3 |
| program-08 | Damage | 2 | 3 | 0 | 0 | 5 |
| program-09 | Defense | 1 | 1 | 0 | 0 | 2 |
| program-10 | Medical | 1 | 2 | 0 | 0 | 3 |
| program-11 | Judging | 1 | 1 | 1 | 0 | 3 |
| program-12 | AI | 2 | 1 | 1 | 0 | 4 |
| program-13 | Weights | 1 | 2 | 0 | 0 | 3 |
| program-16 | Career/save | 3 | 4 | 0 | 0 | 7 |
| program-28 | UI/commentary | 2 | 1 | 1 | 0 | 4 |
| program-29 | Budgets | 3 | 1 | 0 | 0 | 4 |
| interface-audio | Audio | 0 | 1 | 0 | 0 | 1 |
| interface-renderer | Renderer | 0 | 1 | 0 | 0 | 1 |

Every entry's identity, evidence, source addresses/functions, and remaining
static work are in `analysis/reports/static-re-ceiling.json`'s `questions`
array (`counts_by_program` block has the same table in machine-readable form).

## Breakdown by planned overhaul feature

Each question may tag more than one planned feature, so these columns do not
sum to 63.

| Feature | Resolved | Solvable | Ambiguous | Runtime |
|---|---|---|---|---|
| combat | 11 | 16 | 2 | 0 |
| career-2 | 13 | 9 | 3 | 0 |
| roster | 11 | 8 | 4 | 0 |
| amateur | 11 | 7 | 2 | 0 |
| generated-boxers | 10 | 3 | 2 | 0 |
| divisions | 9 | 7 | 1 | 0 |
| career-health | 7 | 10 | 0 | 0 |
| legacy | 2 | 2 | 0 | 0 |

## The five STATICALLY_AMBIGUOUS questions, re-evaluated against the 11 new files

1. **`func_00186464`'s 8-bit linked-list index** -- no direct new evidence
   found. The lead advanced one hop: `selectboxer.big`'s `GetSelectBoxerInfo`
   (the boxer-list-selection screen's own native data accessor) is owned in
   BOOT.BIN only by a generic native-function *registration* trampoline
   (`func_001D537C`/`func_001D5438`, calling the shared registrar
   `func_0CDAC0`/`func_0CDA70`), not by the real implementation. **Remains
   STATICALLY_AMBIGUOUS**, with a concrete new avenue: trace the registration
   mechanism to reach the real implementation.
2. **Fixed maximum roster/database count (121)** -- `selectboxer.big`'s 397
   named UI constants contain no `MAX_BOXER`/`MAX_ROSTER`-style cap (a
   genuine negative result across all 10 newly-decoded `.const` pools; only
   `MAX_WEIGHTCLASS` and generic display-pagination limits exist). This rules
   out one of four original interpretations ("a UI-authored maximum") but not
   the others. **Remains STATICALLY_AMBIGUOUS.**
3. **Judges' distinct per-judge scoring weights** -- none of the 11 files is
   a scorecard/judging screen; no relevant identifier found. **Remains
   STATICALLY_AMBIGUOUS, unaffected by this pass.**
4. **AI difficulty/fighting-style enum** -- **RESOLVED for the difficulty
   half.** A raw byte-level search of `optionsettings.big` (not the
   extracted-string-table search the prior pass relied on) found, at file
   offset `0x8548`, three consecutive localization-key strings inside
   `optionSettings.const`'s data region: `m_arrText = ["$O_Easy",
   "$O_Medium", "$O_Hard"]`, bound to the `cpToggleDifficulty` widget
   (`$M_Difficulty`). This is direct, unambiguous proof of a named 3-level
   difficulty enum. The fighting-style half (swarmer/slugger/etc.) was
   **split into its own question** and remains STATICALLY_AMBIGUOUS -- no
   style name was found in any of the 11 files either.
5. **Commentary lookup/event-ID architecture** -- new evidence:
   `optionsettings.big` proves commentary is a real, named, toggleable rule
   (`cpToggleCommentary`/`iDisplayCommentaryOption`), and the latter's 3
   BOOT.BIN string sites are each owned by a different, disassemblable
   function (`T_001D9A08`, `T_001DC5DC`, `T_001FB69C` -- the same 3 that
   decode a packed options bitfield, see below). **Remains
   STATICALLY_AMBIGUOUS** (the on/off toggle is now well-evidenced; whether
   the actual audio *selection* is table-driven is still open), but with 3
   concrete new disassembly targets in place of one string reference.

## Other backlog questions advanced this pass

- **Boxer per-record schema** (program-04): `selectboxer.big` names an exact,
  ordered 9-field boxer rating-stat schema (Power/Speed/Agility/Stamina/
  Chin/Body/Heart/Cuts/Overall, bounded by `NUM_STATS`), all 9 confirmed as
  BOOT.BIN strings owned by the *same* function pair (`T_001D54A0`/
  `T_001E83E0`) already tied to `iStamina` alone in the base pass.
- **Stamina cost/regeneration formula** (program-07): **corrected**, not
  advanced -- `T_001D54A0`/`T_001E83E0` are now proven to be UI
  rating-display registration trampolines, not in-fight stamina logic. The
  formula must be sought elsewhere; this prevents a future pass from
  wrongly disassembling the wrong functions.
- **Weight-division count** (program-13): independently corroborated by a
  second resource (`selectboxer.big` names exactly the same 6 divisions --
  Featherweight/Lightweight/Welterweight/Middleweight/Light-Heavyweight/
  Heavyweight -- as BOOT.BIN's `INFO_Division_1..6`).
- **Boxer-selection UI screen identity** (program-28): **RESOLVED** --
  `selectboxer.big` is proven to be the boxer-selection screen
  (`TL_Select_Boxer`), with 4 native accessors and a Red/Blue two-corner,
  custom-boxer-aware selection model.
- **Amateur vs. professional fight history** (new, program-16):
  **RESOLVED** -- `careerfighthistory.big` proves the retail game already
  distinguishes Professional and Amateur fight records, directly relevant to
  the planned Amateur Career feature.
- **Hall of Fame / records-book legacy system** (new, program-16):
  `recordbooks.big` proves a 6-category records/Hall-of-Fame screen exists
  (Most Wins, Fastest KOs, Most KOs, Top 10, Career Earnings), relevant to
  the `legacy` planned feature.
- **Damage/stoppage rule surface** (new, program-08): `optionsettings.big`'s
  17-entry rules-toggle list adds 5 previously-unevidenced named rules --
  `cpToggleIllegalBlows`, `cpToggleSavedByBell`, `cpToggleAutoRecovery`,
  `cpToggleKOMoment`, `cpToggleFightStoppage` -- and reveals that the
  options/rules storage format is a **packed 32-bit bitfield** (proven by
  partial disassembly of `T_001D9A08`), not one scalar per option.
- **A third resource-dispatch mechanism** (new, program-03): every
  `GetXxxInfo`/`SetXxxInfo`/`DEBUG_GetXxxData` native name found across all
  11 files is owned by a small trampoline that calls a shared registrar,
  `func_0CDAC0`/`func_0CDA70` -- a single mechanism whose further tracing
  would advance many other open questions at once.

## Discipline confirmation

- No PPSSPP execution, debugger session, save state, breakpoint, or gameplay
  experiment was performed in this pass.
- No overhaul gameplay behavior (combat, stamina, damage, AI, judging,
  Career Mode 2.0, Amateur Career, save expansion, ratings, generated
  fighters, training, world simulation) was implemented.
- No new copyrighted retail payload (ISO, extracted binary, reconstructed
  archive) was committed; all evidence is normalized JSON, hashes, schemas,
  and documentation referencing hash-verified samples already present in the
  repository.
- This pass does not claim full-ISO completeness -- it is delta-only over 11
  named files plus their static cross-references into `BOOT.BIN`.

## Related artifacts

- `analysis/reports/static-re-ceiling.json` -- the full 63-question machine-readable matrix, counts, static ceiling, and runtime floor.
- `analysis/resources/static-re-backlog.json` -- 34 STATICALLY_SOLVABLE/STATICALLY_AMBIGUOUS questions' named remaining static avenues (schema_version 3).
- `analysis/resources/overhaul-alpha1-evidence.json` -- Section L evidence discipline for Overhaul Alpha 1's own findings (fight-session singleton, generic stat accessor, punch-accuracy formula, judging call-site uniformity, etc.), each with original owner, confidence, and replacement-boundary status.
- `analysis/resources/runtime-minimum-backlog.json` -- empty (schema_version 4).
- `analysis/resources/corpus-resource-index.json` -- extended this pass with the 11 new files under `archives_enumerated` and a `delta_passes` record (schema_version 2).
- `analysis/resources/static-discovery-backlog.json` -- the earlier Task 10/11-scoped backlog (boxer/resource-loader detail), preserved unmodified.
- `docs/decomp/packages/resource-loaders/README.md`, `docs/decomp/packages/xdb-schema/README.md`, `docs/decomp/packages/save-system/README.md` -- the narrative packages this inventory draws on.
