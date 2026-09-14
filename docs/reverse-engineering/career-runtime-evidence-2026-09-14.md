# Retail career runtime evidence — 2026-09-14

This document records the controlled Fight Night Round 3 PSP retail career-mode evidence gathered in PPSSPP on 2026-09-14. The structured source of truth is `analysis/save/career-runtime-evidence-2026-09-14.json`.

No `.ppst`, RAM dump, ISO, BOOT.BIN, save payload, or other copyrighted/runtime binary is committed. The repository stores only hashes, observed values, addresses, screenshots-derived facts, and interpretations with explicit confidence boundaries.

## Why this matters for the overhaul

The overhaul needs concrete attachment points into the retail career engine. These checkpoints give us runtime anchors for player identity, rival state, money, record/KO bookkeeping candidates, training attributes, Career Central formatting, and scheduled-fight formatting. The immediate next reverse-engineering step is to place watchpoints or equivalent runtime traces on the confirmed fields and recover the retail functions that read or write them.

The controlled workflow also demonstrates that PPSSPP savestates are sufficient as offline RAM snapshots. Manual memory-dump capture is not required for each experiment.

## Checkpoint set

### Checkpoint 0 — historical late-career reference

Retail `ULUS10066-v1.00` career:

- Evan Lebrecht
- March 8, 2034
- Rank 29
- Record 20-0-0
- 20 KOs
- Rival: Keiji Obayashi
- Bank: $67,396

This state predates the controlled experiment but is valuable because it gives a far-progressed comparison against a clean career.

### Checkpoint 1 — new controlled career

- Jacob Morgan
- Amateur Middleweight
- February 4, 2026
- Unranked
- Record 0-0-0
- 0 KOs
- Rival: N/A
- Bank: $0

The runtime Career Central parameter string was found at `0x093C0BA4`:

```text
strBoxerName=Jacob Morgan&strWeightClass=AMATEUR MIDDLEWEIGHT&strWinLossRecord=0-0-0, 0 KO&strRank=UNRANKED&strMoney=$$0&strRivalName=N/A&strCROBoxer=strCareerBoxer&strCROBoxer=strCareerCentralBoxer&strDate=FEBRUARY 4, 2026&iRetired=0
```

This is useful because it exposes the semantic names the UI receives: `strWinLossRecord`, `strRank`, `strMoney`, `strRivalName`, `strDate`, and `iRetired`.

### Checkpoint 2 — first contract + first training

The first contract and first training had both happened before this state was saved. The only retained visible training result was **Power -4**.

RAM changes from checkpoint 1 included:

| Address | Before | After | Delta |
|---|---:|---:|---:|
| `0x08D9AABA` | 46 | 42 | -4 |
| `0x08D9AABC` | 46 | 42 | -4 |
| `0x08D9AAC2` | 36 | 34 | -2 |
| `0x08D9AAC8` | 40 | 38 | -2 |
| `0x08D9AACA` | 33 | 31 | -2 |

The first two fields therefore correlate strongly with the visible Power change. The later `-2` fields must remain unlabeled because the corresponding visible deltas were not retained.

### Checkpoint 3 — first scheduled fight

Known setup:

- Single Amateur Bout
- Jacob Morgan vs Blake Jacobs
- Venue: 65 Lower Flushing
- 4 x 2-minute rounds
- Player cut: $300 / 40%
- Rank change: N/A
- Bonus: N/A
- Headgear required
- Excessive cuts may stop fight
- 3-knockdown rule

A complete transient parameter string was present at `0x093F88C0`:

```text
strEventName=SINGLE AMATEUR BOUT&strBoxerLeftFirstName=Jacob&strBoxerLeftLastName=Morgan&strBoxerRightFirstName=BLAKE&strBoxerRightLastName=JACOBS&strVenueName=VENUE: 65 LOWER FLUSHING&strRoundInfo=4,2 MINUTE ROUNDS&strCutPercentage=YOUR CUT OF THE PURSE: $300 (40%25)&strSideObjective=RANK CHANGE: N/A
BONUS: N/A&strRules=HEADGEAR REQUIRED
EXCESSIVE CUTS MAY STOP FIGHT
3 KNOCKDOWN RULE
```

The persistent career fields below were unchanged from checkpoint 2, indicating that this state mainly added transient fight-setup/UI state.

### Checkpoint 4 — after first fight and career update

Career Central showed:

- Record: 1-0-0
- 1 KO
- Rival: Blake Jacobs
- Bank: $288
- Date: June 17, 2026
- Still unranked

Payout screen:

- Total purse: $750
- Jacobs: 60% / $450
- Morgan: 40% / $300
- Promoter: 4% / $12
- Trainer: $0
- Cutman: $0
- Net pay: $288

