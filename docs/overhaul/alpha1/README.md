# Overhaul Alpha 1 -- Core Boxer + Fight Systems

## What this milestone is

The first implementation tranche of the planned Fight Night Round 3 PSP
overhaul: a substantial, tested, integrated set of new gameplay systems
(boxer ratings, stamina, damage/stun/knockdown, fight rules, AI response,
judging) built on top of the reverse-engineering foundation from PRs
#31-#33 (63-question static evidence inventory, `analysis/reports/
static-re-ceiling.json`). This is not another assessment pass.

Method used throughout, per this milestone's own instructions: **targeted
static RE -> establish replacement boundary -> implement -> validate
statically -> continue to next dependency.** No runtime observation
(PPSSPP, debugger, breakpoints, save states) was used at any point. No
unidentified field was guessed at or patched.

## What is genuinely new this pass (static RE)

Full write-ups with confidence and source citations are in
`analysis/resources/overhaul-alpha1-evidence.json` (Section L discipline:
original owner, source function, reconstructed behavior, confidence,
replacement/hook boundary, patch location, affected Programs). Summary:

1. **The fight/match-context global singleton** (`func_001B3EA8` lazy
   accessor, `func_001AF768` constructor) -- corrects an earlier pass's
   misreading of `func_001AF768` as a "UI/menu-construction routine." It is
   in fact this singleton's constructor, reached from 3 independent
   subsystems this pass (fight-totals, judging, options). Two of its
   fields are corroborated by multiple call sites: `+0x19B0`/`+0x19B4`
   (the two competing boxers' object pointers).
2. **`func_00186464`'s linked-list index resolved** (previously
   `STATICALLY_AMBIGUOUS`): it is a table-instance registry, not a
   boxer-record index. Full disassembly of its caller `func_0018654C`
   found the missing list-insertion writer (`node->0x10 = new_object`).
3. **A generic fight-statistics accessor**, `func_0BA748(context,
   boxer_slot, subcontext, stat_id)`, with 3 proven stat IDs (0=punches
   thrown, 1=punches hit, 0xE=knockdowns), found inside `T_001F2E00` --
   the first function this project has proven to be a *real*
   implementation (716 instructions) rather than a UI native-function
   registration trampoline (the ~11-30 instruction pattern seen
   everywhere else, including in the two functions below).
4. **A fully reconstructed formula**: punch-accuracy percentage
   (`trunc((hit/thrown)*100)`, float32 math, 0.0 sentinel on zero-thrown),
   traced instruction-by-instruction inside `T_001F2E00`.
5. **Judging call-site uniformity proven**: `T_001F7248` (the real
   `GetJudgesScoreInfo`, 216 instructions) treats all 3 judges with
   identical code -- no per-judge weighting exists in the calling code.
   Whether a per-judge-*object* internal bias exists remains open
   (`func_08A02C`'s own body was not disassembled).
6. **The shared native-function registry** deepened one level:
   `func_0CDAC0`/`func_0CDA70` both reduce to two ~122-instruction
   registration entry points sharing one global registry pointer
   (`0x005436D8`). The call-by-name *dispatch* side (the APT bytecode
   interpreter itself) was not reached -- this is the single largest
   remaining blocker, see "Blockers" below.
7. **T_001D54A0/T_001E83E0 confirmed as UI-only**: the two functions a
   prior pass tied to `iStamina` register all 9 proven boxer rating names
   (Power/Speed/Agility/Stamina/Chin/Body/Heart/Cuts/Overall) as UI
   properties for the boxer rating-card display -- not the in-fight
   stamina mechanic. This is a correction that prevents wasted future
   effort, not new gameplay logic.
8. **`xdbboxr.adf`'s per-record boxer stat layout: attempted, still
   unresolved.** A direct read of the decoded payload past the proven
   `+0x18` flags array shows plausible-looking 16-bit values, but no
   consumer function was found this pass connecting them to the 9 proven
   stat names. Per this project's discipline, this is reported as an open
   blocker, not patched or exposed as a resolved field map.

These two resolutions were folded into `analysis/reports/
static-re-ceiling.json` (`program-04-04` now `STATICALLY_RESOLVED`;
`program-11-03` evidence updated, still `STATICALLY_AMBIGUOUS` pending the
narrower sub-question) and `config/subsystem_registry.json`'s
`blocking_unknowns`, as a direct byproduct of the RE this milestone's
implementation work required -- not a renewed broad-assessment effort.

## Section-by-section status

### A. Boxer core model -- IMPLEMENTED (as a replacement boundary)

`src/fnr3_re/overhaul/boxer_model.py`: `BoxerRatings` (the 9 proven fields,
proven order) and `BoxerRatingOverrideTable` (a new, ID-keyed JSON
resource). Because `xdbboxr.adf`'s per-record byte layout remains
unresolved (see finding 8 above), this module does **not** read or write
those bytes -- it implements a neutral replacement boundary instead, per
this milestone's own instructions ("a proven replacement boundary" is an
acceptable alternative to "actual game-owned boxer data" when the latter
isn't yet safely reachable). `overall` defaults to independently-stored
(the conservative choice) with an explicit, tested hook
(`with_overall_derived`) for a future pass that proves the real
Power/Speed/.../Cuts -> Overall relationship, if one exists.

### B. Boxer selection / roster integration -- PARTIALLY ADVANCED

`GetSelectBoxerInfo`/`UpdateSelectBoxerInfo`/`LoadSelectBoxer`/
`SetSelectBoxerInfo`'s registration functions (`func_001D537C`/
`func_001D5438`) were disassembled and confirmed to be registration
trampolines only, sharing the registry described in finding 6. Their real
implementations were **not** reached -- the call-by-name dispatch side of
the registry was not located this pass (see "Blockers"). Consequently:
boxer-ID mapping, selected-boxer state, division filtering, and roster
iteration through the real game code remain unmapped. The 121-entry
maximum question is **not** treated as resolved and roster expansion is
**not** made to depend on it (per this milestone's explicit instruction) --
`BoxerRatingOverrideTable` is keyed by an opaque, mod-defined `boxer_id`
with no assumption about `xdbboxr.adf`'s own ID scheme or count.

### C. Fight lifecycle -- PARTIALLY ADVANCED

The owning object (the fight-session singleton, finding 1) is now
identified, corroborated by 3 independent call sites, with 2 fields
proven. The full lifecycle functions (init/round-start/round-end/
stoppage/decision/teardown) were **not** located this pass -- `docs/
overhaul/alpha1/README.md`'s "Blockers" section names the next step. No
hook map is claimed beyond `fnr3_re.overhaul.fight_session`'s documented
offsets.

### D. Stamina overhaul foundation -- IMPLEMENTED (new rule engine)

`src/fnr3_re/overhaul/stamina.py`: capacity (rating-scaled), current,
named action costs (jab/hook/uppercut/power_punch/clinch), passive
recovery, between-round recovery, an exhaustion threshold with cost/
recovery multipliers. This is new tunable design, not a retail
reconstruction -- the real in-fight stamina mechanic was searched for and
not found (finding 7 explicitly rules out the one prior lead). Tunables
are data-driven (`config/overhaul/alpha1/stamina_tunables.json`, JSON
round-trippable), not scattered constants.

### E. Damage / stun / knockdown foundation -- IMPLEMENTED (new rule engine)

`src/fnr3_re/overhaul/damage.py`: health (rating-scaled by `chin`), a stun
meter with a proven-anchored knockdown relationship (a knockdown requires
prior stun, mirroring the real game's own stun-then-knockdown
progression), per-round knockdown counting, and 3-knockdown-rule
stoppage -- directly wired to `fnr3_re.overhaul.rules.FightRules.
three_knockdown_rule`, the proven real retail rule (`M_3_Knockdown_Rule`).
Cosmetic damage (cuts/swelling geometry) is explicitly out of scope per
this milestone's own instruction.

### F. Fight rules -- IMPLEMENTED

`src/fnr3_re/overhaul/rules.py`: `FightRules` (difficulty, 3-knockdown
rule, auto-recovery, KO moment, fight stoppage, illegal blows, saved-by-
the-bell, round count), all anchored to named, proven retail option
toggles. The underlying packed bitfield (`fight_session.
OFFSET_PACKED_OPTIONS_BITFIELD`, offset `+0x15C`) was located but not
fully bit-mapped by any pass so far -- this module is this mod's own
tunable rule set, not a bit-for-bit reproduction of retail's storage.

### G. AI integration -- IMPLEMENTED (new rule engine, not a decompiled AI)

`src/fnr3_re/overhaul/ai.py`: a rule-based policy (`choose_action`)
reacting to stamina/damage state, prioritized exactly per this milestone's
list (self-preservation when hurt/low-stamina first, then opponent-
condition awareness, then difficulty-scaled default pace). The real AI
decision loop's owning function was not located this pass (only its two
known modifier-string consumers, `func_00093C5C`/`func_00091D24`, neither
disassembled) -- this is new logic layered on the Alpha 1 combat state,
not a replacement of the original AI. `AIModifiers` is named after the
proven `ai/mods/p%d/...` categories so a future pass that does locate the
real table can re-target this policy's knobs without a shape change.

### H. Judging integration -- IMPLEMENTED, with the ambiguity directly addressed

`src/fnr3_re/overhaul/judging.py`: `T_001F7248` was fully disassembled
this pass specifically to resolve the judge-weighting ambiguity per this
milestone's explicit instruction ("do not leave the known judge-weight
ambiguity untouched"). Finding 5 above is the result: no differential
weighting at the call site, so this module's judging formula (a new
10-point-must implementation, since the real per-round formula itself
remains undisassembled) applies identical scoring per judge by default,
with an explicit, tested, currently-zero per-judge bias hook for the
still-open judge-object-internal-state sub-question.

### I. HUD integration -- ASSESSED, not implemented

`fnhud.hud` (decoded this pass and the prior one) is a component-indexed
vector-HUD-geometry container (4-character tags: `RN`/`RC`/`RCH`/`CM`/
`CD`/`MH`/`OL`/`OV`/`PU`/`CY`, plus rendering primitives), not a
text-field-binding format the way the `.apt`/`.const` UI packages are. No
field semantics were inferred from these tags alone, per this project's
explicit discipline. Whether the existing HUD can display Alpha 1's new
state without structural expansion was **not** established this pass --
its header table (repeating size/type/offset triples) was only partially
decoded. No HUD changes were made.

### J. Mod architecture -- REUSED, not rebuilt

This milestone does **not** duplicate patch/build tooling -- it already
existed: `src/fnr3_re/revision.py` (whole-ISO hash + `PARAM.SFO`
verification) and `src/fnr3_re/rebuild.py` (`BytePatch` with byte-guard-
before-patch and fail-closed mismatch handling, `BuildPlan`, atomic
temp-file-then-replace `rebuild_image`, a `BuildReport` with every changed
range's hashes, and a proven no-change-rebuild-equals-source-hash
invariant). `src/fnr3_re/overhaul/build.py` is a thin wiring layer:
`generate_baseline` (empty plan) and `generate_alpha_build` (loads
`config/overhaul/alpha1/build_plan.json`). "Revert" is inherent to the
architecture -- nothing is ever mutated in place, so reverting is just
rebuilding the baseline again.

**The Alpha 1 build plan currently has zero patches.** This pass did not
establish a safe, evidence-backed byte-level patch site for any of the
still-unresolved original formulas (stamina, damage, AI, judging). Per
this milestone's own instructions ("do not patch unidentified fields...
do not overwrite unresolved original behavior blindly"), guessing one
would have violated the discipline this whole project depends on. The
overhaul's own rule-engine code (sections D-H) is real, tested, and ready
to be wired into a real hook the moment one is proven safe.

### K. Scope boundaries -- RESPECTED

No Career Mode 2.0, Amateur Career, promoter/manager systems, training
calendar, financial simulation, generated world population, full roster
expansion, new divisions, injury/medical persistence, or presentation
overhaul was implemented. `BoxerRatingOverrideTable`'s ID-keyed design and
`FightRules`'/`AIModifiers`' plain dataclass shapes were chosen so later
systems (a save-format extension, a roster generator, a training-calendar
system) can consume them without an architectural rework.

## Blockers (named, not vague)

1. **The APT bytecode call-by-name dispatch mechanism.** Registration
   (`func_0CDAC0`/`func_0CDA70` -> `func_0CFE08`/`func_0CF9C4`, shared
   registry at `0x005436D8`) is fully understood; the lookup/invoke side
   that resolves a script's `"GetSelectBoxerInfo"` call to its real
   implementation function was not located. This single blocker gates
   Section B's boxer-ID mapping and roster iteration, and would very
   likely also unblock several `static-re-backlog.json` entries at once.
2. **`xdbboxr.adf`'s per-record boxer stat byte layout.** Attempted this
   pass (finding 8); still open.
3. **The real in-fight stamina/damage/AI/judging formulas.** Only their
   proven data shapes and a handful of real accessor functions were
   found; the formulas themselves were not reached.
4. **`fnhud.hud`'s full header table.** Partially decoded; not enough to
   assess HUD capacity for Alpha 1's new state.

## Tests and quality

`tests/unit/overhaul/` (68 tests): boxer model (JSON round-trip,
validation), fight_stats (the reconstructed formula, deterministic
vectors including the zero-sentinel and a truncation-vs-rounding case),
stamina, damage (including the stun-then-knockdown and 3-knockdown-rule
interaction), judging (including the "all 3 judges score identically"
invariant this pass proved), AI (priority-order cases), rules, tunables
I/O (including that the repository's own `config/overhaul/alpha1/*.json`
files load cleanly), and `build.py` (the Alpha 1 revision/build-plan load
correctly and agree on `revision_id`). Full repository suite, Ruff, and
strict mypy are reported in the PR description.

## What remains before a playable Alpha ISO

A playable build additionally needs, beyond this pass: (1) resolving
blocker 1 to reach real game state; (2) at least one proven, safe patch
site per system (stamina/damage/AI/judging) to actually wire this
rule-engine code into `BOOT.BIN`; (3) a verified reference ISO and
extracted workspace in a session that has one, to exercise
`fnr3_re.overhaul.build`'s `generate_baseline`/`generate_alpha_build` end
to end (this session, like every prior one, had no verified `<workspace>/
original/` available); (4) HUD capacity confirmation or expansion (Section
I); (5) actual PSP-side hook code, not just the Python-side rules engine.
