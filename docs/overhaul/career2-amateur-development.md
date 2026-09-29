# Career Mode 2.0 — Amateur Development Slice

This is the first implementation slice after the Career Mode 2.0 scope lock.

## Current-version scope

The active Career Mode 2.0 release keeps these areas in scope:

1. amateur development;
2. living divisions;
3. C2EX save persistence;
4. retirement/legacy;
5. career flow and fight offers/contracts.

Recovery/injury expansion, trainer/cutman expansion, and persistent
manager/promoter relationship mechanics remain deferred.

## What this slice implements

src/fnr3_re/overhaul/career2_amateur.py adds a host-side domain model for:

- the proven player age field and retail default age 20;
- the proven persistent career phases 0 -> 1 -> 2;
- Career 2.0-owned per-rating potential ceilings;
- Career 2.0-owned per-rating learning rates;
- deterministic training gains capped by potential;
- annual age advancement;
- annual height/weight growth toward explicit targets;
- preservation of development state through the amateur-to-pro transition;
- projection of age, phase, height and weight back onto only statically
  proven retail fields.

## Retail-backed state

The implementation uses the recovered boundaries rather than inventing new
stock-field meanings:

| State | Retail destination |
|---|---|
| Player age mirror | profile +0x41 |
| Career phase | profile +0x121 |
| Current progression age | progression record +0x09 |
| Height | persistent boxer +0x6A |
| Weight | persistent boxer +0x6C |
| Paired height-linked field | persistent boxer +0x70 |
| Paired weight-linked field | persistent boxer +0x72 |

The paired physical fields are synchronized exactly as the recovered
created/generated-boxer paths do. Their independent semantics are still not
renamed; +0x70 is not claimed to be reach and +0x72 is not claimed to be
natural weight.

## Career 2.0-owned state

Per-rating potential ceilings and learning rates are deliberately new mod
state. Static RE found useful original traits — starting-stat archetype,
natural rating emphasis, prime-age center and a coarse AI performance
baseline — but none is a proven eight-attribute potential table or technical
learning-rate table.

The new development data must therefore be persisted through C2EX rather than
overwriting unidentified retail fields.

The proven save boundary is:

- stock active body: 0x5674 bytes;
- stock body capacity: 0x7530 bytes;
- C2EX append offset: 0x5674;
- available extension space: 0x1EBC / 7,868 bytes.

This slice defines the development model only. Binary C2EX encoding and PSP
save/load hooks remain the dedicated save-schema milestone.

## Training policy

The current host formula is intentionally simple and deterministic:

    gain = effort * learning_rate_bps // 10000
    new_rating = min(current_rating + gain, potential_ceiling)

This is Career Mode 2.0 policy, not a claim about retail FNR3's original
training formula. Overall is not automatically recomputed because retail uses
func_001D50F4 and its exact formula has not yet been reconstructed.

## Amateur-to-pro transition

The model preserves the proven two-step transition:

- phase 0 -> phase 1: amateur/intermediate transition;
- phase 1 -> phase 2: professional entry / Go Pro.

The development state is carried through unchanged instead of generating a
replacement professional boxer. This follows the recovered retail transition
behavior, which preserves the player progression and persistent boxer blocks.

## Next implementation dependency

The next step for this slice is to define the compact versioned C2EX binary
schema for the new potential, learning-rate and physical-growth data, then
round-trip this model through that codec without touching the stock 0x5674
bytes.
