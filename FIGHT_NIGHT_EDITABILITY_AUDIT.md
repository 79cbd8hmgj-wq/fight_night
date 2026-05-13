# Fight Night Round 3 PSP Editability Audit

Audit date: 2026-05-13  
Repository audited: `/workspace/fight_night`  
Scope: read-only inspection of the unpacked repository plus creation of this report. No gameplay assets were patched, deleted, rebuilt, or overwritten.

## Executive summary

This repository is **not a complete PSP ISO dump**. It does not contain `PSP_GAME/`, `PARAM.SFO`, `SYSDIR/EBOOT.BIN`, `SYSDIR/BOOT.BIN`, PRX modules, PMF videos, or obvious raw audio files. The repo appears to contain mostly extracted EA data/resource folders from Fight Night Round 3 PSP: many EA `BIGF`/`BIG4` archives, zlib-wrapped venue packages, front-end UI packages, animation archives, data tables, and a few loose binary support files.

The most realistic editability path is:

1. **Extract and study EA BIG/VIV archives safely in a separate working folder.** Most files are `BIGF` or `BIG4` containers with visible internal filenames.
2. **Prioritize `preload/tables.viv`, `preload/db.viv`, and `contract/contracts.viv`.** These contain table/database/function-like resources whose internal names strongly suggest boxer, venue, store, training, rival, cutman, trainer, hair, shorts, and equipment data.
3. **Treat UI/HUD packages as medium-risk.** The `.big` UI packages contain `.apt`, `.const`, `.o`, and `.msh` members. They contain readable labels and variable names, but actual editing likely requires EA APT/Flash-like tooling or format research.
4. **Treat gameplay tuning as unproven until the data formats are decoded.** The repo contains promising data names, but no plain CSV/JSON/XML that can be edited directly with confidence. Many apparent text/table resources begin with `10 fb` and appear encoded or compressed, so they are not plain text despite having `.csv`, `.txt`, `.adf`, or `.fnc` names.
5. **Executable/code work cannot be audited fully from this repo.** No PSP executable or modules are present, so hardcoded gameplay formulas, AI, stamina, punch damage, and difficulty scaling may live outside this repo in missing `EBOOT.BIN`/`BOOT.BIN` or PRX files.

Bottom line: **visible UI/venue/texture/model changes look plausible after extraction/conversion; data-driven roster/training/store/venue changes are possible but need format research; core gameplay balancing is probably hardcoded or encoded and needs deeper reverse engineering.**

## Commands and methods used

Read-only inventory and scan commands were used, including:

```bash
find . -path ./.git -prune -o -print | sort
find . -path ./.git -prune -o -type f -print0 | xargs -0 strings -a -td -n 4
python3 scripts run from the shell to read archive headers, list BIG/VIV entries, scan printable strings, and zlib-decompress `.zlb` files in memory only
```

The environment did not have the Unix `file` utility installed, so magic/header identification was performed with Python byte reads instead.

## Repo inventory

### Full folder/file structure

