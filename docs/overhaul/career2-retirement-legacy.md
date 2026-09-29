# Career Mode 2.0 — Retirement and Legacy Foundation

This slice covers roadmap priority 4 after the amateur-development, living-
division, and C2EX/save-contract foundations.

## Proven retail retirement state

The retail career has a first-class persistent retirement state:

- profile +0x00 is emitted by Career Central as `iRetired`;
- `GetNextEventState` tests the same byte;
- any nonzero value forces next-event code 4;
- new-career initialization clears the flag at `0x0019D208`;
- contract type 27 is the dedicated Retire contract family.

The retirement transition itself is now statically closed.

### Exact voluntary-retirement write

The indirect handler at `0x001A3B5C` reads the selected/live contract type
from record `+0x34` and compares it with literal `27`.

On that type-27 path:

1. the career profile pointer is reloaded from career `+0x3C`;
2. literal `1` is loaded into `$a1`;
3. `0x001A3C60` executes `sb $a1, 0x0($a0)`;
4. therefore persistent `profile+0x00 = 1`.

The handler is referenced by a function pointer at `0x00581A20` and has no
direct JAL callers in the executable, consistent with an indirect
object/vtable-style contract-finalization dispatch.

The same path also clears/reset several adjacent contract/career fields,
including profile `+0x13C/+0x140`, fight-session/career `+0x19A2`, and the
selected contract's active state. This confirms type 27 is not merely a UI
label: accepting/finalizing it commits the retired state.

A second function, `0x001A38C4`, also has a proven
`profile+0x00 = 1` write at `0x001A39E8` and is referenced at
`0x00581A18`. Its internal contract-type jump-table case is not yet named, so
it remains separate evidence rather than being folded into the voluntary
type-27 path.

## Legacy inputs already mapped

The project can already assemble an evidence-backed retirement snapshot:

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

The host model derives total bouts and KO-win rate without changing retail
state.

## What is deliberately not scored yet

The final Career Mode 2.0 legacy formula should account for more than the
currently mapped counters. Remaining inputs include:

- quality of opposition;
- accomplishments across multiple divisions;
- career longevity;
- technical performance;
- finances;
- health/career wear.

The current implementation therefore exposes a `LegacyEvidenceSnapshot`
rather than inventing a weighting formula. Evidence-backed retail state and
Career Mode 2.0 scoring policy remain separate layers.

## Contract type 27 surfaces

The recovered type-27 path now spans multiple retail systems:

- resolver: `0x001A2C98`;
- contract-list dispatch: `0x0050E224 -> 0x001FF6A4`;
- special scheduler: `0x00508CC4 -> 0x001A5430`;
- persistent retirement handler: `0x001A3B5C`;
- retired-byte store: `0x001A3C60`.

The resolver still contains a conditional raw-27 -> type-25 remap whose
predicate is unnamed. That caveat does not weaken the direct type-27 writer
proof; it only means not every raw type-27 record necessarily reaches the
public Retire path unchanged.

## Remaining priority-4 work

The retirement state transition is resolved. The remaining work is the
**legacy side**:

1. resolve the separate `0x001A38C4` profile+0x00 writer case;
2. decode the 25-byte career-history entries far enough to retain opponent,
   result, class/date and stakes information;
3. identify the stock career-end/forced-retirement eligibility condition;
4. define durable inputs for opposition quality, multi-division achievement
   and longevity;
5. then lock the Career Mode 2.0 legacy formula and any comeback policy.
