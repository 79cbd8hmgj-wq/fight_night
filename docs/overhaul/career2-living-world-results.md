# Career Mode 2.0 — Living World Result Layer

This slice builds on the merged living-division foundation and implements the
proven persistent state transitions around scheduled fights and championships.

## Implemented

The host model now supports:

- reciprocal match assignment using progression-record +0x24/+0x28 semantics;
- the stock AI-match subtype 0 baseline;
- title-challenge subtype 8 and title-defense subtype 9 plumbing;
- exact reciprocal fight-result codes for both fighter perspectives;
- wins, losses, draws, and KO counter updates from the proven result classes;
- clearing schedule state after a resolved bout;
- current/previous championship-holder transfer;
- title-won and title-lost bookkeeping during holder transfer;
- separate title-defense and title-forfeiture counters;
- fail-closed overflow and malformed-transition checks.

## Policy boundary

This layer does **not** select fight outcomes.

Static evidence proves that the retail AI simulation considers ranking /
performance state and RNG, but the exact normalized outcome formula has not
been recovered to a point where we can safely reproduce it as Career Mode 2.0
policy. The result transition therefore receives the result code from a
separate policy layer and only performs the proven state update.

The same separation applies to championships. The title-match helper validates
the recovered subtype-8 / subtype-9 encoding but does not decide:

- who deserves a title shot;
- mandatory-challenger order;
- eliminator rules;
- whether a champion must defend;
- autonomous AI championship frequency.

Those are new Career Mode 2.0 policy decisions because the complete direct
retail scheduler inventory shows the ordinary AI matcher creates subtype 0
fights and does not independently schedule subtype-8 title challenges.

## Ranking boundary

The result layer deliberately does not invent a replacement ranking formula.
Retail ranking score is a u16 value stored at progression+0x20 and mirrored
into the active ladder. The existing foundation can synchronize public ranks
from an ordered ladder, but Career Mode 2.0 still needs a separately approved
ranking policy (or a fully normalized reconstruction of the retail formula)
before it should reorder fighters.

## Next implementation step

The remaining priority-2 work should now be concentrated into explicit policy
modules rather than more storage reconstruction:

1. AI matchup selection above the proven schedule primitives;
2. AI result/outcome policy;
3. ranking-score policy and ladder reorder;
4. autonomous AI championship / mandatory-challenger policy;
5. coordination between physical boxer weight and logical career-class moves.

All of those can now operate without guessing the underlying PSP save-field
layouts.
