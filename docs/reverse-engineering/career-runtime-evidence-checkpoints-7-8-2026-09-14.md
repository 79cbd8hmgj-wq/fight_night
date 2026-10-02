# Retail career runtime evidence — checkpoints 7 and 8

These checkpoints extend the controlled ULUS10066 v1.00 Career Mode evidence with a fully resolved training-stat layout and a completed rival rematch.

## Checkpoint 7 — training and rival contract

Visible training result:

- Power `+0`
- Speed `+3`
- Agility `+1`
- Stamina `+0`
- Chin `+1`
- Body `+0`
- Heart `+1`
- Cuts `+0`

The persistent boxer block changed exactly as the screen reported:

| Address | Meaning | Before | After |
|---|---|---:|---:|
| `0x08D9AABA` | Power | 45 | 45 |
| `0x08D9AABC` | Power paired/mirror field | 45 | 45 |
| `0x08D9AABE` | Speed | 31 | 34 |
| `0x08D9AAC0` | Agility | 26 | 27 |
| `0x08D9AAC2` | Stamina | 35 | 35 |
| `0x08D9AAC4` | Chin | 38 | 39 |
| `0x08D9AAC6` | Heart | 35 | 36 |
| `0x08D9AAC8` | Cuts | 39 | 39 |
| `0x08D9AACA` | Body | 32 | 32 |

The runtime training payload independently exposes the stat order:

`45,31,26,35,38,32,35,39,6`

with deltas:

`0,3,1,0,1,0,1,0,0`

This resolves the visible order as:

`Power, Speed, Agility, Stamina, Chin, Body, Heart, Cuts, derived/overall`

The only remaining wrinkle is the second persistent Power-correlated field at `0x08D9AABC`, whose exact role is still unresolved.

### Rival contract/event payload

The rival offer is not just normal matchmaking with a different opponent name. Runtime strings show a distinct `RIVAL FIGHT` event with independent parameters:

- Opponent: Blake Jacobs
- Total purse: `$5,200`
- Player cut: `$2,600` (`50%`)
- Promoter cut: `5%`
- Venue: `65 LOWER FLUSHING`
- Weeks until fight: `2`
- `4 x 2` minute rounds
- Rank change: `N/A`
- Headgear required
- Excessive cuts may stop fight
- 3-knockdown rule
- Bonus objective: `WIN WITH AN ILLEGAL BLOW TO THE HEAD FOR $7,500`

The same offer list also contained ordinary `$750` bouts against Genaro Perez and Max Horton. This is direct evidence that special career events and normal offers coexist inside the same contract-selection system.

The runtime fight-card payload at `0x093F800D` assembles opponent names, venue, round format, purse cut, side objective, and rules into one event description. This is a strong implementation target for a deeper Career Mode 2.0 contract/event system.

## Checkpoint 8 — rival rematch completed

After the Blake Jacobs rematch, Career bookkeeping reports:

- Record: `3-0-0`
- KO count: `2`
- Rank: `UNRANKED`
- Rival: `BLAKE JACOBS`
- Bank: `$3,190`
- Date: `DECEMBER 2, 2026`

The KO counter moved `1 -> 2`, so the rematch was recorded as a KO/TKO win by Career Mode.

Visible payout:

- Total purse: `$5,200`
- Jacobs: `50% = $2,600`
- Morgan: `50% = $2,600`
- Promoter expense: `5% = $130`
- Net pay: `$2,470`

`0x08D98574` moved exactly `720 -> 3190`, reconfirming the career-bank field.

The training block stayed unchanged through this fight-only transition, which is another useful control.

### Rival state persists after the rematch

The persistent rival buffers still contain:

- `0x08D98672` = `JACOBS`
- `0x08D98692` = `BLAKE`

The post-fight presentation also shows a dedicated newspaper-style `WILL THEY MEET AGAIN?` event.

Together, these show that rivalry is not a one-fight flag that clears after the rematch. It is a persistent, multi-event career subsystem with dedicated matchmaking and narrative presentation.

Three nearby bytes also changed only after this special rival-fight transition:

- `0x08D98628`: `0 -> 1`
- `0x08D9862A`: `0 -> 1`
- `0x08D9862E`: `0 -> 1`

Their exact meanings are not yet proven, but they are strong candidates for rivalry-history or post-special-event state and should be traced later rather than named prematurely.

### Calendar observation

Checkpoint 7's Career state was `NOVEMBER 11, 2026`; checkpoint 8 is `DECEMBER 2, 2026`, a 21-day advance. The rival contract displayed `WEEKS UNTIL FIGHT: 2`.

That discrepancy is useful evidence for later scheduling RE, but it is not yet enough to infer the game's exact calendar formula. Contract lead time, training advancement, and post-fight advancement may be separate contributions.

## Overhaul implications

These checkpoints materially reduce what still needs runtime collection:

- The eight visible training stats are now mapped in retail RAM.
- Routine training-result savestates have diminishing value unless tracing the writer or the derived overall formula.
- The career contract system demonstrably supports special event types, custom purses, purse splits, promoter cuts, lead times, custom rules, side objectives, and persistent opponent relationships.
- Rivalries survive a rematch and can drive dedicated narrative events.
- Jacob is still `UNRANKED` at `3-0`, so the next major progression evidence should target the first numeric rank and the amateur-to-pro transition.

## Updated capture priority

Do **not** deliberately manufacture a loss merely to fill out record fields. That is lower priority for the planned overhaul.

The next useful savestate should be reserved for a meaningful progression transition, especially:

1. first `UNRANKED -> numeric rank` transition;
2. amateur-to-pro transition and its triggering event/offer;
3. a material rival-state change or another special rival event;
4. a contract whose event type, rank-change promise, rounds, sponsor status, weight-class change, or future-contract count differs materially from the current amateur template.

Private `.ppst` and extracted RAM payloads remain outside Git; only hashes and derived evidence are committed.
