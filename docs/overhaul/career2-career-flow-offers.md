# Career Mode 2.0 — Career Flow and Fight Offers

This slice begins the final current-version Career Mode 2.0 priority after
amateur development, living divisions, C2EX persistence, and retirement/legacy.

Retail Fight Night Round 3 already contains a useful offer pipeline. Career
Mode 2.0 should extend that pipeline instead of replacing it blindly.

## Proven retail offer pipeline

The current exact-retail boundaries are:

| Role | ULUS10066-v1.00 address |
|---|---:|
| fights.fnc loader | 0x001A3D48 |
| contract type resolver | 0x001A2C98 |
| select/copy template by ID | 0x001A2FA0 |
| eligibility evaluator | 0x001A3FBC |
| automatic eligible-offer selector | 0x001A319C |
| contract-list provider | 0x0020002C |
| UI selection handler | 0x001FF210 |

The tracked fights.fnc table is FITE plus 50 base templates. Each base
template is 0x44 / 68 bytes.

The retail automatic selector collects at most **10** eligible contract IDs
before its RNG choice.

## Fields used by this host model

The implementation names only fields whose behavior is sufficiently proven:

| Template offset | Host name | Evidence boundary |
|---:|---|---|
| +0x14 | bank_gate_value | compared directly against profile bank |
| +0x18 | worse_rank_bound | zero-based rank upper/worse bound; -1 disables |
| +0x1C | better_rank_bound | zero-based rank lower/better bound; -1 disables |
| +0x20 | weeks_to_fight | scheduling value used as weeks × 7 days |
| +0x30 bit 0 | phase_side_bit | selects initial vs noninitial career side |
| +0x34 | contract_type | signed contract type resolver |
| type 23 | Go Pro | proven special career contract |
| type 27 | Retire | proven special career contract |

Several other fields remain intentionally raw:

- +0x24 → prerequisite_raw
- remaining +0x30 bits → part of eligibility_flags
- +0x44 → fine_print_flags
- +0x50 → percentage_threshold_raw

These names are a boundary, not an omission. Static evidence proves those
fields participate in contract logic, but does not yet justify stronger public
semantic names for every bit/value.

## Proven-gate evaluator

RetailFightContractTemplate.evaluate_proven_gates() currently reproduces only
comparisons that are closed by static evidence.

### Career phase

Retail converts profile+0x121 to boolean and requires:

    bool(profile+0x121) == NOT(template+0x30 bit 0)

Therefore:

- bit 0 = 1 selects the initial/zero career-phase side;
- bit 0 = 0 selects the nonzero/post-initial side.

No meaning is assigned to the remaining flag bits in this slice.

### Ranking

Retail uses zero as the best ranking position.

- +0x18 is the worse/numerically larger bound;
- +0x1C is the better/numerically smaller bound;
- -1 disables the corresponding bound.

The host model therefore accepts rank r only when all active bounds satisfy:

    better_bound <= r <= worse_bound

### Bank gate

Retail rejects a contract when profile+0xA0 is below the value returned from
the live-contract accessor for record +0x14.

The host name bank_gate_value deliberately describes the comparison rather
than claiming whether the template designer intended the value as a fee,
minimum balance, or another economy concept.

### Record-percentage input

Retail forms a rounded win percentage from current W/L/D and later combines it
with template +0x50.

The percentage calculation is exposed by the host context for evidence and
testing, but +0x50 is **not yet applied** because its final comparison
semantics/edge cases are not closed strongly enough for this implementation.

The same rule applies to type-specific prechecks and +0x24: the model does
not silently omit them and then claim complete retail eligibility. The API is
explicitly named evaluate_proven_gates.

## Automatic candidate collection

collect_automatic_eligible_offers() mirrors the proven bounded collection
shape:

1. preserve candidate-pool order;
2. evaluate the proven gate subset;
3. ignore duplicate IDs;
4. stop after ten accepted IDs.

It deliberately does **not** perform the retail RNG choice. Random choice is a
policy/integration layer after candidate validity is established.

## Career calendar projection

The retail scheduler adds the contract's +0x20 value multiplied by seven
days to its persistent date.

Career Mode 2.0 uses a mod-owned monotonic week ordinal for its expanded
calendar/legacy systems. The host projection is therefore:

    scheduled_week = current_week + weeks_to_fight

This is an equivalent host representation of a proven retail scheduling
quantity; it is not a reinterpretation of the retail date binary format.

## Existing selection seam

The original UI already supplies iContractID to OnSelectFightContract
(0x001FF210). That path invokes the career slot-0 contract object's selection
method, whose +0x28 entry is 0x001A2FA0, and copies the selected template into
the live contract object.

This is the preferred integration seam for Career Mode 2.0 offers: produce a
richer eligible list while preserving the game's existing selected-contract
and confirmation flow wherever possible.

## Current-version exclusions

The current Career Mode 2.0 scope still excludes:

- persistent manager relationships;
- persistent promoter relationships/influence;
- trainer/cutman expansion;
- recovery/injury expansion.

Retail fine print may still expose promoter-related contract terms. Those
terms do not justify adding the deferred persistent relationship system.

## Next step

The next bounded RE pass should close the remaining offer-policy fields needed
for this release, especially:

1. the exact +0x50 win-percentage comparison;
2. the contract-type-specific prechecks needed by ordinary fight offers;
3. opponent/template fields used to materialize the selected fight;
4. the selection-confirmation edge into AssignCareerMatch and persistent
   descriptor/date state.

Once those are closed, the host offer model can be promoted from a proven-gate
subset into the complete current-version Career 2.0 offer policy.
