# PSP executable reverse-engineering audit

Scope: focused read-only audit of PSP executable/code-loading files, with detailed string analysis limited to root `BOOT.BIN` and root `EBOOT.BIN`. Existing broad `.bin` inventory was used only as context. No executable, archive, ISO, or original game file was modified.

## Executive answer

- `BOOT.BIN` is useful: it is a plain ELF32 MIPS executable with many readable gameplay/resource strings and should be the first Ghidra target.

- `EBOOT.BIN` is less useful for static RE in its current form: it has a `~PSP` header, very high entropy, many noise strings, and lacks the high-value database/gameplay strings visible in `BOOT.BIN`; hypothesis: it is encrypted/packed and corresponds to the shipped PSP executable container.

- `BOOT.BIN` directly references `preload/db.viv`, `preload/tables.viv`, `contract/contracts.viv`, `xdbboxr.adf`, `xdbtrain.adf`, `xdbvenue.adf`, `xdbstore.adf`, `cutman.fnc`, `trainer.fnc`, and `fights.fnc`.

- Direct executable-string evidence exists for stamina/damage/AI/training/career economy/contracts/venues/HUD, but string evidence alone does not prove storage formats or formulas; PPSSPP/Ghidra xrefs are still required.


## Executable-related files located

| Path | Size | SHA-1 | First 64 bytes | Detected type | State | Readable strings | RE usefulness |
|---|---:|---|---|---|---|---:|---|
| `BOOT.BIN` | 7270664 | `499a53337ff57e1cd21959d1f57fe5f0cf4013c6` | `7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00 a0 ff 08 00 01 00 00 00 cc de 34 00 34 00 00 00 40 29 59 00 01 30 a2 10 34 00 20 00 02 00 28 00 3e 00 3d 00 01 00 00 00 00 01 00 00 00 00 00 00` | ELF32 MIPS executable (plain ELF) | plain ELF / not encrypted at file level | 20702 | High: primary plain executable for Ghidra/code xrefs. |
| `EBOOT.BIN` | 7271008 | `5faef8248b376f16ac1fbf3183cb76d5418783bd` | `7e 50 53 50 00 00 00 00 01 01 46 69 67 68 74 4e 69 67 68 74 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 02 08 f1 6e 00 60 f2 6e 00 cc de 34 00 74 6f 4f 00 c8 55 03 00 00 01 40 00` | PSP ~PSP executable container/PRX-style header (title/module: FightNight) | appears encrypted/packed PSP executable container; payload has high-entropy bytes | 86782 | Low-to-medium: confirms shipped PSP container; less useful until decrypted/unpacked. |
| `UPDATE/DATA.BIN` | 14809632 | `70fef68d7e4267d9a4e92a46e17ef828ddc9e0b2` | `50 53 41 52 03 00 00 00 10 fa e1 00 01 00 00 00 6b ff d8 88 3d 76 8b 8f 4b b2 26 e5 03 f6 fa 68 8e bb 4d c7 2f 83 b2 5f 8c 7c 16 67 19 5b f0 17 e0 65 2b 1d d7 52 1b 47 3a 90 aa 39 91 d3 23 66` | PSP update PSAR payload | appears encrypted/compressed PSP update payload | 176018 | Low for gameplay: PSP updater/update payload, not Fight Night gameplay code. |
| `UPDATE/EBOOT.BIN` | 3951712 | `4bf047a3564edd4d9116ce8d3a512043bdf68616` | `7e 50 53 50 00 08 00 00 01 01 75 70 64 61 74 65 72 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 02 08 4b 3c 00 60 4c 3c 00 68 07 00 00 cc 76 0f 00 b4 5f 03 00 40 00 40 00` | PSP ~PSP executable container/PRX-style header (title/module: updater) | appears encrypted/packed PSP executable container; payload has high-entropy bytes | 47016 | Low for gameplay: PSP updater/update payload, not Fight Night gameplay code. |
| `UPDATE/PARAM.SFO` | 1772 | `963f0924a4a061d660868397054a8fecf8b18e8b` | `00 50 53 46 01 01 00 00 24 01 00 00 bc 01 00 00 11 00 00 00 00 00 04 04 04 00 00 00 04 00 00 00 00 00 00 00 09 00 04 02 03 00 00 00 04 00 00 00 04 00 00 00 12 00 04 02 0b 00 00 00 10 00 00 00` | PSP PARAM.SFO metadata (PSF) | plain metadata, not executable code | 38 | Low for gameplay: PSP updater/update payload, not Fight Night gameplay code. |