```text
.
beanim.viv
careermodebe
careermodebe/earningdetails.big
careermodebe/paycheck.big
careermodefe1
careermodefe1/boxerbiooverlay.big
careermodefe1/careerranks.big
careermodefe1/careertrophycase.big
careermodefe1/fightstore.big
careermodefe1/mycareerstats.big
careermodefe1/viewaward.big
careermodefe1/viewmatchuprivals.big
careermodefe2
careermodefe2/careerhalloffame.big
careermodefe2/careersummary.big
careermodefe2/confirmcareer.big
careermodefe2/createchampbuild.big
careermodefe2/createchampheadfeatures.big
careermodefe2/createchampheadshape.big
careermodefe2/createchampinfo.big
careermodefe2/createchampphysique.big
careermodefe2/createchampratings.big
careermodefe2/fightinfo.big
careermodefe2/ringentrance.big
careermodefe2/selectalegend.big
careermodefe2/selectfightcontract.big
careermodefe2/selectmode.big
careermodefe2/signcontract.big
careermodefe2/training.big
careermodefe2/trainingresults.big
components
components/adhocInetGameInfoPopup.big
components/alpha.big
components/bgGradient.big
components/footer.big
components/footerbe.big
components/header.big
components/move.big
components/pspCreditsRoll.big
components/pspEATrax.big
components/pspFastImageLoader.big
components/pspIconListBox.big
components/pspIconListBox2.big
components/pspItemScroller.big
components/pspMenuEditor.big
components/pspMiniSlider.big
components/pspMultiStatBar.big
components/pspMultiStatBarToggle.big
components/pspOptionScroller.big
components/pspPopUpListBox.big
components/pspScrollbar.big
components/pspShoulderToggle.big
components/pspStars.big
components/pspStatBar.big
components/pspStdAnalogToggle.big
components/pspStdScrollbar.big
components/pspStdSlider.big
components/pspStdSliderBE.big
components/pspStdToggle.big
components/pspStdToggleBE.big
components/pspStdToggleSlider.big
components/pspStdToggleSliderBE.big
components/pspTrophyCase.big
components/pspbgeditor.big
components/pspcro.big
components/psphelp.big
components/psphighlight.big
components/psphighlightbe.big
components/pspimageholder.big
components/pspoverlay.big
components/pspoverlaybe.big
components/pspoverlayfe.big
components/psppausewaittimer.big
components/pspstdart.big
components/pspstdart2.big
components/pspstdart2be.big
components/pspstdart3.big
components/pspstdartbe.big
components/pspstdbutton.big
components/pspstdbuttonbe.big
components/pspstdpopup.big
components/pspstdpopupbe.big
components/pspsxb.big
components/pspsxbbe.big
components/scale.big
contract
contract/contracts.viv
data
data/fusion.bts
enviro
enviro/atlntic.zlb
enviro/atlntict.zlb
enviro/cafrica.zlb
enviro/cafricat.zlb
enviro/countyf.zlb
enviro/countyft.zlb
enviro/dodge.zlb
enviro/dodget.zlb
enviro/elevese.zlb
enviro/eleveset.zlb
enviro/hbtokyo.zlb
enviro/hbtokyot.zlb
enviro/loflush.zlb
enviro/loflusht.zlb
enviro/minick.zlb
enviro/minickt.zlb
enviro/misc.bh
enviro/misc.viv
enviro/sparrin.zlb
enviro/sparrint.zlb
enviro/staples.zlb
enviro/staplest.zlb
enviro/trainin.zlb
enviro/trainint.zlb
enviro/viceroy.zlb
enviro/viceroyt.zlb
feanim.viv
fighthype
fighthype/fighthype0.big
fighthype/fighthype1.big
fighthype/fighthype10.big
fighthype/fighthype11.big
fighthype/fighthype2.big
fighthype/fighthype3.big
fighthype/fighthype4.big
fighthype/fighthype5.big
fighthype/fighthype6.big
fighthype/fighthype7.big
fighthype/fighthype8.big
fighthype/fighthype9.big
fighthype/retirehanggloves.big
framework
framework/componentclasses.big
framework/componentclassesbe.big
framework/screenconstants.big
framework/screenconstantsbe.big
framework/transitionconstants.big
framework/transitionconstantsbe.big
gamemodesFE
gamemodesFE/hardHitsLoading.big
gamemodesFE/hardhitssettings.big
gamemodesbe
gamemodesbe/kdsscorecard.big
gamemodesbe/pauseoptionsparring.big
hud
hud/fnhud.hud
icons
icons/analog_psp.big
icons/c_psp.big
icons/dlr_psp.big
icons/dud_psp.big
icons/l1_psp.big
icons/lan_psp.big
icons/r1_psp.big
icons/r2_psp.big
icons/r_psp.big
icons/s_psp.big
icons/sel_psp.big
icons/str_psp.big
icons/t_psp.big
icons/x_psp.big
menu
menu/debugmenu.big
menu/genericbackground.big
menu/internetmainmenu.big
menu/mainmenu.big
menu/tutorialoverlay.big
mycornerfe
mycornerfe/adhocrivals.big
mycornerfe/careerfighthistory.big
mycornerfe/recordbooks.big
pad1.pad
pausemenu
pausemenu/pausemenu.big
pausemenu/pausemenump.big
playNowBE
playNowBE/befeLoadScreen.big
playNowBE/fighttotals.big
playNowBE/judgesscores.big
playNowBE/minigamepopup.big
playNowBE/pauseoptionsettings.big
playnowfe
playnowfe/controllerconfig.big
playnowfe/febedodgeloadscreen.big
playnowfe/febeloadscreen.big
playnowfe/optionsettings.big
playnowfe/selectboxer.big
playnowfe/selectcorner.big
playnowfe/selectvenue.big
preload
preload/bootpreloads.viv
preload/boxerpre.viv
preload/db.viv
preload/tables.viv
profilemanager
profilemanager/profileselect.big
rivalChallenge
rivalChallenge/faqloadscreen.big
rivalChallenge/febeloadscreen.big
rivalChallenge/rivalchallengefe.big
rivalChallengeBE
rivalChallengeBE/awards.big
rivalChallengeBE/challengeScorecard.big
rivalChallengeBE/challengeScorecard2.big
rivalChallengeBE/challengedescription.big
rivalChallengeBE/finalResults.big
rivalChallengeBE/unlocked.big
scranim.viv
scripts
scripts/scripts.viv
scripts/scrptpal.viv
system
system/autosaveicon.big
system/psptrcpopup.big
system/systemdebugscreen.big
```

### Extension inventory

| Extension | Count | Evidence / meaning |
|---|---:|---|
| `.big` | 152 | EA BIG archives, all observed with `BIGF` headers. These are containers, usually UI screen packages containing `.apt`, `.const`, `.o`, `.msh`. |
| `.zlb` | 24 | Zlib-wrapped venue/environment containers. Header is 4-byte little-endian uncompressed size followed by zlib stream beginning with `78 da`; decompressed payload begins with `BIG4`. |
| `.viv` | 11 | EA VIV/BIG archives, observed as `BIGF` or `BIG4`. Contains animations, databases, scripts, tables, model headers, and miscellaneous venue models. |
| `.pad` | 1 | `pad1.pad`, 10 MiB of apparent zero padding. Not useful for gameplay improvement. |
| `.bh` | 1 | `enviro/misc.bh`, starts `VIV4`; likely EA hash/header/index sidecar for `enviro/misc.viv`. Unsafe to edit directly. |
| `.hud` | 1 | `hud/fnhud.hud`, custom binary HUD layout/resource file containing readable markers such as `POLY` and `fill`. Potentially editable only after format research. |
| `.bts` | 1 | `data/fusion.bts`, 130 bytes of ASCII/hash-like data. Probably build/config/checksum metadata, not an obvious gameplay target. |

### Largest files / likely large containers

