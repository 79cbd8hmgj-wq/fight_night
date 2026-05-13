# PPSSPP debugger test plan

Purpose: manually prove which runtime values are real gameplay/career state and then connect those addresses back to `BOOT.BIN` functions in Ghidra. Do not edit original files, rebuild ISOs, or patch executables for these tests.

General workflow for every test:

1. Use `BOOT.BIN` as the Ghidra static reference.
2. In PPSSPP, reproduce the screen/situation, pause at stable moments, and run memory searches for visible or inferred values.
3. Narrow candidates by changing only one variable at a time.
4. Put write watchpoints on candidate addresses.
5. When a watchpoint hits, record the PSP PC address and map it back to the corresponding Ghidra function/address range.
6. Treat a value as display-only until changing/freezing it affects gameplay/career logic, not just the drawn number/bar.

## Stamina memory

- Situation: in-fight round with visible stamina/energy behavior; use training/free fight if available for repeatability.
- Visible value: stamina/energy bar drain and recovery. If no numeric value is shown, use unknown initial value searches.
- Search type: unknown initial value, then decreased after throwing punches, increased after resting, unchanged while paused. Try 8-bit/16-bit/32-bit integer and float searches.
- Changes to test: throw repeated punches, block/rest, get between-round recovery.
- Proves real gameplay data: freezing/increasing candidate allows sustained punching or changes fatigue effects; write watchpoint hits during punch/rest logic.
- Suggests UI-only data: freezing only affects the bar or immediately gets overwritten by another authoritative value.
- Connect to Ghidra: compare watchpoint PC to xrefs for `stamina`, `energy and health`, and damage/combat modifier strings in `BOOT.BIN`.

## Health/damage memory

- Situation: in-fight exchange where one boxer takes clean punches and blocked punches.
- Visible value: health/condition bar, knockdown risk, visible damage reactions.
- Search type: unknown initial value; decreased after clean hits; unchanged/decreased less after blocked hits. Test floats and integers.
- Changes to test: receive clean head/body shots, block shots, pause between exchanges.
- Proves real gameplay data: freezing prevents knockdowns/health loss or changing value changes survivability.
- Suggests UI-only data: value only controls visible bar while knockdowns/damage continue normally.
- Connect to Ghidra: watchpoint PC should be checked against xrefs for `dec damage taken from clean punch`, `dec damage taken from blocked punch`, `dec damage taken from body punch`, `dec damage taken from head punch`, and `ai/mods/p%d/energy and health`.

## Punch damage effects

- Situation: repeatable spar/fight scenario with same boxer matchup.
- Visible value: opponent health drain, stun, knockdown frequency.
- Search type: start from health target found above; use write watchpoints when a punch lands. Also search for damage scalar candidates if PPSSPP supports changed/unchanged float scans.
- Changes to test: jab vs hook vs uppercut; clean vs blocked; head vs body.
- Proves real gameplay data: modifying suspected scalar changes resulting health loss/knockdown without merely changing UI.
- Suggests UI-only data: hit reactions and health changes do not follow edited candidate.
- Connect to Ghidra: trace PCs to functions referencing `inc jab damage`, `inc hook damage`, `inc uppercut damage`, `inc all attack damage`, and the `bodypunch_modifier`/`block_modifier` strings.

## Career money/purse

- Situation: career screen that displays money, purse, contract offer, or post-fight payout.
- Visible value: exact displayed cash/purse amount.
- Search type: exact 32-bit integer for displayed amount; repeat with BCD/string only if integer search fails.
- Changes to test: accept a fight, complete a fight, buy an item/training if available, or move between screens that recalculate purse.
- Proves real gameplay data: editing/freezing changes affordability, saved career money, or contract acceptance results.
- Suggests UI-only data: only displayed number changes or value is regenerated from another address.
- Connect to Ghidra: use watchpoint PCs and xrefs for `purse`, `money`, `contracts.viv`, and `contract/contracts.viv`.

## Training result values

- Situation: career training minigame/result screen.
- Visible value: points, grade, stat increase, or result numeric value.
- Search type: exact integer for score/result; unknown changed/increased after successful actions; compare before/after result application.
- Changes to test: perform poorly vs well, accept/apply results, exit without applying if possible.
- Proves real gameplay data: changing candidate affects awarded stat increase or persisted training result.
- Suggests UI-only data: result display changes but applied stats/rewards do not.
- Connect to Ghidra: trace xrefs/watchpoints to `xdbtrain.adf`, `trainer.fnc`, `training`, and any result-format strings nearby.

## Fighter rating values

- Situation: boxer select/profile/career roster screen showing ratings, rank, weight/class, power/speed/endurance if visible.
- Visible value: exact rating number or rank/class value.
- Search type: exact 8-bit/16-bit/32-bit integer for visible ratings; compare two fighters with known different values.
- Changes to test: switch fighters, train to change ratings, load different weight class.
- Proves real gameplay data: editing candidate changes matchup logic, fighter performance, or persistent profile stats.
- Suggests UI-only data: only profile display changes and fight performance is unaffected.
- Connect to Ghidra: use `xdbboxr.adf`, `aiRanking`, `rank`, `weight`, `class`, `power`, `speed`, and `endurance`/rating-related xrefs.

## Venue selection

- Situation: venue selection screen or fight loading into a known venue.
- Visible value: selected venue name/index and loaded arena.
- Search type: exact/changed integer for selection index; changed/unchanged while moving cursor; string/path watch if debugger supports it.
- Changes to test: move between venues, start fight, reload save.
- Proves real gameplay data: editing index changes loaded venue or match setup, not just menu highlight.
- Suggests UI-only data: highlight changes but fight loads original venue.
- Connect to Ghidra: xrefs for `xdbvenue.adf`, `Venue Script`, `venue`, and `.zlb`/venue package strings.

## HUD values

- Situation: active fight HUD and menus that show bars, timer, scorecards, punch stats.
- Visible value: HUD bar lengths, timer/round, punch stats, scorecard values.
- Search type: exact for timer/round/score numbers; unknown changed for bar widths; watch display buffers after gameplay-state values are found.
- Changes to test: let timer run, throw punches to alter stats, pause/unpause, enter scorecards.
- Proves real gameplay data: changing source state changes rules/outcome, not only rendered text/bar.
- Suggests UI-only data: editing candidate changes rendering but not timer, scoring, health, or rules.
- Connect to Ghidra: use xrefs for `fnhud`, `hud`, `Punch Stats`, `Scorecards`, `StartAPTRender`, and `StopAPTRender`; distinguish HUD renderer writes from gameplay state writes.
