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

The earlier second-writer ambiguity is also resolved. Function `0x001A38C4`
is the type-27 **state/apply** stage: its contract-type table at `0x005089A0`
maps type 27 to `0x001A3978`, which reaches the
`profile+0x00 = 1` store at `0x001A39E8`. Function `0x001A3B5C` is the
later **commit/finalization** stage and performs the same idempotent set-to-1
at `0x001A3C60`. Both are indirect methods, referenced at `0x00581A18`
and `0x00581A20` respectively.

The exact ULUS10066-v1.00 retail BOOT.BIN independently reproduces this
lifecycle. The bounded retail writer inventory finds three strong direct
writers to profile+0x00: initialization clears it at `0x0019D208`, while the
type-27 state/apply and commit paths set it to 1. No separate direct retail
comeback/unretire writer was found in that bounded scan.

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
- state/apply dispatch: `0x00508A00 -> 0x001A3978` inside `0x001A38C4`;
- state/apply retired-byte store: `0x001A39E8`;
- commit/finalization handler: `0x001A3B5C`;
- commit/finalization retired-byte store: `0x001A3C60`;
- type-27 post-fight dispatch entry is null, consistent with retirement being
  a non-fight contract.

The resolver still contains a conditional raw-27 -> type-25 remap whose
predicate is unnamed. That caveat does not weaken the direct type-27 writer
proof; it only means not every raw type-27 record necessarily reaches the
public Retire path unchanged.

## Retail fight-history record — fully decoded

The retail Career History screen uses two 20-entry rings: one Amateur and one
Professional. Every entry is exactly 25 bytes:

| Offset | Size | Meaning |
|---|---:|---|
| +0x00..+0x15 | 22 | opponent display-name string buffer |
| +0x16 | 1 | fight-result code |
| +0x17 | 1 | rounds lasted |
| +0x18 | 1 | TKO/KO time second-count |

The result code is now closed for every value produced by the retail history
writer:

- 0 = Win by KO (`$M_Win_KO`);
- 1 = Win by Decision (`$M_Win_Decision`);
- 2 = Loss by KO (`$M_Loss_KO`);
- 3 = Loss by Decision (`$M_Loss_Decision`);
- 4 = Draw (`$M_Draw`).

`GetCareerHistoryInfo` uses entry +0x18 only when it is nonzero and sends it
to formatter `0x00206E18`. That formatter divides the value by 60 and
formats the quotient/remainder, proving that the stored byte is a whole-second
time count rendered as minutes/seconds.

This closes the display semantics of all 25 bytes. It also establishes an
important Career Mode 2.0 limitation: the stock rings do **not** persist a
stable opponent ID, opponent rank at the time of the fight, division, career
date, or title stakes. They also retain only the most recent 20 amateur and 20
professional bouts. The stock history therefore cannot support accurate
full-career opposition-quality or multi-division legacy scoring by itself.

Those richer facts need a separate mod-owned legacy fight ledger in C2EX,
rather than repurposing bytes in the retail rings.

## Remaining priority-4 work

The retirement transition and retail fight-history display format are now
resolved. The remaining work is the **Career 2.0 legacy layer**:

1. define the compact C2EX legacy fight ledger for stable opponent identity,
   opponent rank, division, career date and title stakes;
2. identify the stock career-end/forced-retirement eligibility condition;
3. map career-longevity and division-history inputs;
4. lock the current-version legacy scoring policy.

The type-27 retirement writer and 25-byte stock fight-history record should not
be re-traced unless contradictory runtime evidence appears.