| File | Size | Type / header | Notes |
|---|---:|---|---|
| `scranim.viv` | 12,899,664 | `BIGF` | Large screen/animation archive with 34 internal animation files. |
| `pad1.pad` | 10,485,760 | all-zero header | Padding/filler, not a gameplay asset. |
| `beanim.viv` | 3,899,640 | `BIGF` | In-game boxer/face/between-round animation archive. |
| `enviro/misc.viv` | 2,014,346 | `BIGF` | Miscellaneous venue models, HUD model assets, mesh resources. |
| `enviro/*.zlb` | 1,860 to 716,543 packed | zlib + `BIG4` payload | Venue/environment archives with meshes, lighting, placements, particles, ORL/ORD/SFX resources. |
| `scripts/scrptpal.viv` | 539,540 | `BIGF` | Script palette archive; many `.bin` members matching script names in `scripts/scripts.viv`. |
| `feanim.viv` | 340,236 | `BIGF` | Front-end animation archive. |

## File type classification table

| File/folder group | Classification | Why | Practical editability |
|---|---|---|---|
| `preload/tables.viv` | Probably editable after extraction/conversion | Internal names include `.csv` and `.txt` resources such as `actors.csv`, `hairtable.csv`, `shorts.csv`, and many hair physics text files. Contents are not plain CSV/TXT because they begin with encoded/compressed bytes (`10 fb`). | High-value first target for appearance/equipment data, but requires decoding/repacking. |
| `preload/db.viv` | Possibly editable but needs format research | Contains `xdbboxr.adf`, `xdbvenue.adf`, `xdbstore.adf`, `xdbtrain.adf`, `xdbrivl.adf`, and related database-looking files. | Highest-value target for roster, venue, store, training, rival/progression data if ADF format is decoded. |
| `contract/contracts.viv` | Possibly editable but needs format research | Contains `cutman.fnc`, `fights.fnc`, `trainer.fnc`; readable tags include `CUTS`, `FITE2`, `TRNR`. | Could affect contracts, cutmen/trainers, fight setup, but format is unknown. |
| `careermodebe/`, `careermodefe1/`, `careermodefe2/` | Probably editable after extraction/conversion | UI packages for career screens; readable variable names include purse, training, ratings, contracts, rankings. | Good for UI text/layout and possibly display logic, not proven for underlying gameplay values. |
| `playnowfe/`, `playNowBE/`, `pausemenu/`, `gamemodesFE/`, `gamemodesbe/`, `mycornerfe/`, `profilemanager/`, `rivalChallenge/`, `rivalChallengeBE/` | Probably editable after extraction/conversion | Screen packages with `.apt`, `.const`, `.o`, `.msh` internals. | Good for menus, loading screens, scorecards, settings, selection screens. |
| `components/`, `framework/`, `icons/`, `menu/`, `system/` | Probably editable after extraction/conversion | Shared UI/component BIG archives. | Useful for HUD/menu visuals, button icons, debug screens, background screens; risk of breaking shared UI if repacked incorrectly. |
| `hud/fnhud.hud` | Possibly editable but needs format research | Custom binary HUD file with structured table and readable `POLY`/`fill` strings. | Potentially important for in-fight HUD position/geometry; do not edit until decoded. |
| `enviro/*.zlb` | Probably editable after extraction/conversion | Each is a zlib-wrapped `BIG4` archive containing venue meshes, lighting, placement text, particles, ORL/ORD/SFX resources. | Strong target for venue/ring/lighting/crowd visual edits after decompression and repacking. |
| `enviro/misc.viv` and `enviro/misc.bh` | Possibly editable but needs format research | `misc.viv` contains many `.msh` resources including `hud.msh` and `fuihud.msh`; `.bh` looks like sidecar/index. | Visual/model target, but sidecar relationship must be understood. |
| `beanim.viv`, `feanim.viv`, `scranim.viv` | Possibly editable but needs format research | Animation archives with many `.bin` and `.zlb` members and readable animation state names. | Animation replacement/reorder may be possible, but high risk without animation format tooling. |
| `scripts/scripts.viv`, `scripts/scrptpal.viv` | Possibly editable but needs format research | Large sets of named `.bin` scripts. Names suggest reusable scripted behaviors or presentation logic. | Could be important, but format is binary. Treat as reverse-engineering target. |
| `data/fusion.bts` | Not useful for gameplay improvement | Small ASCII/hash-like file, no obvious gameplay fields. | Leave alone unless a boot/build dependency is discovered. |
| `pad1.pad` | Not useful for gameplay improvement | 10 MiB zero-filled padding. | Do not edit; likely ISO alignment/filler. |
| Missing `EBOOT.BIN`, `BOOT.BIN`, PRX | Probably code/binary-only if uploaded later | PSP executable code is absent from this repo. | Required for full hardcoded gameplay audit. |

## Suspected editable files and assets

### Text/config/table/script-like resources

No loose plain XML/JSON/CSV files were found. However, containers expose many promising internal names:

- `preload/tables.viv` internal table/text entries:
  - `actors.csv`
  - `cabstore.csv`
  - `facemorph.csv`
  - `facialhair.csv`
  - `haircolor.csv`
  - `hairtable.csv`
  - `morphslots.csv`
  - `shoes.csv`
  - `shorts.csv`
  - many hair physics `.txt` files such as `actorhair1.txt`, `braid.txt`, `punchout.txt`, `refhair.txt`, `shortstraight.txt`
- `preload/db.viv` internal database entries:
  - `xdbboxr.adf`
  - `xdbvenue.adf`
  - `xdbalias.adf`
  - `xdbevent.adf`
  - `xdbhmtwn.adf`
  - `xdbstore.adf`
  - `xdbpref.adf`
  - `xdbrivl.adf`
  - `xdbtrain.adf`
  - `xdbcutpn.adf`