Notes: no `.prx` or `.elf` extension files were found. Magic scan found `BOOT.BIN` ELF magic, root/update `EBOOT.BIN` `~PSP` signatures, `UPDATE/PARAM.SFO` PSF metadata, and `UPDATE/DATA.BIN` PSAR update payload.

## BOOT.BIN vs EBOOT.BIN comparison

- Size: `BOOT.BIN` 7270664 bytes; `EBOOT.BIN` 7271008 bytes; EBOOT is 344 bytes larger.

- SHA-1: `BOOT.BIN` `499a53337ff57e1cd21959d1f57fe5f0cf4013c6`; `EBOOT.BIN` `5faef8248b376f16ac1fbf3183cb76d5418783bd`; hashes differ.

- Header: `BOOT.BIN` begins `7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00 a0 ff 08 00 01 00 00 00 cc de 34 00 34 00 00 00 40 29 59 00 01 30 a2 10 34 00 20 00 02 00 28 00 3e 00 3d 00 01 00 00 00 00 01 00 00 00 00 00 00` (ELF magic); `EBOOT.BIN` begins `7e 50 53 50 00 00 00 00 01 01 46 69 67 68 74 4e 69 67 68 74 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 02 08 f1 6e 00 60 f2 6e 00 cc de 34 00 74 6f 4f 00 c8 55 03 00 00 01 40 00` (`~PSP` PSP executable container).

- Readable string counts (`[ -~]{4,}`): `BOOT.BIN` 20702; `EBOOT.BIN` 86782. EBOOT's higher count is not more useful because high entropy produces many random printable runs.

- Entropy estimate, first MiB: `BOOT.BIN` 5.7567 bits/byte; `EBOOT.BIN` 7.9998 bits/byte.

- High-value string hit counts:

| String | BOOT.BIN hits | EBOOT.BIN hits |
|---|---:|---:|
| `db.viv` | 1 | 0 |
| `tables.viv` | 1 | 0 |
| `contracts.viv` | 1 | 0 |
| `xdbboxr` | 1 | 0 |
| `xdbtrain` | 1 | 0 |
| `xdbvenue` | 1 | 0 |
| `xdbstore` | 1 | 0 |
| `cutman.fnc` | 1 | 0 |
| `trainer.fnc` | 1 | 0 |
| `fights.fnc` | 1 | 0 |
| `stamina` | 2 | 0 |
| `damage` | 20 | 0 |
| `ai/mods` | 6 | 0 |
| `purse` | 7 | 0 |
| `money` | 5 | 0 |
| `training` | 18 | 0 |
| `fnhud` | 1 | 0 |

Conclusion: load `BOOT.BIN` into Ghidra first. `BOOT.BIN` appears decrypted/plain ELF; `EBOOT.BIN` appears packed/encrypted. This is strongly supported by magic bytes, entropy, and domain-string distribution, but exact PSP encryption/compression details are not decoded here.

## Executable references to resource formats

- `.viv`: **Strong evidence**. `0x4F9D5C` `scripts.viv`, `0x505EC0` `audio/BEAudio.viv`, `0x506868` `coreaems.viv`, `0x506998` `chants.viv`, `0x5086D4` `contracts.viv`, `0x5091FC` `db.viv`, `0x50CCC0` `feCRO/vnecro.viv`, `0x50CCD4` `feCRO/fhcro.viv`
- `.big`: **Strong evidence**. `0x506C3C` `trndat.big`, `0x506C54` `trnhdr.big`, `0x506C60` `ancdat.big`, `0x506C78` `anchdr.big`, `0x506C84` `comdat.big`, `0x506C9C` `comhdr.big`, `0x509838` `%s.big`, `0x51D6BC` `%s_entrance_particles.big`
- `.zlb`: **Strong evidence**. `0x4FB330` `anibiscr.zlb`, `0x5098D4` `apt/FEload.zlb`, `0x5098E4` `apt/BEload.zlb`, `0x51D68C` `%s\%s.zlb`, `0x51D6B0` `%s\%st.zlb`
- `.adf`: **Strong evidence**. `0x509204` `xdbboxr.adf`, `0x509210` `xdbvenue.adf`, `0x509220` `xdbalias.adf`, `0x509230` `xdbevent.adf`, `0x509240` `xdbhmtwn.adf`, `0x509250` `xdbstore.adf`, `0x509260` `xdbpref.adf`, `0x50926C` `xdbrivl.adf`
- `.fnc`: **Strong evidence**. `0x5086E8` `cutman.fnc`, `0x50882C` `fights.fnc`, `0x5096F0` `trainer.fnc`
- `.apt`: **Strong evidence**. `0x5098D4` `apt/FEload.zlb`, `0x5098E4` `apt/BEload.zlb`, `0x52582C` `.apt`
- `.msh`: **Strong evidence**. `0x50A0EC` `.msh`, `0x51B080` `tpage00.msh`
- `.hud`: **Strong evidence**. `0x50FEC0` `fnhud.hud`

