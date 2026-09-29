# Career Mode 2.0 — Legacy Fight Ledger

Retail Career History is now fully decoded, but it is intentionally too small
for Career Mode 2.0 legacy scoring. Each stock entry is only 25 bytes and
contains:

- 22 bytes of opponent display-name storage;
- one result-code byte;
- one rounds-lasted byte;
- one KO/TKO-time byte.

Retail keeps only 20 amateur and 20 professional entries. It does not persist
a stable opponent identity, opponent rank at the time of the bout, division,
career date, title stakes, or an opponent-quality snapshot.

## C2EX-owned historical record

career2_legacy.py defines an append-only mod-owned record for those facts.
The record is **not** a reinterpretation of unused retail fields.

Each entry is exactly 16 bytes:

| Bytes | Meaning |
|---:|---|
| 2 | stable C2EX opponent identity |
| 2 | Career 2.0 week ordinal |
| 1 | opponent zero-based rank at fight (0xFF = unranked) |
| 1 | absolute retail WeightClass |
| 1 | Career 2.0 title-stakes flags |
| 1 | opponent overall snapshot |
| 4 | opponent W/L/D/KO snapshot |
| 1 | exact retail-compatible result code |
| 1 | rounds lasted |
| 1 | finish time in seconds |
| 1 | reserved, currently zero |

The compact row is designed to preserve historical evidence, not to freeze a
legacy-score formula.

## Stable identity boundary

The 16-bit opponent_id is explicitly C2EX-owned. It must not be assumed to be
identical to a retail progression-record index forever because generated-boxer
slot reuse has not been proven safe as a permanent identity system.

The future integration layer must assign and preserve the stable C2EX identity
when it records a completed bout.

## Historical opponent quality

Rank, overall and W/L/D/KO are snapshots from the time of the fight. This is
deliberate. Looking up the opponent's current values years later would distort
historical opposition quality as fighters develop, decline, change rank or
retire.

No weighting is applied yet. The ledger exposes aggregate evidence such as:

- wins/losses/draws and KO wins;
- ranked opponents and wins over ranked opponents;
- best rank defeated;
- title fights and successful player title defenses;
- eliminators;
- number of distinct divisions;
- span between first and last ledgered fight.

The eventual Career Mode 2.0 legacy policy can consume those values without
changing the persisted history.

## Calendar boundary

career_week is a Career 2.0-owned monotonic ordinal. It is not a claim about
the encoding of the retail career date. The later career-flow/calendar
integration will own the mapping from the game's calendar state to this
ordinal.

## Save-schema dependency

The row codec is complete, but the existing merged C2EX v1 block stores only
amateur-development state. The next save-schema step is a backward-compatible
C2EX revision that retains the v1 development prefix and adds a counted
variable-length ledger section while staying below the proven 0x1EBC-byte save
tail capacity.

Until that revision is implemented, the ledger model is host-side only and
must not be described as already persisted by the PSP save hook.