- `contract/contracts.viv` internal entries:
  - `cutman.fnc`
  - `fights.fnc`
  - `trainer.fnc`
- `scripts/scripts.viv` and `scripts/scrptpal.viv` contain many `.bin` script-like resources.

Important honesty note: although some internal filenames say `.csv` or `.txt`, their extracted bytes are **not immediately plain text**. They contain readable fragments but begin with non-text headers such as `10 fb`. This means edits require format decoding, decompression, or a purpose-built EA table codec before values can be changed safely.

### Images/textures

No loose `PNG`, `BMP`, `DDS`, `TGA`, `GIM`, or `TIM2/TM2` files were found. Texture-like data is probably embedded inside:

- `.msh` resources in UI `.big` archives.
- `.msh`, `.orl`, `.ord`, `.sfx`, and `.lit` resources inside decompressed venue `.zlb` archives.
- `enviro/misc.viv` mesh resources such as `hud.msh`, `fuihud.msh`, and miscellaneous prop meshes.

Likely tools/research paths: EA BIG/VIV extractors, Noesis with EA model/mesh plugins if available, TextureFinder/RawTex for PSP swizzled textures, and custom MSH/ORL/ORD analysis.

### Audio/music

No loose `AT3`, `WAV`, `VAG`, `ADX`, or obvious audio extensions were found. Some venue `.zlb` archives contain `.sfx` members, but those may be shader/effect files or sound effects depending on EA naming in this title. `components/pspEATrax.big` is a UI package for the EA Trax screen, not evidence of actual music audio by itself.

Practical conclusion: audio/music is **not directly editable from obvious files in this repo**. Search/extract the original ISO for audio banks if audio replacement is a goal.

### Video/cutscenes

No `.pmf` files were found. Cutscenes/videos are **not present in this repo**, or they are stored in non-obvious containers not identifiable from current evidence.

### Fonts/UI/menu/HUD

UI is heavily represented and likely modifiable after extraction/conversion:

- Front-end and back-end screens: `menu/`, `playnowfe/`, `careermodefe*/`, `careermodebe/`, `rivalChallenge*/`, `mycornerfe/`, `profilemanager/`.
- Shared components: `components/`, `framework/`, `icons/`, `system/`.
- Fight HUD: `hud/fnhud.hud` and `enviro/misc.viv` internal `hud.msh`/`fuihud.msh`.

The UI packages consistently contain `.apt`, `.const`, `.o`, and `.msh` members. This resembles EA's APT/Flash-style UI system. Readable strings are abundant, so label/layout changes may be possible once APT/CONST/MSH tooling is established.

### Models/animations

- Models/meshes likely use `.msh` inside `.big`, `.viv`, and decompressed `.zlb` packages.
- Venue render/order/light resources use `.orl`, `.ord`, `.lit`, and possibly `.sfx` inside decompressed `.zlb` packages.
- Animation archives include `beanim.viv`, `feanim.viv`, and `scranim.viv`, with many internal `.bin` animation banks and readable animation names.

These are high-impact but not simple text edits.

## Suspected containers/archive files

### EA BIG/VIV containers

The repo contains **163 EA-style containers**: 152 `.big` files and 11 `.viv` files. Headers observed:

- `BIGF`: most `.big` files and several `.viv` files.
- `BIG4`: some preload `.viv` files such as `preload/boxerpre.viv`, `preload/db.viv`, and `preload/tables.viv`.

The header structure was sufficiently readable to list internal filenames and offsets. Common BIG/VIV tools may support these archives, but this game may require preserving alignment, compression, checksums, or companion hash tables.

Representative examples:

| Container | Size | Header | Internal entries | Likely contents | Extraction outlook |
|---|---:|---|---:|---|---|
| `preload/tables.viv` | 44,668 | `BIG4` | 72 | Appearance/equipment/hair/morph tables | Very promising; needs table codec. |
| `preload/db.viv` | 21,854 | `BIG4` | 10 | Boxer, venue, store, training, rival databases | Very promising; ADF format research needed. |
| `contract/contracts.viv` | 1,520 | `BIGF` | 3 | Cutman/fight/trainer function resources | Promising but unknown `.fnc` binary format. |
| `scripts/scripts.viv` | 153,110 | `BIGF` | 167 | Many named `.bin` scripts | Extraction likely; editing hard. |
| `scripts/scrptpal.viv` | 539,540 | `BIGF` | 167 | Matching/related script palette binaries | Extraction likely; editing hard. |
| `beanim.viv` | 3,899,640 | `BIGF` | 15 | Boxer/face/between-round animation banks | Extraction likely; editing hard. |
| `scranim.viv` | 12,899,664 | `BIGF` | 34 | Screen/presentation animations | Extraction likely; editing hard. |
| `enviro/misc.viv` | 2,014,346 | `BIGF` | 79 | Miscellaneous `.msh` props/HUD meshes | Extraction likely; model format research needed. |
| `menu/mainmenu.big` | 271,024 | `BIGF` | 4 | `MainMenu.apt`, `.const`, `.o`, `.msh` | Extraction likely; APT UI format needed. |

### ZLB venue/environment containers

All 24 `.zlb` files appear to be zlib-wrapped `BIG4` archives:

- First 4 bytes: little-endian uncompressed size.
- Byte 4 onward: zlib stream beginning `78 da`.
- Decompressed payload begins `BIG4` and has a readable internal table of contents.