## Database and table investigation targets

- `preload/db.viv`: **Yes**. Evidence: `BOOT.BIN:0x5091FC` `db.viv`. Why it may matter: Database archive likely containing xdb ADF tables. Follow-up: in Ghidra, search for the leaf name and rename the xref function as an archive/database loader candidate; in PPSSPP, set file-I/O/log breakpoints if available while entering the related career/menu screen.
- `preload/tables.viv`: **Yes**. Evidence: `BOOT.BIN:0x51C388` `tables.viv`. Why it may matter: Tables archive likely containing table resources. Follow-up: in Ghidra, search for the leaf name and rename the xref function as an archive/database loader candidate; in PPSSPP, set file-I/O/log breakpoints if available while entering the related career/menu screen.
- `contract/contracts.viv`: **Yes**. Evidence: `BOOT.BIN:0x5086D4` `contracts.viv`. Why it may matter: Career/contract archive. Follow-up: in Ghidra, search for the leaf name and rename the xref function as an archive/database loader candidate; in PPSSPP, set file-I/O/log breakpoints if available while entering the related career/menu screen.
- `preload/db.viv!xdbboxr.adf`: **Yes**. Evidence: `BOOT.BIN:0x5091FC` `db.viv`, `BOOT.BIN:0x509204` `xdbboxr.adf`. Why it may matter: Boxer database; likely ratings/identity/roster target. Follow-up: in Ghidra, search for the leaf name and rename the xref function as an archive/database loader candidate; in PPSSPP, set file-I/O/log breakpoints if available while entering the related career/menu screen.
- `preload/db.viv!xdbtrain.adf`: **Yes**. Evidence: `BOOT.BIN:0x5091FC` `db.viv`, `BOOT.BIN:0x509278` `xdbtrain.adf`. Why it may matter: Training database; likely drills/results target. Follow-up: in Ghidra, search for the leaf name and rename the xref function as an archive/database loader candidate; in PPSSPP, set file-I/O/log breakpoints if available while entering the related career/menu screen.
- `preload/db.viv!xdbvenue.adf`: **Yes**. Evidence: `BOOT.BIN:0x5091FC` `db.viv`, `BOOT.BIN:0x509210` `xdbvenue.adf`. Why it may matter: Venue database; venue selection target. Follow-up: in Ghidra, search for the leaf name and rename the xref function as an archive/database loader candidate; in PPSSPP, set file-I/O/log breakpoints if available while entering the related career/menu screen.
- `preload/db.viv!xdbstore.adf`: **Yes**. Evidence: `BOOT.BIN:0x5091FC` `db.viv`, `BOOT.BIN:0x509250` `xdbstore.adf`. Why it may matter: Store/unlock/equipment economy target. Follow-up: in Ghidra, search for the leaf name and rename the xref function as an archive/database loader candidate; in PPSSPP, set file-I/O/log breakpoints if available while entering the related career/menu screen.
- `contract/contracts.viv!cutman.fnc`: **Yes**. Evidence: `BOOT.BIN:0x5086D4` `contracts.viv`, `BOOT.BIN:0x5086E8` `cutman.fnc`. Why it may matter: Cutman contract/function script. Follow-up: in Ghidra, search for the leaf name and rename the xref function as an archive/database loader candidate; in PPSSPP, set file-I/O/log breakpoints if available while entering the related career/menu screen.
- `contract/contracts.viv!trainer.fnc`: **Yes**. Evidence: `BOOT.BIN:0x5086D4` `contracts.viv`, `BOOT.BIN:0x5096F0` `trainer.fnc`. Why it may matter: Trainer contract/function script. Follow-up: in Ghidra, search for the leaf name and rename the xref function as an archive/database loader candidate; in PPSSPP, set file-I/O/log breakpoints if available while entering the related career/menu screen.
- `contract/contracts.viv!fights.fnc`: **Yes**. Evidence: `BOOT.BIN:0x5086D4` `contracts.viv`, `BOOT.BIN:0x50882C` `fights.fnc`. Why it may matter: Fight contract/function script. Follow-up: in Ghidra, search for the leaf name and rename the xref function as an archive/database loader candidate; in PPSSPP, set file-I/O/log breakpoints if available while entering the related career/menu screen.