Fight totals captured on-screen included 191/307 landed/thrown for Morgan, 41/72 for Jacobs, and 6-0 knockdowns. All three judges displayed 40-30 totals.

The post-fight Career Central parameter string appeared at `0x09453DD4`:

```text
strBoxerName=Jacob Morgan&strWeightClass=AMATEUR MIDDLEWEIGHT&strWinLossRecord=1-0-0, 1 KO&strRank=UNRANKED&strMoney=$$288&strRivalName=BLAKE JACOBS&strCROBoxer=strCareerBoxer&strCROBoxer=strCareerCentralBoxer&strDate=JUNE 17, 2026&iRetired=0
```

The rival notification text appeared at `0x094531AC`.

### Checkpoint 5 — second training result

Visible deltas:

- Power +3
- Speed +0
- Agility +0
- Stamina +1
- Chin +0
- Body +1
- Heart +0
- Cuts +1

RAM changes from checkpoint 4:

| Address | Before | After | Delta |
|---|---:|---:|---:|
| `0x08D9AABA` | 42 | 45 | +3 |
| `0x08D9AABC` | 42 | 45 | +3 |
| `0x08D9AAC2` | 34 | 35 | +1 |
| `0x08D9AAC8` | 38 | 39 | +1 |
| `0x08D9AACA` | 31 | 32 | +1 |

This confirms a training-sensitive player attribute block around `0x08D9AABA-0x08D9AACA`. The two adjacent `+3` fields both track visible Power, but the reason for the duplication remains unresolved. The three `+1` fields cannot yet be individually labeled Stamina/Body/Cuts because those visible attributes all changed by the same amount in the same experiment.

## Confirmed and strong runtime fields

| Address | Type | Meaning | Confidence | Evidence |
|---|---|---|---|---|
| `0x08D98574` | `u32` | Career bank | Confirmed | `$67,396` in the historical state, `$0` in the clean career, `$288` after fight 1 |
| `0x08D98672` | string | Rival last name | Confirmed | `OBAYASHI` -> empty -> `JACOBS` |
| `0x08D98692` | string | Rival first name | Confirmed | `KEIJI` -> empty -> `BLAKE` |
| `0x08D9AA42` | string | Player last name | Confirmed | `Lebrecht` / `Morgan` |
| `0x08D9AA62` | string | Player first name | Confirmed | `Evan` / `Jacob` |
| `0x08D98504` | `u16` | Wins-or-KOs candidate A | Strong candidate | `20 -> 0 -> 1`; always equal to the observed KO count so far |
| `0x08D98506` | `u16` | Wins-or-KOs candidate B | Strong candidate | Same evidence as candidate A |
| `0x08D9AABA` | `u16` | Power-correlated attribute | Strong | `46 -> 42` for Power -4, then `42 -> 45` for Power +3 |
| `0x08D9AABC` | `u16` | Paired Power-correlated attribute | Strong | Mirrors the same two Power deltas |

Two additional money-related fields remain candidates:

- `0x08D98568`: historical `12656`, clean `0`, first-fight `288`
- `0x08D98578`: historical `174396`, clean `0`, first-fight `288`

They must not be labeled as total earnings, last purse, or another semantic until another controlled payout separates them.

## Savestate/RAM extraction finding

For this evidence set, PPSSPP revision-5 `.ppst` files use Zstandard compression. After the 48-byte chunk header and 128-byte title, decompression yields the serialized state. The 32 MiB PSP RAM image begins at decompressed offset `0x48` for all six captured states.

The working address translation for these extracted RAM images is:

```text
ram_file_offset = psp_address - 0x08000000
```

This was validated by matching the historical state's separately extracted RAM against the savestate-derived memory at multiple nonzero offsets.

This observation should be treated as verified for this captured PPSSPP state format/version set; do not silently assume every future PPSSPP version preserves the same serialized layout without checking.

## Next high-value experiments

1. **Decision win** — distinguish `0x08D98504` from `0x08D98506` by making wins increment while KOs remain unchanged.
2. **Training with distinct deltas** — use a result where Stamina, Body, and Cuts do not all move by the same amount, allowing `0x08D9AAC2`, `0x08D9AAC8`, and `0x08D9AACA` to be labeled individually.
3. **Another payout** — separate bank, last-payout, and possible cumulative-money fields.
4. **Runtime writer tracing** — watch confirmed fields and identify the retail BOOT.BIN functions that update them. Those functions are the actual implementation hooks needed for Career Mode 2.0/amateur overhaul work.

## Debug prototype note

The same session also inspected the separate `FNR3_PSP_Debug` prototype. That evidence is deliberately kept separate in `analysis/reference/debug-prototype-runtime-evidence-2026-09-14.json` so prototype observations cannot be mistaken for retail behavior.