Representative `.zlb` findings:

| File | Packed size | Decompressed size | Entries | Internal data observed |
|---|---:|---:|---:|---|
| `enviro/atlntic.zlb` | 674,985 | 1,605,584 | 20 | particles `.big`, `.msh`, `.ord` venue resources. |
| `enviro/atlntict.zlb` | 276,558 | 983,984 | 35 | entrance particles, high-res entrance meshes, placement `.txt`, `.orl`, `.lit`, `.sfx`. |
| `enviro/cafrica.zlb` | 716,543 | 1,790,224 | 23 | particles, vertex animation meshes, skybox/spec/unlocked meshes, `.ord`. |
| `enviro/trainin.zlb` | 25,621 | 55,648 | 7 | training venue meshes and `.ord` resources. |
| `enviro/trainint.zlb` | 1,860 | 9,632 | 6 | training lighting/ORL/SFX resources. |
| `enviro/viceroyt.zlb` | 248,291 | 983,200 | 41 | entrance particles, placement text/SFX, ORL/LIT/ORD resources. |

Safe next-step extraction plan:

1. Create `_audit_extract_test/` or another separate folder.
2. Copy target archives into it; do not overwrite repo originals.
3. For `.zlb`, write a small script to decompress `data[4:]` with zlib and verify decompressed length equals the 4-byte size.
4. Run a BIG/VIV extractor against the decompressed payload.
5. Preserve original offsets/sizes/alignment in metadata for repacking experiments.

## PSP executable/code findings

No PSP executable or module files were found in this repo:

- No `PSP_GAME/PARAM.SFO`.
- No `PSP_GAME/SYSDIR/EBOOT.BIN`.
- No `PSP_GAME/SYSDIR/BOOT.BIN`.
- No `.prx` modules.
- No ELF-like loose executable files detected by filename or obvious magic.

Consequences:

- Gameplay formulas may be hardcoded in missing executable code.
- Stamina drain/recovery, punch damage formulas, AI decision logic, camera behavior, difficulty scaling, and memory layout cannot be proven editable from this repo alone.
- If the full ISO is available, upload/extract `PSP_GAME/SYSDIR/` and PRX modules for a separate executable audit.

Recommended executable reverse-engineering workflow if those files become available:

1. Confirm `EBOOT.BIN` encryption/compression state. PSP retail `EBOOT.BIN` may need decryption before disassembly.
2. Load decrypted ELF in Ghidra or IDA with MIPS/PSP settings.
3. Search executable strings for names seen in data archives: `xdbboxr`, `xdbtrain`, `GetTrainingResultsInfo`, `GetEarningsDetailsInfo`, `selectBoxer`, `punch`, `stamina`, etc.
4. Use PPSSPP debugger to set memory watches on visible stats and stamina values.
5. Compare changes to extracted database/table entries to determine whether values are data-driven or hardcoded.

## Strings/keyword scan findings

Keyword scan terms included: `boxer`, `fighter`, `stamina`, `damage`, `speed`, `strength`, `chin`, `cut`, `swelling`, `career`, `purse`, `money`, `training`, `difficulty`, `round`, `weight`, `venue`, `unlock`, `AI`, `CPU`, `punch`, `jab`, `hook`, `uppercut`, `block`, `dodge`, `camera`.

The scan found many hits, especially in UI packages and animation archives. Offsets below are byte offsets in the containing file; when an internal member is known, both container-relative and member-relative offsets are shown.

### High-signal gameplay/UI hits

| File/member | Offset evidence | Interpretation |
|---|---|---|
| `careermodebe/earningdetails.big!EarningDetails.apt` | file `@6136`: `txtBoxer2Amount`; `@6152`: `txtBoxer1Amount`; `@6340`: `txtTotalPurse` | Career earnings/purse display UI; likely not source values. |
| `careermodebe/earningdetails.big!EarningDetails.const` | file `@7696`: `GetEarningsDetailsInfo`; `@7848`: `strBoxerPurseRate1`; `@7884`: `strBoxerPurseRate2`; `@7904`: `txtBoxer1Amount` | Strong evidence of purse/earnings UI bindings. Underlying values probably elsewhere. |
| `careermodebe/paycheck.big!Paycheck.const` | file `@3760`: `strBoxerName`; `@3796`: `escapeMoneyString`; `@3952`: `EARNINGSDETAILS` | Paycheck display logic. |
| `playnowfe/selectboxer.big` | strings include `bIsRandomBoxer` and weight-class fields in related select UI packages | Roster/select UI logic, not proof of editable stats. |
| `careermodefe2/createchampratings.big` | filename and package members `createChampRatings.apt/.const/.o/.msh` | Create-a-champ ratings UI. Good place to inspect for displayed stat names/ranges. |
| `careermodefe2/training.big` and `trainingresults.big` | screen/package names and strings such as training results functions in UI | Training UI flow; actual training calculations likely in `preload/db.viv`, contract data, or executable. |
| `preload/db.viv!xdbboxr.adf` | internal filename at archive TOC plus readable fragments in ADF | Best current candidate for boxer roster/stat database, but format unknown. |
| `preload/db.viv!xdbtrain.adf` | internal filename plus readable fragments | Best current candidate for training data/results, but format unknown. |
| `preload/db.viv!xdbvenue.adf` | internal filename plus venue names/fragments such as `sparrin`/`venimg0` | Candidate venue database. |
| `beanim.viv!anim\anibic.bin` | file `@1572`: `ILLEGAL_PUNCH_LOW_BLOW_3_FAR_r`; `@5174`: `boxer_moveback_hook_l_body_4_far_power_r` | Animation/event names for punches and boxer movement. Does not prove damage values are editable here. |
| `beanim.viv!anim\anific.bin` | file `@1840958`: `Block_High_Center_Leftsquint_t`; `@1841331`: `Exert_Punch_Hook_t`; `@1841350`: `Exert_Punch_Jab_t`; `@1841368`: `Exert_Punch_Uppercut_t` | Face/exertion/block/punch animation names. |
| `beanim.viv!anim\anibitra.bin` | file `@3477318`: `FIGHT_INTRODUCTION_TRAINER_02_3_TRAIN_r`; `@3477574`: `chinup_full_2_cycle_A_r` | Trainer/training animation banks. |
| `hud/fnhud.hud` | readable `POLY` and `fill` markers in binary layout | In-fight HUD geometry/resources may be encoded here. |