## Gameplay systems evidence

- **fighter ratings**: **Indirect evidence found**. Evidence: `0x509204` `xdbboxr.adf`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: data-driven hypothesis via boxer database and ranking/class strings.
- **stamina**: **Direct executable evidence found**. Evidence: `0x50AFE8` `iStamina`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: unknown/data-driven-or-code-driven.
- **punch damage**: **Direct executable evidence found**. Evidence: `0x4F9F10` `dec damage taken from clean punch`, `0x4F9F34` `dec damage taken from blocked punch`, `0x4F9F58` `dec damage taken from body punch`, `0x4F9F7C` `dec damage taken from head punch`, `0x4FA084` `inc all attack damage`, `0x4FA09C` `inc uppercut damage`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: code-driven modifiers with possible data inputs.
- **health**: **Direct executable evidence found**. Evidence: `0x4FA458` `ai/mods/p%d/energy and health`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: code-driven with runtime memory state.
- **cuts/swelling**: **Direct executable evidence found**. Evidence: `0x4FA09C` `inc uppercut damage`, `0x4FA234` `dec swelling`, `0x4FA244` `inc opp swelling`, `0x4FA8E0` `cutman`, `0x5086E8` `cutman.fnc`, `0x509288` `xdbcutpn.adf`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: code-driven modifiers and fight-state data.
- **AI behavior**: **Direct executable evidence found**. Evidence: `0x4F98C0` `ai/drones/drone0`, `0x4F98D4` `ai/drones/drone1`, `0x4F9A48` `DRONE_ATTACKING`, `0x4F9A58` `DRONE_TAUNTING`, `0x4F9A68` `DRONE_ILLEGAL_PUNCH`, `0x4F9A7C` `DRONE_SIGNATURE_PUNCH`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: code-driven AI with data/script labels.
- **difficulty scaling**: **No evidence found yet**. Evidence: None in focused meaningful string set.. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: no string evidence; unknown.
- **training results**: **Indirect evidence found**. Evidence: `0x4FB658` `body_ingame_training`, `0x504F10` `fe_TrainingMeter`, `0x504F34` `fe_TrainingHeartBeat_Lp`, `0x5056D0` `EnvSfx_Training`, `0x509278` `xdbtrain.adf`, `0x5096F0` `trainer.fnc`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: data-driven hypothesis via db/script strings.
- **career purse/money**: **Indirect evidence found**. Evidence: `0x505BCC` `MenuSfx_MoneyCount_Lp`, `0x5086D4` `contracts.viv`, `0x50A9FC` `strMoney`, `0x50ACD0` `Money`, `0x50DB54` `astrContractPurse`, `0x50DD30` `$INFO_Money`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: data-driven/script-driven hypothesis.
- **contracts**: **Direct executable evidence found**. Evidence: `0x5086D4` `contracts.viv`, `0x5086E8` `cutman.fnc`, `0x50882C` `fights.fnc`, `0x5096F0` `trainer.fnc`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: script/archive-driven.
- **venue selection**: **Indirect evidence found**. Evidence: `0x4FA598` `Venue Script`, `0x509210` `xdbvenue.adf`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: data-driven/resource-driven.
- **HUD**: **Indirect evidence found**. Evidence: `0x50FEC0` `fnhud.hud`, `0x523B7D` `hud`. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: UI/resource-driven.
- **camera**: **No evidence found yet**. Evidence: None in focused meaningful string set.. Next area: search/rename xref functions for these strings in `BOOT.BIN`; connect with PPSSPP memory watchpoints where runtime values exist. Data/code classification: unknown; likely code/resource labels.

## Practical next steps

1. Import `BOOT.BIN` as MIPS little-endian ELF in Ghidra and prioritize xrefs to archive/database strings around offsets `0x5086D4`, `0x5091FC`-`0x509288`, and `0x51C388`.

2. Use PPSSPP debugger/manual memory search to confirm whether runtime stamina/health/money/training values are authoritative gameplay state or display-only UI state.

3. Do not edit executables or repack archives until xrefs and memory watchpoints prove the relevant data path.
