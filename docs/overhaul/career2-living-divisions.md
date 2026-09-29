# Career Mode 2.0 — Living Divisions Foundation

This slice implements the retail-backed primitives required by the second
Career Mode 2.0 priority: AI fights, rankings, championships, and weight-class
movement.

## Proven retail structures preserved

The host model now exposes:

- the exact six-class weight classifier:
  - Featherweight <= 126
  - Lightweight 127..135
  - Welterweight 136..147
  - Middleweight 148..168
  - Light Heavyweight 169..190
  - Heavyweight 191..280
  - 281+ invalid in the retail classifier;
- the three persistent career slots:
  - slot 0 = classified base class;
  - slot 1 = one class heavier, or sentinel 7 at Heavyweight;
  - slot 2 = one class lighter, or sentinel 7 at Featherweight;
- the working slot at profile+0x2A and committed/player shadow at profile+0x2B;
- the packed progression-record match descriptor at +0x24;
- the exact result reciprocity table for result codes 0..11;
- the 20-entry initial amateur ladder and 50-entry professional/default ladder;
- four-byte ranking entries containing u16 score + s16 progression index;
- public zero-based rank synchronization from ordered ladder position;
- the three current title holders at profile+0x50/+0x52/+0x54;
- the three previous title holders at profile+0x56/+0x58/+0x5A.

## Deliberate non-inventions

This foundation does not yet choose Career Mode 2.0 policy for:

- autonomous AI championship scheduling;
- mandatory challengers;
- eliminators;
- vacancy succession beyond the already-proven retail baseline;
- mathematical replacement of the retail ranking-score formula;
- public names for the individual result methods represented by codes 2..11.

That boundary matters because static RE proves that normal retail AI matchmaking
uses subtype 0 and does not independently create subtype-8 title challenges.
Richer AI championship behavior is therefore a Career Mode 2.0 extension, not
a hidden retail mechanism to rename.

## Weight movement boundary

Retail weight-class movement is a logical switch among the fixed three-slot
window. The slot setter does not change persistent boxer weight +0x6C.

A later Career Mode 2.0 body-weight policy can coordinate real weight gain/cuts
with this slot model. The foundation intentionally keeps those two operations
separate so logical division movement is not mistaken for physical growth.

## Match descriptor

The proven layout is:

    bits 16..30  opponent progression index (15 bits)
    bits  8..15  match/fight subtype
    bits  4..7   result/state code
    bits  0..3   secondary result/state code
    bit      31  unused by the retail packer

Known result classes:

- 0: unresolved/unset
- 1: draw
- 2..6: win classes
- 7..11: reciprocal loss classes
- 2 and 3: both increment the winner's KO statistic

The exact public method labels inside the win classes remain intentionally
unnamed.

## Next slice

With the storage/layout primitives locked, the next living-division slice can
add Career Mode 2.0 policy above them:

1. deterministic AI bout scheduling/result input interfaces;
2. title-bout eligibility and autonomous AI championship scheduling;
3. mandatory-challenger / vacancy policy;
4. ranking-policy integration without overwriting unresolved retail semantics.

Those policies should consume the primitives in
src/fnr3_re/overhaul/career2_living_divisions.py rather than duplicating retail
field layouts.