### Lower-signal or misleading hits

- Many `AI` hits are false positives from random binary byte sequences such as `Ai5UUU%@`.
- Many `speed` hits in animation archives refer to an animation style/name such as `SPEED_STAND_*`, not player speed stats.
- UI files contain display strings and binding names, but UI evidence alone does not prove gameplay values are stored there.

## Practical modding opportunities, ranked

### Easy edits

1. **Documentation-only / extraction tooling setup**
   - Files involved: new scripts outside game files, `_audit_extract_test/` only.
   - Why it matters: creates a safe workflow without touching originals.
   - Could enable: repeatable archive inventory, table extraction, diffing.
   - Risk: Low if output is isolated.
   - Required tools: Python `struct`, `zlib`; optional EA BIG/VIV extractor.
   - Recommended next step: write a read-only extractor that emits files to `_audit_extract_test/` and a JSON manifest of offsets/sizes.

2. **UI text/layout research**
   - Files involved: `careermodebe/*.big`, `careermodefe*.big`, `playnowfe/*.big`, `menu/*.big`, `components/*.big`.
   - Why it matters: UI packages expose many readable names and screen-specific resources.
   - Could enable: visible menu text/layout changes, screen labels, button prompts, possibly stat display names.
   - Risk: Medium when repacking; low for extraction-only.
   - Required tools: BIG extractor, APT/CONST research, hex/string diff tools.
   - Recommended next step: extract one small UI package such as `components/footer.big` or `careermodebe/paycheck.big` into a test folder and inspect member formats.

### Medium edits

3. **Appearance/equipment tables**
   - Files involved: `preload/tables.viv`.
   - Why it matters: internal names directly reference actors, face morphs, hair, shoes, shorts, and morph slots.
   - Could enable: boxer appearance, equipment availability, create-a-boxer visual options.
   - Risk: Medium; table encoding is not plain CSV.
   - Required tools: BIG/VIV extractor, custom decoder for `10 fb` table resources, repacker.
   - Recommended next step: decode one small table (`haircolor.csv` or `facialhair.csv`) and verify row/field structure without modifying originals.

4. **Venue visual edits**
   - Files involved: `enviro/*.zlb`.
   - Why it matters: venues decompress cleanly to `BIG4` and contain meshes, lighting, placements, particles, and unlocked resources.
   - Could enable: venue lighting, crowd placement, ring/environment visuals, possibly unlock-state visuals.
   - Risk: Medium to high; repacking zlib/BIG and model formats must be exact.
   - Required tools: zlib script, BIG extractor/repacker, model/texture tools, PPSSPP test ISO workflow.
   - Recommended next step: decompress `enviro/trainint.zlb` in `_audit_extract_test/`, inspect the small training venue lighting files, and document format signatures.

5. **HUD/UI geometry**
   - Files involved: `hud/fnhud.hud`, `enviro/misc.viv` internal `hud.msh`/`fuihud.msh`, UI component packages.
   - Why it matters: can produce visible in-fight improvements.
   - Could enable: HUD placement, gauge visuals, overlays.
   - Risk: Medium/high until format is decoded.
   - Required tools: binary structure analysis, mesh/texture viewer, emulator screenshot testing.
   - Recommended next step: parse `hud/fnhud.hud` table offsets and identify named blocks; do not patch yet.

### Hard edits

6. **Roster/fighter stats/venue/training databases**
   - Files involved: `preload/db.viv` internal `.adf` files.
   - Why it matters: names strongly indicate boxer, venue, store, training, rival, hometown, and cut-person databases.
   - Could enable: roster names, stats, store items, training tuning, rival challenge data, venue unlock/progression if decoded.
   - Risk: High; ADF binary format unknown.
   - Required tools: ADF decoder/repacker, known-good save/game tests, PPSSPP memory verification.
   - Recommended next step: compare `xdbboxr.adf` strings/fields to visible roster list in-game; build a schema hypothesis before editing.

7. **Contract/career economy logic**
   - Files involved: `contract/contracts.viv`, career UI packages, `preload/db.viv`.
   - Why it matters: could affect purses, cutman/trainer costs, fight setup, career rewards.
   - Could enable: money/purse/reward balancing.
   - Risk: High; `.fnc` is binary and may be bytecode or data tables.
   - Required tools: `.fnc` format research, executable references, emulator testing.
   - Recommended next step: correlate `cutman.fnc`, `trainer.fnc`, and `fights.fnc` values against career UI strings and in-game paycheck screens.

### Experimental / reverse-engineering edits

