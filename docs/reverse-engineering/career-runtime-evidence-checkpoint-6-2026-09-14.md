# Retail career runtime evidence — checkpoint 6

This note extends `analysis/save/career-runtime-evidence-2026-09-14.json` with the second controlled amateur fight.

## Controlled outcome

Checkpoint 6 was captured after Jacob Morgan's second amateur bout, a decision win over Lopez.

Visible Career Central state:

- Record: `2-0-0, 1 KO`
- Rank: `UNRANKED`
- Rival: `BLAKE JACOBS`
- Bank: `$720`
- Date: `NOVEMBER 11, 2026`

Visible payout:

- Total purse: `$750`
- Morgan share: `60% = $450`
- Promoter expense: `4% = $18`
- Net pay: `$432`

Visible fight result:

- Morgan punches: `169 / 277` (`57%`)
- Lopez punches: `115 / 186` (`61%`)
- Knockdowns: Morgan `2`, Lopez `0`
- Judges: `39-35`, `39-35`, `40-34` for Morgan

## Record fields resolved

This checkpoint cleanly resolves the two previously ambiguous record counters:

| Address | Checkpoint 5 | Checkpoint 6 | Meaning | Confidence |
|---|---:|---:|---|---|
| `0x08D98504` | 1 | 2 | Career wins | Confirmed |
| `0x08D98506` | 1 | 1 | Career KO count | Confirmed |

The earlier samples could not separate these fields because every observed win was also a KO. The second fight was won by decision, so only the wins counter advanced.

## Bank field strengthened again

`0x08D98574` changed from `288` to `720`, exactly matching the Career Central bank after adding the visible `$432` net pay.

This independently reconfirms `0x08D98574` as the persistent career bank field.

Two additional money-related fields, `0x08D98568` and `0x08D98578`, also changed `288 -> 720`. Their exact semantics remain unresolved because the historical 20-0 career shows values different from the bank at these locations. They may represent accumulated earnings or another money-related total.

## Rival semantics strengthened

The most recent opponent was Lopez, but the rival remained Blake Jacobs. The persistent rival buffers still contain:

- `0x08D98672` = `JACOBS`
- `0x08D98692` = `BLAKE`

This confirms the rival fields represent persistent career rival state, not merely the most recent opponent.

## Training block control

The training-sensitive player boxer region around `0x08D9AABA-0x08D9AACA` did not change from checkpoint 5 to checkpoint 6. That is the expected control result for a fight-only transition after the prior training session and further supports separating boxer attributes from fight/career bookkeeping.

## Savestate payload boundary

The private checkpoint file and extracted RAM are not committed. Only hashes and derived observations are recorded in Git.

- Savestate SHA-256: `f142cfe8146017dab9229477b098a617f5da3e5be218d37fac7da5aed389cff3`
- Extracted 32 MiB RAM SHA-256: `e6a7c0bd1bb711aff3a72059f8c0f085d6ae376e6940985feabd619bfd332d44`

## Highest-value next experiments

1. Capture a loss to isolate loss/result fields near the record structure.
2. Capture a draw if the game permits one to isolate draw handling.
3. Make a non-fight purchase or expense so the bank field diverges from the two unresolved money accumulators.
4. Continue taking exact training-result screenshots with varied deltas so every member of the player attribute block can be labeled.
