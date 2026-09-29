# Career Mode 2.0 — Retirement and Legacy Foundation

This slice begins roadmap priority 4 after the amateur-development, living-
division, and C2EX/save-contract foundations.

## Proven retail retirement state

The retail career already has a first-class retirement flag:

- profile +0x00 is emitted by Career Central as iRetired;
- GetNextEventState tests the same byte;
- any nonzero value forces next-event code 4;
- the retail contract system also exposes a dedicated Retire contract family
  as resolved contract type 27.

The host model therefore treats retirement as a real persistent career state,
not as a Career 2.0-only overlay.

The current foundation exposes retirement as one-way. Although a future
Career 2.0 comeback feature is in scope conceptually, a retail unretire/comeback
writer path has not been proven yet. Clearing the flag is therefore not exposed
as if it were already understood retail behavior.

## Legacy inputs already mapped

The project can already assemble a useful evidence-backed retirement snapshot
from retail career state:

| Metric | Proven source |
|---|---|
| retired flag | profile +0x00 |
| money/bank balance | profile +0xA0 |
| current zero-based rank | progression record +0x04 |
| wins | progression record +0x05 |
| losses | progression record +0x06 |
| draws | progression record +0x07 |
| knockouts | progression record +0x08 |
| title wins | progression record +0x15 |
| title losses | progression record +0x16 |
| title defenses | progression record +0x17 |
| title forfeitures | progression record +0x18 |
| age | proven career-age path used by the amateur-development slice |

The model also derives total bouts and KO-win rate without changing retail
state.

## What is deliberately not scored yet

The Career Mode 2.0 design calls for a broader legacy evaluation than retail
currently exposes directly. The final formula should eventually account for
areas such as:

- quality of opposition;
- championships and defenses;
- accomplishments across multiple divisions;
- longevity;
- knockouts;
- technical performance;
- finances;
- health/career wear.

Only some of those inputs are presently mapped strongly enough to be named and
consumed. This slice therefore produces a LegacyEvidenceSnapshot rather than
hard-coding a legacy score or arbitrary weights.

That keeps two layers separate:

1. evidence-backed retail state;
2. Career Mode 2.0 scoring policy, which can be tuned after its remaining
   inputs are defined.

## Existing retirement contract path

The recovered contract system contains a dedicated special retirement contract:

- resolved type 27;
- exposed through iRetireContractID;
- contract-list case at debug/review 0x001FF6C0;
- type resolver at 0x001A2C98;
- the resolver can conditionally remap raw type 27 to type 25 through a still-
  unnamed predicate.

That makes the existing special-contract path a strong candidate for the
eventual player-driven retirement UI/transition, but this slice does not claim
the final writer site for profile+0x00 until that path is traced directly.

## Next static/implementation step

The next retirement/legacy pass should:

1. trace every writer of profile+0x00;
2. follow the accepted Retire contract path until the exact retirement write is
   reached;
3. map the existing career-end condition and distinguish it from voluntary
   retirement;
4. identify durable sources for opposition quality, division history and
   longevity;
5. only then lock the Career Mode 2.0 legacy scoring formula and any comeback
   policy.