8. **Core stamina, punch damage, AI, difficulty, and camera behavior**
   - Files involved: missing executable, `scripts/*.viv`, possible database tables.
   - Why it matters: this is the core gameplay improvement goal.
   - Could enable: better stamina pacing, punch damage, smarter AI, camera tweaks, difficulty rebalance.
   - Risk: Very high.
   - Required tools: full ISO executable, decrypted PSP ELF, Ghidra/IDA, PPSSPP debugger, memory watchpoints, MIPS patching.
   - Recommended next step: upload full `PSP_GAME/SYSDIR` and run a separate executable/string/disassembly audit.

9. **Animation behavior/timing edits**
   - Files involved: `beanim.viv`, `scranim.viv`, `feanim.viv`.
   - Why it matters: punch/block/dodge animations and presentation could influence game feel.
   - Could enable: animation swaps, timing research, presentation changes.
   - Risk: Very high without animation format knowledge.
   - Required tools: animation bank parser, model skeleton knowledge, emulator test harness.
   - Recommended next step: extract animation banks and map animation names to in-game events; do not edit until loaded format is understood.

## Gameplay improvement focus

### Fighter stats

- Editable now: **No.** No plain fighter stat table was found.
- Possibly editable: `preload/db.viv!xdbboxr.adf` is the strongest candidate because the name suggests a boxer database.
- Not found yet: decoded field names for power, speed, stamina, chin, heart, cuts, swelling, or ratings.
- Likely hardcoded: stat formulas and in-fight application may be in missing executable code; current repo cannot prove otherwise.

### Fighter names/rosters

- Editable now: **No direct plain roster file.**
- Possibly editable: `preload/db.viv!xdbboxr.adf`, `preload/db.viv!xdbalias.adf`, `playnowfe/selectboxer.big`, `careermodefe1/boxerbiooverlay.big`.
- Not found yet: a decoded roster name list in plain text.
- Likely hardcoded: not enough evidence; roster may be data-driven but encoded.

### Weight classes

- Editable now: **No.**
- Possibly editable: UI strings/fields in boxer selection packages include weight-class labels such as `FEATHERWEIGHT`, `LIGHTWEIGHT`, `WELTHERWEIGHT`, `MIDDLEWEIGHT`, `HEAVYWEIGHT` and variables like `iWeightClass`/`m_iWeightClass`.
- Not found yet: actual boxer-to-weight-class table.
- Likely hardcoded: number/order of classes may be in executable or APT UI logic.

### Career progression

- Editable now: **No.**
- Possibly editable: `careermodefe*/`, `careermodebe/`, `preload/db.viv!xdbrivl.adf`, `preload/db.viv!xdbevent.adf`, `contract/contracts.viv!fights.fnc`.
- Not found yet: decoded progression rules, rank thresholds, opponent scheduling.
- Likely hardcoded: progression algorithms may be executable-side.

### Money/purse/rewards

- Editable now: **No safe value edit.**
- Possibly editable: `careermodebe/earningdetails.big` and `paycheck.big` expose purse/money display bindings; `contract/contracts.viv` may hold contract/fight/trainer/cutman data.
- Not found yet: actual numeric purse/reward tables.
- Likely hardcoded: money formatting and calculation may be code; values may be in `.fnc`/`.adf` if decoded.

### Training results

- Editable now: **No.**
- Possibly editable: `preload/db.viv!xdbtrain.adf`, `careermodefe2/training.big`, `careermodefe2/trainingresults.big`, `beanim.viv` trainer/training animation names.
- Not found yet: decoded minigame score-to-stat conversion values.
- Likely hardcoded: training result formulas may be executable-side.

### Stamina drain/recovery

- Editable now: **No evidence of editable data.**
- Possibly editable: not identified; may appear in `xdbboxr.adf`, scripts, or executable.
- Not found yet: `stamina` readable strings in data files were not high-signal enough to identify a table.
- Likely hardcoded: likely in executable or animation/combat engine code unless a decoded table is found.

### Punch damage

- Editable now: **No.**
- Possibly editable: animation archives contain many punch names, but these are likely animation identifiers, not damage values. Damage could also be in `scripts` or executable.
- Not found yet: damage numeric table or punch property table.
- Likely hardcoded: combat damage formulas likely require executable reverse engineering.

### AI behavior

- Editable now: **No.**
- Possibly editable: `scripts/scripts.viv`, `scripts/scrptpal.viv`, `preload/db.viv`, or missing executable.
- Not found yet: obvious AI behavior table.
- Likely hardcoded: many `AI` string hits were binary false positives; behavior likely lives in code/scripts not yet decoded.

### Difficulty scaling

- Editable now: **No.**
- Possibly editable: `playnowfe/optionsettings.big`, `playNowBE/pauseoptionsettings.big`, `gamemodesFE/hardhitssettings.big`, `preload/db.viv`, executable.
- Not found yet: difficulty numeric scaling table.
- Likely hardcoded: probable executable-side unless decoded settings tables show values.

### Camera

- Editable now: **No.**
- Possibly editable: UI/options packages or executable; no clear camera config found.
- Not found yet: camera parameter table.
- Likely hardcoded: camera behavior likely engine/executable-side.

### HUD/UI

- Editable now: **Not directly, but strongly represented.**
- Possibly editable: `hud/fnhud.hud`, `enviro/misc.viv` internal HUD meshes, `components/`, `framework/`, screen `.big` packages.
- Not found yet: decoded HUD format/repacker.
- Likely hardcoded: some HUD logic may be executable-side, but visual/layout assets are probably data-driven.

### Venues/rings

- Editable now: **No direct raw asset edit, but extraction is straightforward.**
- Possibly editable: `enviro/*.zlb`, `preload/db.viv!xdbvenue.adf`, `playnowfe/selectvenue.big`.
- Not found yet: decoded mesh/texture/light formats and venue selection table.
- Likely hardcoded: venue loading code is executable-side, but venue assets are data-driven.

### Textures

- Editable now: **No loose standard textures.**
- Possibly editable: embedded in `.msh`, `.orl`, `.ord`, or UI `.msh` resources.
- Not found yet: texture format signature or extraction mapping.
- Likely hardcoded: no; textures are probably asset data, just packed/encoded.

### Audio/music

- Editable now: **No.**
- Possibly editable: no obvious audio banks in this repo; `.sfx` inside venues needs identification.
- Not found yet: AT3/VAG/ADX/PMF/audio archives from full ISO.
- Likely hardcoded: no; assets likely missing from this repo rather than hardcoded.

### Cutscenes/videos

- Editable now: **No.**
- Possibly editable: not from this repo.
- Not found yet: `.pmf` files or video containers from full ISO.
- Likely hardcoded: no; videos likely absent.

## What is safe to edit first

Do not edit game files in-place yet. Safe first actions are extraction/research only:

1. Create `_audit_extract_test/` and extract copies of small files there.
2. Start with `preload/tables.viv` and `preload/db.viv` because they are small and high-value.
3. Start with the smallest UI packages for APT research, e.g. `components/footer.big`, `components/bgGradient.big`, or `careermodebe/paycheck.big`.
4. Decompress only the smallest `.zlb` first, e.g. `enviro/trainint.zlb`, because it is tiny and has only 6 internal entries.
5. Keep manifests of original archive offsets, sizes, headers, and alignment before attempting any repack.

## What should not be touched yet

- Do not edit `pad1.pad`; it appears to be zero padding/filler.
- Do not edit `enviro/misc.bh` until the relationship with `enviro/misc.viv` is understood.
- Do not repack `.zlb` venue archives until the decompressed `BIG4` payload and compression wrapper are both reproduced byte-for-byte in a test copy.
- Do not patch `.adf`, `.fnc`, `.bin`, `.hud`, `.msh`, `.orl`, `.ord`, or `.lit` files until the format is decoded and an emulator test plan exists.
- Do not claim stamina, damage, AI, difficulty, or camera are data-editable until either a decoded table or executable reference proves it.
- Do not rebuild the ISO until extracted/repacked assets are verified in isolation.

## Recommended next Codex task prompt

```text
Create a safe read-only extraction toolkit for this repo. Do not modify game files. Add scripts under tools/audit/ that:
1. Parse BIGF/BIG4 archives and write a JSON manifest with container path, header, file count, member names, offsets, sizes, and SHA-1 hashes.
2. Optionally extract selected containers into _audit_extract_test/<container-name>/ only.
3. Parse .zlb files by reading the first 4-byte little-endian uncompressed size, zlib-decompressing data[4:], verifying the size, and then parsing the inner BIG4 manifest.
4. Produce a report listing all internal file extensions and high-value members containing names like xdbboxr, xdbtrain, xdbvenue, xdbstore, cutman, trainer, fights, actors, shorts, hair, ratings, purse, training, and HUD.
Do not patch or repack anything.
```

## Recommended manual emulator/debugger testing plan

1. **Baseline setup**
   - Run the unmodified game in PPSSPP.
   - Create save states for Play Now boxer select, career paycheck, training results, venue select, and in-fight HUD.
   - Capture screenshots and note exact visible roster names, weight classes, ratings, purse values, training rewards, venue names, and HUD positions.

2. **Data correlation without edits**
   - Extract `preload/db.viv` and `preload/tables.viv` into `_audit_extract_test/`.
   - Search extracted byte strings for visible in-game roster/venue/equipment names.
   - If a visible value appears, record container, member, offset, and surrounding bytes.

3. **Memory watch testing**
   - In PPSSPP debugger, locate current stamina/health/HUD gauge values during a round.
   - Freeze or change the memory value to confirm the address affects gameplay.
   - Backtrace reads/writes if possible to identify executable functions.

4. **Executable-required testing**
   - Add decrypted `EBOOT.BIN`/`BOOT.BIN` to a separate audit.
   - Search disassembly for strings/resource names such as `xdbboxr`, `xdbtrain`, `xdbvenue`, `GetEarningsDetailsInfo`, and `GetTrainingResultsInfo`.
   - Identify loader/parser functions for `.adf`, `.fnc`, `.apt`, `.msh`, and `.zlb` resources.

5. **First controlled edit after format research**
   - Choose a low-risk visible-only target, such as one UI string or a small table entry in a test copy.
   - Repack into a duplicate ISO only.
   - Test boot, target screen load, and several transitions before attempting gameplay-affecting edits.

## Final practical conclusion

This repo is rich in packed data but poor in directly editable plain files. The best realistic targets are:

1. `preload/db.viv` for boxer/venue/store/training/rival database research.
2. `preload/tables.viv` for appearance/equipment/create-a-boxer tables.
3. `contract/contracts.viv` for career economy/fight/trainer/cutman research.
4. UI `.big` packages for visible menu/career/HUD display changes.
5. `enviro/*.zlb` for venue/ring/lighting/model changes.
6. Missing PSP executables for hardcoded gameplay systems.

Until the encoded table/database formats are decoded or the executable is audited, the honest status is: **visible asset/UI/venue edits are plausible; roster/stat/career data edits are promising but unproven; core gameplay feel edits need deeper reverse engineering.**
