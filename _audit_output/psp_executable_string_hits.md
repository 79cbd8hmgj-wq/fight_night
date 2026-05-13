# PSP executable focused string hits

Deep string scan scope: root `BOOT.BIN` and root `EBOOT.BIN` only. Hits below are selected meaningful or diagnostic hits from printable strings; very short/random `EBOOT.BIN` tokens are marked as likely noise because EBOOT appears high-entropy/encrypted. Offsets are file offsets.

## `BOOT.BIN` @ `0x4F9540`: `bodypunch_modifier 0: none, use weave state`
- Matched term(s): `punch`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4F94A0`: `Module %d unloaded successfully`
  - `0x4F94C4`: `Module %d not unloaded. Sony Err: [%d]`
  - `0x4F94F0`: `weave_modifier 0: turns move into weave`
  - `0x4F9518`: `weave_modifier 1: turns weave into move`
  - `0x4F9540`: `bodypunch_modifier 0: none, use weave state`
  - `0x4F956C`: `bodypunch_modifier 1: none, use combo of weave state + weave modifier`
  - `0x4F95B4`: `bodypunch_modifier 2: it's there`
  - `0x4F95D8`: `block_modifier 0: none, right analog is block, use it as feint modifier`
  - `0x4F9620`: `block_modifier 1: mod right analog, punch becomes block`
  - `0x4F9658`: `block_modifier 2: mod right analog, block becomes punch`
- Surrounding 128 bytes: `3a 20 74 75 72 6e 73 20 6d 6f 76 65 20 69 6e 74 6f 20 77 65 61 76 65 00 77 65 61 76 65 5f 6d 6f 64 69 66 69 65 72 20 31 3a 20 74 75 72 6e 73 20 77 65 61 76 65 20 69 6e 74 6f 20 6d 6f 76 65 00 62 6f 64 79 70 75 6e 63 68 5f 6d 6f 64 69 66 69 65 72 20 30 3a 20 6e 6f 6e 65 2c 20 75 73 65 20 77 65 61 76 65 20 73 74 61 74 65 00 62 6f 64 79 70 75 6e 63 68 5f 6d 6f 64 69 66 69 65 72 20 31`

## `BOOT.BIN` @ `0x4F956C`: `bodypunch_modifier 1: none, use combo of weave state + weave modifier`
- Matched term(s): `punch`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4F94C4`: `Module %d not unloaded. Sony Err: [%d]`
  - `0x4F94F0`: `weave_modifier 0: turns move into weave`
  - `0x4F9518`: `weave_modifier 1: turns weave into move`
  - `0x4F9540`: `bodypunch_modifier 0: none, use weave state`
  - `0x4F956C`: `bodypunch_modifier 1: none, use combo of weave state + weave modifier`
  - `0x4F95B4`: `bodypunch_modifier 2: it's there`
  - `0x4F95D8`: `block_modifier 0: none, right analog is block, use it as feint modifier`
  - `0x4F9620`: `block_modifier 1: mod right analog, punch becomes block`
  - `0x4F9658`: `block_modifier 2: mod right analog, block becomes punch`
  - `0x4F9690`: `block_modifier 3: mod left analog to block, right analog always punches`
- Surrounding 128 bytes: `72 6e 73 20 77 65 61 76 65 20 69 6e 74 6f 20 6d 6f 76 65 00 62 6f 64 79 70 75 6e 63 68 5f 6d 6f 64 69 66 69 65 72 20 30 3a 20 6e 6f 6e 65 2c 20 75 73 65 20 77 65 61 76 65 20 73 74 61 74 65 00 62 6f 64 79 70 75 6e 63 68 5f 6d 6f 64 69 66 69 65 72 20 31 3a 20 6e 6f 6e 65 2c 20 75 73 65 20 63 6f 6d 62 6f 20 6f 66 20 77 65 61 76 65 20 73 74 61 74 65 20 2b 20 77 65 61 76 65 20 6d 6f 64`

## `BOOT.BIN` @ `0x4F95B4`: `bodypunch_modifier 2: it's there`
- Matched term(s): `punch`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4F94F0`: `weave_modifier 0: turns move into weave`
  - `0x4F9518`: `weave_modifier 1: turns weave into move`
  - `0x4F9540`: `bodypunch_modifier 0: none, use weave state`
  - `0x4F956C`: `bodypunch_modifier 1: none, use combo of weave state + weave modifier`
  - `0x4F95B4`: `bodypunch_modifier 2: it's there`
  - `0x4F95D8`: `block_modifier 0: none, right analog is block, use it as feint modifier`
  - `0x4F9620`: `block_modifier 1: mod right analog, punch becomes block`
  - `0x4F9658`: `block_modifier 2: mod right analog, block becomes punch`
  - `0x4F9690`: `block_modifier 3: mod left analog to block, right analog always punches`
  - `0x4F96D8`: `modifier_layout 0: Ll:weavem   R1:bpm   L2:   R2:blockm`
- Surrounding 128 bytes: `68 5f 6d 6f 64 69 66 69 65 72 20 31 3a 20 6e 6f 6e 65 2c 20 75 73 65 20 63 6f 6d 62 6f 20 6f 66 20 77 65 61 76 65 20 73 74 61 74 65 20 2b 20 77 65 61 76 65 20 6d 6f 64 69 66 69 65 72 00 00 00 62 6f 64 79 70 75 6e 63 68 5f 6d 6f 64 69 66 69 65 72 20 32 3a 20 69 74 27 73 20 74 68 65 72 65 00 00 00 00 62 6c 6f 63 6b 5f 6d 6f 64 69 66 69 65 72 20 30 3a 20 6e 6f 6e 65 2c 20 72 69 67 68`

## `BOOT.BIN` @ `0x4F95D8`: `block_modifier 0: none, right analog is block, use it as feint modifier`
- Matched term(s): `block`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4F9518`: `weave_modifier 1: turns weave into move`
  - `0x4F9540`: `bodypunch_modifier 0: none, use weave state`
  - `0x4F956C`: `bodypunch_modifier 1: none, use combo of weave state + weave modifier`
  - `0x4F95B4`: `bodypunch_modifier 2: it's there`
  - `0x4F95D8`: `block_modifier 0: none, right analog is block, use it as feint modifier`
  - `0x4F9620`: `block_modifier 1: mod right analog, punch becomes block`
  - `0x4F9658`: `block_modifier 2: mod right analog, block becomes punch`
  - `0x4F9690`: `block_modifier 3: mod left analog to block, right analog always punches`
  - `0x4F96D8`: `modifier_layout 0: Ll:weavem   R1:bpm   L2:   R2:blockm`
  - `0x4F9710`: `modifier_layout 1: Ll:weavem   R1:bpm   L2:blockm   R2:`
- Surrounding 128 bytes: `76 65 20 73 74 61 74 65 20 2b 20 77 65 61 76 65 20 6d 6f 64 69 66 69 65 72 00 00 00 62 6f 64 79 70 75 6e 63 68 5f 6d 6f 64 69 66 69 65 72 20 32 3a 20 69 74 27 73 20 74 68 65 72 65 00 00 00 00 62 6c 6f 63 6b 5f 6d 6f 64 69 66 69 65 72 20 30 3a 20 6e 6f 6e 65 2c 20 72 69 67 68 74 20 61 6e 61 6c 6f 67 20 69 73 20 62 6c 6f 63 6b 2c 20 75 73 65 20 69 74 20 61 73 20 66 65 69 6e 74 20 6d`

## `BOOT.BIN` @ `0x4F9620`: `block_modifier 1: mod right analog, punch becomes block`
- Matched term(s): `punch`, `block`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4F9540`: `bodypunch_modifier 0: none, use weave state`
  - `0x4F956C`: `bodypunch_modifier 1: none, use combo of weave state + weave modifier`
  - `0x4F95B4`: `bodypunch_modifier 2: it's there`
  - `0x4F95D8`: `block_modifier 0: none, right analog is block, use it as feint modifier`
  - `0x4F9620`: `block_modifier 1: mod right analog, punch becomes block`
  - `0x4F9658`: `block_modifier 2: mod right analog, block becomes punch`
  - `0x4F9690`: `block_modifier 3: mod left analog to block, right analog always punches`
  - `0x4F96D8`: `modifier_layout 0: Ll:weavem   R1:bpm   L2:   R2:blockm`
  - `0x4F9710`: `modifier_layout 1: Ll:weavem   R1:bpm   L2:blockm   R2:`
  - `0x4F9748`: `modifier_layout 2: Ll:weavem   R1:blockm   L2:   R2:bpm`
- Surrounding 128 bytes: `64 69 66 69 65 72 20 30 3a 20 6e 6f 6e 65 2c 20 72 69 67 68 74 20 61 6e 61 6c 6f 67 20 69 73 20 62 6c 6f 63 6b 2c 20 75 73 65 20 69 74 20 61 73 20 66 65 69 6e 74 20 6d 6f 64 69 66 69 65 72 00 62 6c 6f 63 6b 5f 6d 6f 64 69 66 69 65 72 20 31 3a 20 6d 6f 64 20 72 69 67 68 74 20 61 6e 61 6c 6f 67 2c 20 70 75 6e 63 68 20 62 65 63 6f 6d 65 73 20 62 6c 6f 63 6b 00 62 6c 6f 63 6b 5f 6d 6f`

## `BOOT.BIN` @ `0x4F9658`: `block_modifier 2: mod right analog, block becomes punch`
- Matched term(s): `punch`, `block`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4F956C`: `bodypunch_modifier 1: none, use combo of weave state + weave modifier`
  - `0x4F95B4`: `bodypunch_modifier 2: it's there`
  - `0x4F95D8`: `block_modifier 0: none, right analog is block, use it as feint modifier`
  - `0x4F9620`: `block_modifier 1: mod right analog, punch becomes block`
  - `0x4F9658`: `block_modifier 2: mod right analog, block becomes punch`
  - `0x4F9690`: `block_modifier 3: mod left analog to block, right analog always punches`
  - `0x4F96D8`: `modifier_layout 0: Ll:weavem   R1:bpm   L2:   R2:blockm`
  - `0x4F9710`: `modifier_layout 1: Ll:weavem   R1:bpm   L2:blockm   R2:`
  - `0x4F9748`: `modifier_layout 2: Ll:weavem   R1:blockm   L2:   R2:bpm`
  - `0x4F9780`: `modifier_layout 3: Ll:weavem   R1:blockm   L2:bpm   R2:`
- Surrounding 128 bytes: `6f 64 69 66 69 65 72 00 62 6c 6f 63 6b 5f 6d 6f 64 69 66 69 65 72 20 31 3a 20 6d 6f 64 20 72 69 67 68 74 20 61 6e 61 6c 6f 67 2c 20 70 75 6e 63 68 20 62 65 63 6f 6d 65 73 20 62 6c 6f 63 6b 00 62 6c 6f 63 6b 5f 6d 6f 64 69 66 69 65 72 20 32 3a 20 6d 6f 64 20 72 69 67 68 74 20 61 6e 61 6c 6f 67 2c 20 62 6c 6f 63 6b 20 62 65 63 6f 6d 65 73 20 70 75 6e 63 68 00 62 6c 6f 63 6b 5f 6d 6f`

## `BOOT.BIN` @ `0x4F9690`: `block_modifier 3: mod left analog to block, right analog always punches`
- Matched term(s): `punch`, `block`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4F95B4`: `bodypunch_modifier 2: it's there`
  - `0x4F95D8`: `block_modifier 0: none, right analog is block, use it as feint modifier`
  - `0x4F9620`: `block_modifier 1: mod right analog, punch becomes block`
  - `0x4F9658`: `block_modifier 2: mod right analog, block becomes punch`
  - `0x4F9690`: `block_modifier 3: mod left analog to block, right analog always punches`
  - `0x4F96D8`: `modifier_layout 0: Ll:weavem   R1:bpm   L2:   R2:blockm`
  - `0x4F9710`: `modifier_layout 1: Ll:weavem   R1:bpm   L2:blockm   R2:`
  - `0x4F9748`: `modifier_layout 2: Ll:weavem   R1:blockm   L2:   R2:bpm`
  - `0x4F9780`: `modifier_layout 3: Ll:weavem   R1:blockm   L2:bpm   R2:`
  - `0x4F97B8`: `out of memory`
- Surrounding 128 bytes: `73 20 62 6c 6f 63 6b 00 62 6c 6f 63 6b 5f 6d 6f 64 69 66 69 65 72 20 32 3a 20 6d 6f 64 20 72 69 67 68 74 20 61 6e 61 6c 6f 67 2c 20 62 6c 6f 63 6b 20 62 65 63 6f 6d 65 73 20 70 75 6e 63 68 00 62 6c 6f 63 6b 5f 6d 6f 64 69 66 69 65 72 20 33 3a 20 6d 6f 64 20 6c 65 66 74 20 61 6e 61 6c 6f 67 20 74 6f 20 62 6c 6f 63 6b 2c 20 72 69 67 68 74 20 61 6e 61 6c 6f 67 20 61 6c 77 61 79 73 20`

## `BOOT.BIN` @ `0x4F98C0`: `ai/drones/drone0`
- Matched term(s): `AI`
- Assessment: **meaningful**
- Why it matters: AI/drone behavior label; useful for locating AI setup or event/state code.
- Nearby printable strings:
  - `0x4F9850`: `out of memory`
  - `0x4F9860`: `out of memory`
  - `0x4F9870`: `out of memory`
  - `0x4F98B0`: `out of memory`
  - `0x4F98C0`: `ai/drones/drone0`
  - `0x4F98D4`: `ai/drones/drone1`
  - `0x4F98E8`: `out of memory`
  - `0x4F9960`: `out of memory`
  - `0x4F9970`: `out of memory`
  - `0x4F99F0`: `out of memory`
- Surrounding 128 bytes: `40 f9 02 00 98 f9 02 00 a8 f8 02 00 5c f9 02 00 5c f9 02 00 98 f9 02 00 98 f9 02 00 5c f9 02 00 7c f9 02 00 98 f9 02 00 98 f9 02 00 40 f9 02 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 61 69 2f 64 72 6f 6e 65 73 2f 64 72 6f 6e 65 30 00 00 00 00 61 69 2f 64 72 6f 6e 65 73 2f 64 72 6f 6e 65 31 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 80 51 03 00 70 51 03 00`

## `BOOT.BIN` @ `0x4F98D4`: `ai/drones/drone1`
- Matched term(s): `AI`
- Assessment: **meaningful**
- Why it matters: AI/drone behavior label; useful for locating AI setup or event/state code.
- Nearby printable strings:
  - `0x4F9860`: `out of memory`
  - `0x4F9870`: `out of memory`
  - `0x4F98B0`: `out of memory`
  - `0x4F98C0`: `ai/drones/drone0`
  - `0x4F98D4`: `ai/drones/drone1`
  - `0x4F98E8`: `out of memory`
  - `0x4F9960`: `out of memory`
  - `0x4F9970`: `out of memory`
  - `0x4F99F0`: `out of memory`
  - `0x4F9A00`: `out of memory`
- Surrounding 128 bytes: `98 f9 02 00 98 f9 02 00 5c f9 02 00 7c f9 02 00 98 f9 02 00 98 f9 02 00 40 f9 02 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 61 69 2f 64 72 6f 6e 65 73 2f 64 72 6f 6e 65 30 00 00 00 00 61 69 2f 64 72 6f 6e 65 73 2f 64 72 6f 6e 65 31 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 80 51 03 00 70 51 03 00 78 51 03 00 9c 51 03 00 88 51 03 00 90 51 03 00 98 51 03 00`

## `BOOT.BIN` @ `0x4F9A48`: `DRONE_ATTACKING`
- Matched term(s): (context match)
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4F9A00`: `out of memory`
  - `0x4F9A10`: `out of memory`
  - `0x4F9A20`: `A:%d, D:%d, M:%d`
  - `0x4F9A34`: `out of memory`
  - `0x4F9A48`: `DRONE_ATTACKING`
  - `0x4F9A58`: `DRONE_TAUNTING`
  - `0x4F9A68`: `DRONE_ILLEGAL_PUNCH`
  - `0x4F9A7C`: `DRONE_SIGNATURE_PUNCH`
  - `0x4F9A94`: `DRONE_FEINTING`
  - `0x4F9AA4`: `out of memory`
- Surrounding 128 bytes: `65 6d 6f 72 79 0a 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 41 3a 25 64 2c 20 44 3a 25 64 2c 20 4d 3a 25 64 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 41 54 54 41 43 4b 49 4e 47 00 44 52 4f 4e 45 5f 54 41 55 4e 54 49 4e 47 00 00 44 52 4f 4e 45 5f 49 4c 4c 45 47 41 4c 5f 50 55 4e 43 48 00 44 52 4f 4e 45 5f 53 49 47 4e 41 54`

## `BOOT.BIN` @ `0x4F9A58`: `DRONE_TAUNTING`
- Matched term(s): (context match)
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4F9A10`: `out of memory`
  - `0x4F9A20`: `A:%d, D:%d, M:%d`
  - `0x4F9A34`: `out of memory`
  - `0x4F9A48`: `DRONE_ATTACKING`
  - `0x4F9A58`: `DRONE_TAUNTING`
  - `0x4F9A68`: `DRONE_ILLEGAL_PUNCH`
  - `0x4F9A7C`: `DRONE_SIGNATURE_PUNCH`
  - `0x4F9A94`: `DRONE_FEINTING`
  - `0x4F9AA4`: `out of memory`
  - `0x4F9B00`: `DRONE_COUNTER_PUNCH`
- Surrounding 128 bytes: `65 6d 6f 72 79 0a 00 00 41 3a 25 64 2c 20 44 3a 25 64 2c 20 4d 3a 25 64 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 41 54 54 41 43 4b 49 4e 47 00 44 52 4f 4e 45 5f 54 41 55 4e 54 49 4e 47 00 00 44 52 4f 4e 45 5f 49 4c 4c 45 47 41 4c 5f 50 55 4e 43 48 00 44 52 4f 4e 45 5f 53 49 47 4e 41 54 55 52 45 5f 50 55 4e 43 48 00 00 00 44 52 4f 4e`

## `BOOT.BIN` @ `0x4F9A68`: `DRONE_ILLEGAL_PUNCH`
- Matched term(s): `punch`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4F9A20`: `A:%d, D:%d, M:%d`
  - `0x4F9A34`: `out of memory`
  - `0x4F9A48`: `DRONE_ATTACKING`
  - `0x4F9A58`: `DRONE_TAUNTING`
  - `0x4F9A68`: `DRONE_ILLEGAL_PUNCH`
  - `0x4F9A7C`: `DRONE_SIGNATURE_PUNCH`
  - `0x4F9A94`: `DRONE_FEINTING`
  - `0x4F9AA4`: `out of memory`
  - `0x4F9B00`: `DRONE_COUNTER_PUNCH`
  - `0x4F9B14`: `out of memory`
- Surrounding 128 bytes: `25 64 2c 20 4d 3a 25 64 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 41 54 54 41 43 4b 49 4e 47 00 44 52 4f 4e 45 5f 54 41 55 4e 54 49 4e 47 00 00 44 52 4f 4e 45 5f 49 4c 4c 45 47 41 4c 5f 50 55 4e 43 48 00 44 52 4f 4e 45 5f 53 49 47 4e 41 54 55 52 45 5f 50 55 4e 43 48 00 00 00 44 52 4f 4e 45 5f 46 45 49 4e 54 49 4e 47 00 00 6f 75 74 20`

## `BOOT.BIN` @ `0x4F9A7C`: `DRONE_SIGNATURE_PUNCH`
- Matched term(s): `punch`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4F9A34`: `out of memory`
  - `0x4F9A48`: `DRONE_ATTACKING`
  - `0x4F9A58`: `DRONE_TAUNTING`
  - `0x4F9A68`: `DRONE_ILLEGAL_PUNCH`
  - `0x4F9A7C`: `DRONE_SIGNATURE_PUNCH`
  - `0x4F9A94`: `DRONE_FEINTING`
  - `0x4F9AA4`: `out of memory`
  - `0x4F9B00`: `DRONE_COUNTER_PUNCH`
  - `0x4F9B14`: `out of memory`
  - `0x4F9B28`: `DRONE_DEFENDING`
- Surrounding 128 bytes: `65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 41 54 54 41 43 4b 49 4e 47 00 44 52 4f 4e 45 5f 54 41 55 4e 54 49 4e 47 00 00 44 52 4f 4e 45 5f 49 4c 4c 45 47 41 4c 5f 50 55 4e 43 48 00 44 52 4f 4e 45 5f 53 49 47 4e 41 54 55 52 45 5f 50 55 4e 43 48 00 00 00 44 52 4f 4e 45 5f 46 45 49 4e 54 49 4e 47 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 8c 05 00`

## `BOOT.BIN` @ `0x4F9A94`: `DRONE_FEINTING`
- Matched term(s): (context match)
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4F9A48`: `DRONE_ATTACKING`
  - `0x4F9A58`: `DRONE_TAUNTING`
  - `0x4F9A68`: `DRONE_ILLEGAL_PUNCH`
  - `0x4F9A7C`: `DRONE_SIGNATURE_PUNCH`
  - `0x4F9A94`: `DRONE_FEINTING`
  - `0x4F9AA4`: `out of memory`
  - `0x4F9B00`: `DRONE_COUNTER_PUNCH`
  - `0x4F9B14`: `out of memory`
  - `0x4F9B28`: `DRONE_DEFENDING`
  - `0x4F9B38`: `DRONE_DEFEND_PREPARE`
- Surrounding 128 bytes: `49 4e 47 00 44 52 4f 4e 45 5f 54 41 55 4e 54 49 4e 47 00 00 44 52 4f 4e 45 5f 49 4c 4c 45 47 41 4c 5f 50 55 4e 43 48 00 44 52 4f 4e 45 5f 53 49 47 4e 41 54 55 52 45 5f 50 55 4e 43 48 00 00 00 44 52 4f 4e 45 5f 46 45 49 4e 54 49 4e 47 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 8c 05 00 4c 8c 05 00 7c 8c 05 00 ac 8c 05 00 a4 8c 05 00 c4 8c 05 00 90 8c 05 00`

## `BOOT.BIN` @ `0x4F9B00`: `DRONE_COUNTER_PUNCH`
- Matched term(s): `punch`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4F9A68`: `DRONE_ILLEGAL_PUNCH`
  - `0x4F9A7C`: `DRONE_SIGNATURE_PUNCH`
  - `0x4F9A94`: `DRONE_FEINTING`
  - `0x4F9AA4`: `out of memory`
  - `0x4F9B00`: `DRONE_COUNTER_PUNCH`
  - `0x4F9B14`: `out of memory`
  - `0x4F9B28`: `DRONE_DEFENDING`
  - `0x4F9B38`: `DRONE_DEFEND_PREPARE`
  - `0x4F9B50`: `DRONE_BREAKCLINCH`
  - `0x4F9B64`: `DRONE_CLINCH`
- Surrounding 128 bytes: `7c 8c 05 00 ac 8c 05 00 a4 8c 05 00 c4 8c 05 00 90 8c 05 00 64 8c 05 00 18 c4 05 00 18 c4 05 00 18 c4 05 00 18 c4 05 00 1c c4 05 00 1c c4 05 00 1c c4 05 00 1c c4 05 00 18 c4 05 00 18 c4 05 00 44 52 4f 4e 45 5f 43 4f 55 4e 54 45 52 5f 50 55 4e 43 48 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 44 45 46 45 4e 44 49 4e 47 00 44 52 4f 4e 45 5f 44 45`

## `BOOT.BIN` @ `0x4F9B28`: `DRONE_DEFENDING`
- Matched term(s): (context match)
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4F9A94`: `DRONE_FEINTING`
  - `0x4F9AA4`: `out of memory`
  - `0x4F9B00`: `DRONE_COUNTER_PUNCH`
  - `0x4F9B14`: `out of memory`
  - `0x4F9B28`: `DRONE_DEFENDING`
  - `0x4F9B38`: `DRONE_DEFEND_PREPARE`
  - `0x4F9B50`: `DRONE_BREAKCLINCH`
  - `0x4F9B64`: `DRONE_CLINCH`
  - `0x4F9B74`: `out of memory`
  - `0x4F9B88`: `DRONE_STATE_IDLE`
- Surrounding 128 bytes: `1c c4 05 00 1c c4 05 00 1c c4 05 00 1c c4 05 00 18 c4 05 00 18 c4 05 00 44 52 4f 4e 45 5f 43 4f 55 4e 54 45 52 5f 50 55 4e 43 48 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 44 45 46 45 4e 44 49 4e 47 00 44 52 4f 4e 45 5f 44 45 46 45 4e 44 5f 50 52 45 50 41 52 45 00 00 00 00 44 52 4f 4e 45 5f 42 52 45 41 4b 43 4c 49 4e 43 48 00 00 00 44 52 4f 4e`

## `BOOT.BIN` @ `0x4F9B38`: `DRONE_DEFEND_PREPARE`
- Matched term(s): (context match)
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4F9AA4`: `out of memory`
  - `0x4F9B00`: `DRONE_COUNTER_PUNCH`
  - `0x4F9B14`: `out of memory`
  - `0x4F9B28`: `DRONE_DEFENDING`
  - `0x4F9B38`: `DRONE_DEFEND_PREPARE`
  - `0x4F9B50`: `DRONE_BREAKCLINCH`
  - `0x4F9B64`: `DRONE_CLINCH`
  - `0x4F9B74`: `out of memory`
  - `0x4F9B88`: `DRONE_STATE_IDLE`
  - `0x4F9BA0`: `DRONE_KNOCKDOWN_ATTACK`
- Surrounding 128 bytes: `18 c4 05 00 18 c4 05 00 44 52 4f 4e 45 5f 43 4f 55 4e 54 45 52 5f 50 55 4e 43 48 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 44 45 46 45 4e 44 49 4e 47 00 44 52 4f 4e 45 5f 44 45 46 45 4e 44 5f 50 52 45 50 41 52 45 00 00 00 00 44 52 4f 4e 45 5f 42 52 45 41 4b 43 4c 49 4e 43 48 00 00 00 44 52 4f 4e 45 5f 43 4c 49 4e 43 48 00 00 00 00 6f 75 74 20`

## `BOOT.BIN` @ `0x4F9B50`: `DRONE_BREAKCLINCH`
- Matched term(s): (context match)
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4F9B00`: `DRONE_COUNTER_PUNCH`
  - `0x4F9B14`: `out of memory`
  - `0x4F9B28`: `DRONE_DEFENDING`
  - `0x4F9B38`: `DRONE_DEFEND_PREPARE`
  - `0x4F9B50`: `DRONE_BREAKCLINCH`
  - `0x4F9B64`: `DRONE_CLINCH`
  - `0x4F9B74`: `out of memory`
  - `0x4F9B88`: `DRONE_STATE_IDLE`
  - `0x4F9BA0`: `DRONE_KNOCKDOWN_ATTACK`
  - `0x4F9BB8`: `out of memory`
- Surrounding 128 bytes: `4e 43 48 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 44 45 46 45 4e 44 49 4e 47 00 44 52 4f 4e 45 5f 44 45 46 45 4e 44 5f 50 52 45 50 41 52 45 00 00 00 00 44 52 4f 4e 45 5f 42 52 45 41 4b 43 4c 49 4e 43 48 00 00 00 44 52 4f 4e 45 5f 43 4c 49 4e 43 48 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 53 54`

## `BOOT.BIN` @ `0x4F9B64`: `DRONE_CLINCH`
- Matched term(s): (context match)
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4F9B14`: `out of memory`
  - `0x4F9B28`: `DRONE_DEFENDING`
  - `0x4F9B38`: `DRONE_DEFEND_PREPARE`
  - `0x4F9B50`: `DRONE_BREAKCLINCH`
  - `0x4F9B64`: `DRONE_CLINCH`
  - `0x4F9B74`: `out of memory`
  - `0x4F9B88`: `DRONE_STATE_IDLE`
  - `0x4F9BA0`: `DRONE_KNOCKDOWN_ATTACK`
  - `0x4F9BB8`: `out of memory`
  - `0x4F9BC8`: `DRONE_MOVEMENT`
- Surrounding 128 bytes: `00 00 00 00 44 52 4f 4e 45 5f 44 45 46 45 4e 44 49 4e 47 00 44 52 4f 4e 45 5f 44 45 46 45 4e 44 5f 50 52 45 50 41 52 45 00 00 00 00 44 52 4f 4e 45 5f 42 52 45 41 4b 43 4c 49 4e 43 48 00 00 00 44 52 4f 4e 45 5f 43 4c 49 4e 43 48 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 53 54 41 54 45 5f 49 44 4c 45 00 00 00 00 00 00 00 00 44 52 4f 4e`

## `BOOT.BIN` @ `0x4F9B88`: `DRONE_STATE_IDLE`
- Matched term(s): (context match)
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4F9B38`: `DRONE_DEFEND_PREPARE`
  - `0x4F9B50`: `DRONE_BREAKCLINCH`
  - `0x4F9B64`: `DRONE_CLINCH`
  - `0x4F9B74`: `out of memory`
  - `0x4F9B88`: `DRONE_STATE_IDLE`
  - `0x4F9BA0`: `DRONE_KNOCKDOWN_ATTACK`
  - `0x4F9BB8`: `out of memory`
  - `0x4F9BC8`: `DRONE_MOVEMENT`
  - `0x4F9BD8`: `out of memory`
  - `0x4F9C10`: `out of memory`
- Surrounding 128 bytes: `50 41 52 45 00 00 00 00 44 52 4f 4e 45 5f 42 52 45 41 4b 43 4c 49 4e 43 48 00 00 00 44 52 4f 4e 45 5f 43 4c 49 4e 43 48 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 53 54 41 54 45 5f 49 44 4c 45 00 00 00 00 00 00 00 00 44 52 4f 4e 45 5f 4b 4e 4f 43 4b 44 4f 57 4e 5f 41 54 54 41 43 4b 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00`

## `BOOT.BIN` @ `0x4F9BA0`: `DRONE_KNOCKDOWN_ATTACK`
- Matched term(s): `knockdown`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4F9B50`: `DRONE_BREAKCLINCH`
  - `0x4F9B64`: `DRONE_CLINCH`
  - `0x4F9B74`: `out of memory`
  - `0x4F9B88`: `DRONE_STATE_IDLE`
  - `0x4F9BA0`: `DRONE_KNOCKDOWN_ATTACK`
  - `0x4F9BB8`: `out of memory`
  - `0x4F9BC8`: `DRONE_MOVEMENT`
  - `0x4F9BD8`: `out of memory`
  - `0x4F9C10`: `out of memory`
  - `0x4F9C20`: `out of memory`
- Surrounding 128 bytes: `48 00 00 00 44 52 4f 4e 45 5f 43 4c 49 4e 43 48 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 44 52 4f 4e 45 5f 53 54 41 54 45 5f 49 44 4c 45 00 00 00 00 00 00 00 00 44 52 4f 4e 45 5f 4b 4e 4f 43 4b 44 4f 57 4e 5f 41 54 54 41 43 4b 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 44 52 4f 4e 45 5f 4d 4f 56 45 4d 45 4e 54 00 00 6f 75 74 20 6f 66 20 6d`

## `BOOT.BIN` @ `0x4F9BC8`: `DRONE_MOVEMENT`
- Matched term(s): (context match)
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4F9B74`: `out of memory`
  - `0x4F9B88`: `DRONE_STATE_IDLE`
  - `0x4F9BA0`: `DRONE_KNOCKDOWN_ATTACK`
  - `0x4F9BB8`: `out of memory`
  - `0x4F9BC8`: `DRONE_MOVEMENT`
  - `0x4F9BD8`: `out of memory`
  - `0x4F9C10`: `out of memory`
  - `0x4F9C20`: `out of memory`
  - `0x4F9C50`: `out of memory`
  - `0x4F9C60`: `out of memory`
- Surrounding 128 bytes: `44 52 4f 4e 45 5f 53 54 41 54 45 5f 49 44 4c 45 00 00 00 00 00 00 00 00 44 52 4f 4e 45 5f 4b 4e 4f 43 4b 44 4f 57 4e 5f 41 54 54 41 43 4b 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 44 52 4f 4e 45 5f 4d 4f 56 45 4d 45 4e 54 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 74 42 06 00 7c 42 06 00 8c 42 06 00 9c 42 06 00 ac 42 06 00 bc 42 06 00 cc 42 06 00 dc 42 06 00`

## `BOOT.BIN` @ `0x4F9D5C`: `scripts.viv`
- Matched term(s): `scripts.viv`, `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x4F9C70`: `out of memory`
  - `0x4F9C80`: `out of memory`
  - `0x4F9C90`: `out of memory`
  - `0x4F9D28`: `out of memory`
  - `0x4F9D5C`: `scripts.viv`
  - `0x4F9D68`: `Player 2`
  - `0x4F9D74`: `Player %d`
  - `0x4F9D80`: `out of memory`
  - `0x4F9D90`: `out of memory`
  - `0x4F9DA0`: `out of memory`
- Surrounding 128 bytes: `c4 e5 07 00 a4 e5 07 00 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 2c 02 08 00 40 02 08 00 54 02 08 00 68 02 08 00 a4 02 08 00 7c 02 08 00 90 02 08 00 00 00 00 00 2f 00 00 00 73 63 72 69 70 74 73 2e 76 69 76 00 50 6c 61 79 65 72 20 32 00 00 00 00 50 6c 61 79 65 72 20 25 64 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72`

## `BOOT.BIN` @ `0x4F9F10`: `dec damage taken from clean punch`
- Matched term(s): `damage`, `punch`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4F9EA0`: `dec rate max E reduction`
  - `0x4F9EBC`: `dec rate max H reduction`
  - `0x4F9ED8`: `inc current E regen rate`
  - `0x4F9EF4`: `inc current H regen rate`
  - `0x4F9F10`: `dec damage taken from clean punch`
  - `0x4F9F34`: `dec damage taken from blocked punch`
  - `0x4F9F58`: `dec damage taken from body punch`
  - `0x4F9F7C`: `dec damage taken from head punch`
  - `0x4F9FA0`: `dec chance for cut`
  - `0x4F9FB4`: `inc opp chance for cut`
- Surrounding 128 bytes: `74 69 6f 6e 00 00 00 00 69 6e 63 20 63 75 72 72 65 6e 74 20 45 20 72 65 67 65 6e 20 72 61 74 65 00 00 00 00 69 6e 63 20 63 75 72 72 65 6e 74 20 48 20 72 65 67 65 6e 20 72 61 74 65 00 00 00 00 64 65 63 20 64 61 6d 61 67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 63 6c 65 61 6e 20 70 75 6e 63 68 00 00 00 64 65 63 20 64 61 6d 61 67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 62 6c 6f 63 6b 65`

## `BOOT.BIN` @ `0x4F9F34`: `dec damage taken from blocked punch`
- Matched term(s): `damage`, `punch`, `block`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4F9EBC`: `dec rate max H reduction`
  - `0x4F9ED8`: `inc current E regen rate`
  - `0x4F9EF4`: `inc current H regen rate`
  - `0x4F9F10`: `dec damage taken from clean punch`
  - `0x4F9F34`: `dec damage taken from blocked punch`
  - `0x4F9F58`: `dec damage taken from body punch`
  - `0x4F9F7C`: `dec damage taken from head punch`
  - `0x4F9FA0`: `dec chance for cut`
  - `0x4F9FB4`: `inc opp chance for cut`
  - `0x4F9FCC`: `dec chance for injury`
- Surrounding 128 bytes: `69 6e 63 20 63 75 72 72 65 6e 74 20 48 20 72 65 67 65 6e 20 72 61 74 65 00 00 00 00 64 65 63 20 64 61 6d 61 67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 63 6c 65 61 6e 20 70 75 6e 63 68 00 00 00 64 65 63 20 64 61 6d 61 67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 62 6c 6f 63 6b 65 64 20 70 75 6e 63 68 00 64 65 63 20 64 61 6d 61 67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 62 6f 64 79 20 70`

## `BOOT.BIN` @ `0x4F9F58`: `dec damage taken from body punch`
- Matched term(s): `damage`, `punch`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4F9ED8`: `inc current E regen rate`
  - `0x4F9EF4`: `inc current H regen rate`
  - `0x4F9F10`: `dec damage taken from clean punch`
  - `0x4F9F34`: `dec damage taken from blocked punch`
  - `0x4F9F58`: `dec damage taken from body punch`
  - `0x4F9F7C`: `dec damage taken from head punch`
  - `0x4F9FA0`: `dec chance for cut`
  - `0x4F9FB4`: `inc opp chance for cut`
  - `0x4F9FCC`: `dec chance for injury`
  - `0x4F9FE4`: `inc opp chance for injury`
- Surrounding 128 bytes: `67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 63 6c 65 61 6e 20 70 75 6e 63 68 00 00 00 64 65 63 20 64 61 6d 61 67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 62 6c 6f 63 6b 65 64 20 70 75 6e 63 68 00 64 65 63 20 64 61 6d 61 67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 62 6f 64 79 20 70 75 6e 63 68 00 00 00 00 64 65 63 20 64 61 6d 61 67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 68 65 61 64 20 70`

## `BOOT.BIN` @ `0x4F9F7C`: `dec damage taken from head punch`
- Matched term(s): `damage`, `punch`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4F9EF4`: `inc current H regen rate`
  - `0x4F9F10`: `dec damage taken from clean punch`
  - `0x4F9F34`: `dec damage taken from blocked punch`
  - `0x4F9F58`: `dec damage taken from body punch`
  - `0x4F9F7C`: `dec damage taken from head punch`
  - `0x4F9FA0`: `dec chance for cut`
  - `0x4F9FB4`: `inc opp chance for cut`
  - `0x4F9FCC`: `dec chance for injury`
  - `0x4F9FE4`: `inc opp chance for injury`
  - `0x4FA000`: `inc tcc cuts heal rate`
- Surrounding 128 bytes: `67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 62 6c 6f 63 6b 65 64 20 70 75 6e 63 68 00 64 65 63 20 64 61 6d 61 67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 62 6f 64 79 20 70 75 6e 63 68 00 00 00 00 64 65 63 20 64 61 6d 61 67 65 20 74 61 6b 65 6e 20 66 72 6f 6d 20 68 65 61 64 20 70 75 6e 63 68 00 00 00 00 64 65 63 20 63 68 61 6e 63 65 20 66 6f 72 20 63 75 74 00 00 69 6e 63 20 6f 70 70 20`

## `BOOT.BIN` @ `0x4FA084`: `inc all attack damage`
- Matched term(s): `damage`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA030`: `inc between round max E regen rate`
  - `0x4FA054`: `inc move speed`
  - `0x4FA064`: `inc block speed`
  - `0x4FA074`: `inc lean speed`
  - `0x4FA084`: `inc all attack damage`
  - `0x4FA09C`: `inc uppercut damage`
  - `0x4FA0B0`: `inc hook damage`
  - `0x4FA0C0`: `inc straight damage`
  - `0x4FA0D4`: `inc jab damage`
  - `0x4FA0E4`: `inc lead attack damage`
- Surrounding 128 bytes: `78 20 45 20 72 65 67 65 6e 20 72 61 74 65 00 00 69 6e 63 20 6d 6f 76 65 20 73 70 65 65 64 00 00 69 6e 63 20 62 6c 6f 63 6b 20 73 70 65 65 64 00 69 6e 63 20 6c 65 61 6e 20 73 70 65 65 64 00 00 69 6e 63 20 61 6c 6c 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 00 69 6e 63 20 75 70 70 65 72 63 75 74 20 64 61 6d 61 67 65 00 69 6e 63 20 68 6f 6f 6b 20 64 61 6d 61 67 65 00 69 6e 63 20`

## `BOOT.BIN` @ `0x4FA09C`: `inc uppercut damage`
- Matched term(s): `damage`, `uppercut`, `cut`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA054`: `inc move speed`
  - `0x4FA064`: `inc block speed`
  - `0x4FA074`: `inc lean speed`
  - `0x4FA084`: `inc all attack damage`
  - `0x4FA09C`: `inc uppercut damage`
  - `0x4FA0B0`: `inc hook damage`
  - `0x4FA0C0`: `inc straight damage`
  - `0x4FA0D4`: `inc jab damage`
  - `0x4FA0E4`: `inc lead attack damage`
  - `0x4FA0FC`: `inc rear attack damage`
- Surrounding 128 bytes: `20 73 70 65 65 64 00 00 69 6e 63 20 62 6c 6f 63 6b 20 73 70 65 65 64 00 69 6e 63 20 6c 65 61 6e 20 73 70 65 65 64 00 00 69 6e 63 20 61 6c 6c 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 00 69 6e 63 20 75 70 70 65 72 63 75 74 20 64 61 6d 61 67 65 00 69 6e 63 20 68 6f 6f 6b 20 64 61 6d 61 67 65 00 69 6e 63 20 73 74 72 61 69 67 68 74 20 64 61 6d 61 67 65 00 69 6e 63 20 6a 61 62 20`

## `BOOT.BIN` @ `0x4FA0B0`: `inc hook damage`
- Matched term(s): `damage`, `hook`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA064`: `inc block speed`
  - `0x4FA074`: `inc lean speed`
  - `0x4FA084`: `inc all attack damage`
  - `0x4FA09C`: `inc uppercut damage`
  - `0x4FA0B0`: `inc hook damage`
  - `0x4FA0C0`: `inc straight damage`
  - `0x4FA0D4`: `inc jab damage`
  - `0x4FA0E4`: `inc lead attack damage`
  - `0x4FA0FC`: `inc rear attack damage`
  - `0x4FA114`: `inc rolling power damage`
- Surrounding 128 bytes: `65 65 64 00 69 6e 63 20 6c 65 61 6e 20 73 70 65 65 64 00 00 69 6e 63 20 61 6c 6c 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 00 69 6e 63 20 75 70 70 65 72 63 75 74 20 64 61 6d 61 67 65 00 69 6e 63 20 68 6f 6f 6b 20 64 61 6d 61 67 65 00 69 6e 63 20 73 74 72 61 69 67 68 74 20 64 61 6d 61 67 65 00 69 6e 63 20 6a 61 62 20 64 61 6d 61 67 65 00 00 69 6e 63 20 6c 65 61 64 20 61 74 74`

## `BOOT.BIN` @ `0x4FA0C0`: `inc straight damage`
- Matched term(s): `damage`, `AI`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA074`: `inc lean speed`
  - `0x4FA084`: `inc all attack damage`
  - `0x4FA09C`: `inc uppercut damage`
  - `0x4FA0B0`: `inc hook damage`
  - `0x4FA0C0`: `inc straight damage`
  - `0x4FA0D4`: `inc jab damage`
  - `0x4FA0E4`: `inc lead attack damage`
  - `0x4FA0FC`: `inc rear attack damage`
  - `0x4FA114`: `inc rolling power damage`
  - `0x4FA130`: `dec perry vulnerable time`
- Surrounding 128 bytes: `65 64 00 00 69 6e 63 20 61 6c 6c 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 00 69 6e 63 20 75 70 70 65 72 63 75 74 20 64 61 6d 61 67 65 00 69 6e 63 20 68 6f 6f 6b 20 64 61 6d 61 67 65 00 69 6e 63 20 73 74 72 61 69 67 68 74 20 64 61 6d 61 67 65 00 69 6e 63 20 6a 61 62 20 64 61 6d 61 67 65 00 00 69 6e 63 20 6c 65 61 64 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 69 6e 63 20`

## `BOOT.BIN` @ `0x4FA0D4`: `inc jab damage`
- Matched term(s): `damage`, `jab`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA084`: `inc all attack damage`
  - `0x4FA09C`: `inc uppercut damage`
  - `0x4FA0B0`: `inc hook damage`
  - `0x4FA0C0`: `inc straight damage`
  - `0x4FA0D4`: `inc jab damage`
  - `0x4FA0E4`: `inc lead attack damage`
  - `0x4FA0FC`: `inc rear attack damage`
  - `0x4FA114`: `inc rolling power damage`
  - `0x4FA130`: `dec perry vulnerable time`
  - `0x4FA14C`: `inc opp perry vulnerable time`
- Surrounding 128 bytes: `61 6d 61 67 65 00 00 00 69 6e 63 20 75 70 70 65 72 63 75 74 20 64 61 6d 61 67 65 00 69 6e 63 20 68 6f 6f 6b 20 64 61 6d 61 67 65 00 69 6e 63 20 73 74 72 61 69 67 68 74 20 64 61 6d 61 67 65 00 69 6e 63 20 6a 61 62 20 64 61 6d 61 67 65 00 00 69 6e 63 20 6c 65 61 64 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 69 6e 63 20 72 65 61 72 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00`

## `BOOT.BIN` @ `0x4FA0E4`: `inc lead attack damage`
- Matched term(s): `damage`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA09C`: `inc uppercut damage`
  - `0x4FA0B0`: `inc hook damage`
  - `0x4FA0C0`: `inc straight damage`
  - `0x4FA0D4`: `inc jab damage`
  - `0x4FA0E4`: `inc lead attack damage`
  - `0x4FA0FC`: `inc rear attack damage`
  - `0x4FA114`: `inc rolling power damage`
  - `0x4FA130`: `dec perry vulnerable time`
  - `0x4FA14C`: `inc opp perry vulnerable time`
  - `0x4FA16C`: `inc chance E boost`
- Surrounding 128 bytes: `72 63 75 74 20 64 61 6d 61 67 65 00 69 6e 63 20 68 6f 6f 6b 20 64 61 6d 61 67 65 00 69 6e 63 20 73 74 72 61 69 67 68 74 20 64 61 6d 61 67 65 00 69 6e 63 20 6a 61 62 20 64 61 6d 61 67 65 00 00 69 6e 63 20 6c 65 61 64 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 69 6e 63 20 72 65 61 72 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 69 6e 63 20 72 6f 6c 6c 69 6e 67 20 70 6f 77 65`

## `BOOT.BIN` @ `0x4FA0FC`: `inc rear attack damage`
- Matched term(s): `damage`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA0B0`: `inc hook damage`
  - `0x4FA0C0`: `inc straight damage`
  - `0x4FA0D4`: `inc jab damage`
  - `0x4FA0E4`: `inc lead attack damage`
  - `0x4FA0FC`: `inc rear attack damage`
  - `0x4FA114`: `inc rolling power damage`
  - `0x4FA130`: `dec perry vulnerable time`
  - `0x4FA14C`: `inc opp perry vulnerable time`
  - `0x4FA16C`: `inc chance E boost`
  - `0x4FA180`: `inc length E boost`
- Surrounding 128 bytes: `61 67 65 00 69 6e 63 20 73 74 72 61 69 67 68 74 20 64 61 6d 61 67 65 00 69 6e 63 20 6a 61 62 20 64 61 6d 61 67 65 00 00 69 6e 63 20 6c 65 61 64 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 69 6e 63 20 72 65 61 72 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 69 6e 63 20 72 6f 6c 6c 69 6e 67 20 70 6f 77 65 72 20 64 61 6d 61 67 65 00 00 00 00 64 65 63 20 70 65 72 72 79 20 76 75`

## `BOOT.BIN` @ `0x4FA114`: `inc rolling power damage`
- Matched term(s): `damage`, `power`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA0C0`: `inc straight damage`
  - `0x4FA0D4`: `inc jab damage`
  - `0x4FA0E4`: `inc lead attack damage`
  - `0x4FA0FC`: `inc rear attack damage`
  - `0x4FA114`: `inc rolling power damage`
  - `0x4FA130`: `dec perry vulnerable time`
  - `0x4FA14C`: `inc opp perry vulnerable time`
  - `0x4FA16C`: `inc chance E boost`
  - `0x4FA180`: `inc length E boost`
  - `0x4FA194`: `dec KO moment length`
- Surrounding 128 bytes: `69 6e 63 20 6a 61 62 20 64 61 6d 61 67 65 00 00 69 6e 63 20 6c 65 61 64 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 69 6e 63 20 72 65 61 72 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 69 6e 63 20 72 6f 6c 6c 69 6e 67 20 70 6f 77 65 72 20 64 61 6d 61 67 65 00 00 00 00 64 65 63 20 70 65 72 72 79 20 76 75 6c 6e 65 72 61 62 6c 65 20 74 69 6d 65 00 00 00 69 6e 63 20 6f 70 70 20`

## `BOOT.BIN` @ `0x4FA234`: `dec swelling`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4FA1C8`: `inc knockdown recover chance`
  - `0x4FA1E8`: `dec opp knockdown recover chance`
  - `0x4FA20C`: `dec called`
  - `0x4FA218`: `inc chance opp can't parry`
  - `0x4FA234`: `dec swelling`
  - `0x4FA244`: `inc opp swelling`
  - `0x4FA258`: `inc chance undetected illegal`
  - `0x4FA278`: `rival inc chance undetected illegal`
  - `0x4FA29C`: `inc moving attack damage`
  - `0x4FA2B8`: `inc chance clinch thru punch`
- Surrounding 128 bytes: `6b 64 6f 77 6e 20 72 65 63 6f 76 65 72 20 63 68 61 6e 63 65 00 00 00 00 64 65 63 20 63 61 6c 6c 65 64 00 00 69 6e 63 20 63 68 61 6e 63 65 20 6f 70 70 20 63 61 6e 27 74 20 70 61 72 72 79 00 00 64 65 63 20 73 77 65 6c 6c 69 6e 67 00 00 00 00 69 6e 63 20 6f 70 70 20 73 77 65 6c 6c 69 6e 67 00 00 00 00 69 6e 63 20 63 68 61 6e 63 65 20 75 6e 64 65 74 65 63 74 65 64 20 69 6c 6c 65 67 61`

## `BOOT.BIN` @ `0x4FA244`: `inc opp swelling`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4FA1E8`: `dec opp knockdown recover chance`
  - `0x4FA20C`: `dec called`
  - `0x4FA218`: `inc chance opp can't parry`
  - `0x4FA234`: `dec swelling`
  - `0x4FA244`: `inc opp swelling`
  - `0x4FA258`: `inc chance undetected illegal`
  - `0x4FA278`: `rival inc chance undetected illegal`
  - `0x4FA29C`: `inc moving attack damage`
  - `0x4FA2B8`: `inc chance clinch thru punch`
  - `0x4FA2D8`: `inc chance to sustain punch during KO moment`
- Surrounding 128 bytes: `61 6e 63 65 00 00 00 00 64 65 63 20 63 61 6c 6c 65 64 00 00 69 6e 63 20 63 68 61 6e 63 65 20 6f 70 70 20 63 61 6e 27 74 20 70 61 72 72 79 00 00 64 65 63 20 73 77 65 6c 6c 69 6e 67 00 00 00 00 69 6e 63 20 6f 70 70 20 73 77 65 6c 6c 69 6e 67 00 00 00 00 69 6e 63 20 63 68 61 6e 63 65 20 75 6e 64 65 74 65 63 74 65 64 20 69 6c 6c 65 67 61 6c 00 00 00 72 69 76 61 6c 20 69 6e 63 20 63 68`

## `BOOT.BIN` @ `0x4FA29C`: `inc moving attack damage`
- Matched term(s): `damage`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA234`: `dec swelling`
  - `0x4FA244`: `inc opp swelling`
  - `0x4FA258`: `inc chance undetected illegal`
  - `0x4FA278`: `rival inc chance undetected illegal`
  - `0x4FA29C`: `inc moving attack damage`
  - `0x4FA2B8`: `inc chance clinch thru punch`
  - `0x4FA2D8`: `inc chance to sustain punch during KO moment`
  - `0x4FA308`: `inc chance flash KO`
  - `0x4FA31C`: `dec chance to be flash KOd`
  - `0x4FA338`: `inc chance that jab won't be parried`
- Surrounding 128 bytes: `63 68 61 6e 63 65 20 75 6e 64 65 74 65 63 74 65 64 20 69 6c 6c 65 67 61 6c 00 00 00 72 69 76 61 6c 20 69 6e 63 20 63 68 61 6e 63 65 20 75 6e 64 65 74 65 63 74 65 64 20 69 6c 6c 65 67 61 6c 00 69 6e 63 20 6d 6f 76 69 6e 67 20 61 74 74 61 63 6b 20 64 61 6d 61 67 65 00 00 00 00 69 6e 63 20 63 68 61 6e 63 65 20 63 6c 69 6e 63 68 20 74 68 72 75 20 70 75 6e 63 68 00 00 00 00 69 6e 63 20`

## `BOOT.BIN` @ `0x4FA360`: `inc combo punch damage`
- Matched term(s): `damage`, `punch`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA2D8`: `inc chance to sustain punch during KO moment`
  - `0x4FA308`: `inc chance flash KO`
  - `0x4FA31C`: `dec chance to be flash KOd`
  - `0x4FA338`: `inc chance that jab won't be parried`
  - `0x4FA360`: `inc combo punch damage`
  - `0x4FA378`: `inc damage when your punch hits a non-directional block`
  - `0x4FA3B0`: `inc amount of opp punch redirection`
  - `0x4FA3D4`: `dec your punch redirection amt`
  - `0x4FA3F4`: `ai/mods/p%d/misc offense`
  - `0x4FA410`: `ai/mods/p%d/defense`
- Surrounding 128 bytes: `63 68 61 6e 63 65 20 74 6f 20 62 65 20 66 6c 61 73 68 20 4b 4f 64 00 00 69 6e 63 20 63 68 61 6e 63 65 20 74 68 61 74 20 6a 61 62 20 77 6f 6e 27 74 20 62 65 20 70 61 72 72 69 65 64 00 00 00 00 69 6e 63 20 63 6f 6d 62 6f 20 70 75 6e 63 68 20 64 61 6d 61 67 65 00 00 69 6e 63 20 64 61 6d 61 67 65 20 77 68 65 6e 20 79 6f 75 72 20 70 75 6e 63 68 20 68 69 74 73 20 61 20 6e 6f 6e 2d 64 69`

## `BOOT.BIN` @ `0x4FA378`: `inc damage when your punch hits a non-directional block`
- Matched term(s): `damage`, `punch`, `block`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x4FA308`: `inc chance flash KO`
  - `0x4FA31C`: `dec chance to be flash KOd`
  - `0x4FA338`: `inc chance that jab won't be parried`
  - `0x4FA360`: `inc combo punch damage`
  - `0x4FA378`: `inc damage when your punch hits a non-directional block`
  - `0x4FA3B0`: `inc amount of opp punch redirection`
  - `0x4FA3D4`: `dec your punch redirection amt`
  - `0x4FA3F4`: `ai/mods/p%d/misc offense`
  - `0x4FA410`: `ai/mods/p%d/defense`
  - `0x4FA424`: `ai/mods/p%d/bagotricks`
- Surrounding 128 bytes: `69 6e 63 20 63 68 61 6e 63 65 20 74 68 61 74 20 6a 61 62 20 77 6f 6e 27 74 20 62 65 20 70 61 72 72 69 65 64 00 00 00 00 69 6e 63 20 63 6f 6d 62 6f 20 70 75 6e 63 68 20 64 61 6d 61 67 65 00 00 69 6e 63 20 64 61 6d 61 67 65 20 77 68 65 6e 20 79 6f 75 72 20 70 75 6e 63 68 20 68 69 74 73 20 61 20 6e 6f 6e 2d 64 69 72 65 63 74 69 6f 6e 61 6c 20 62 6c 6f 63 6b 00 69 6e 63 20 61 6d 6f 75`

## `BOOT.BIN` @ `0x4FA3F4`: `ai/mods/p%d/misc offense`
- Matched term(s): `AI`
- Assessment: **meaningful**
- Why it matters: AI/drone behavior label; useful for locating AI setup or event/state code.
- Nearby printable strings:
  - `0x4FA360`: `inc combo punch damage`
  - `0x4FA378`: `inc damage when your punch hits a non-directional block`
  - `0x4FA3B0`: `inc amount of opp punch redirection`
  - `0x4FA3D4`: `dec your punch redirection amt`
  - `0x4FA3F4`: `ai/mods/p%d/misc offense`
  - `0x4FA410`: `ai/mods/p%d/defense`
  - `0x4FA424`: `ai/mods/p%d/bagotricks`
  - `0x4FA43C`: `ai/mods/p%d/attack power`
  - `0x4FA458`: `ai/mods/p%d/energy and health`
  - `0x4FA478`: `ai/mods/p%d/phys damage`
- Surrounding 128 bytes: `61 6d 6f 75 6e 74 20 6f 66 20 6f 70 70 20 70 75 6e 63 68 20 72 65 64 69 72 65 63 74 69 6f 6e 00 64 65 63 20 79 6f 75 72 20 70 75 6e 63 68 20 72 65 64 69 72 65 63 74 69 6f 6e 20 61 6d 74 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 6d 69 73 63 20 6f 66 66 65 6e 73 65 00 00 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 64 65 66 65 6e 73 65 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 62 61 67 6f`

## `BOOT.BIN` @ `0x4FA410`: `ai/mods/p%d/defense`
- Matched term(s): `AI`
- Assessment: **meaningful**
- Why it matters: AI/drone behavior label; useful for locating AI setup or event/state code.
- Nearby printable strings:
  - `0x4FA378`: `inc damage when your punch hits a non-directional block`
  - `0x4FA3B0`: `inc amount of opp punch redirection`
  - `0x4FA3D4`: `dec your punch redirection amt`
  - `0x4FA3F4`: `ai/mods/p%d/misc offense`
  - `0x4FA410`: `ai/mods/p%d/defense`
  - `0x4FA424`: `ai/mods/p%d/bagotricks`
  - `0x4FA43C`: `ai/mods/p%d/attack power`
  - `0x4FA458`: `ai/mods/p%d/energy and health`
  - `0x4FA478`: `ai/mods/p%d/phys damage`
  - `0x4FA490`: `out of memory`
- Surrounding 128 bytes: `69 6f 6e 00 64 65 63 20 79 6f 75 72 20 70 75 6e 63 68 20 72 65 64 69 72 65 63 74 69 6f 6e 20 61 6d 74 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 6d 69 73 63 20 6f 66 66 65 6e 73 65 00 00 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 64 65 66 65 6e 73 65 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 62 61 67 6f 74 72 69 63 6b 73 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 61 74 74 61 63 6b 20 70`

## `BOOT.BIN` @ `0x4FA424`: `ai/mods/p%d/bagotricks`
- Matched term(s): `AI`
- Assessment: **meaningful**
- Why it matters: AI/drone behavior label; useful for locating AI setup or event/state code.
- Nearby printable strings:
  - `0x4FA3B0`: `inc amount of opp punch redirection`
  - `0x4FA3D4`: `dec your punch redirection amt`
  - `0x4FA3F4`: `ai/mods/p%d/misc offense`
  - `0x4FA410`: `ai/mods/p%d/defense`
  - `0x4FA424`: `ai/mods/p%d/bagotricks`
  - `0x4FA43C`: `ai/mods/p%d/attack power`
  - `0x4FA458`: `ai/mods/p%d/energy and health`
  - `0x4FA478`: `ai/mods/p%d/phys damage`
  - `0x4FA490`: `out of memory`
  - `0x4FA4A0`: `out of memory`
- Surrounding 128 bytes: `65 64 69 72 65 63 74 69 6f 6e 20 61 6d 74 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 6d 69 73 63 20 6f 66 66 65 6e 73 65 00 00 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 64 65 66 65 6e 73 65 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 62 61 67 6f 74 72 69 63 6b 73 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 61 74 74 61 63 6b 20 70 6f 77 65 72 00 00 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f`

## `BOOT.BIN` @ `0x4FA43C`: `ai/mods/p%d/attack power`
- Matched term(s): `power`, `AI`
- Assessment: **meaningful**
- Why it matters: AI/drone behavior label; useful for locating AI setup or event/state code.
- Nearby printable strings:
  - `0x4FA3D4`: `dec your punch redirection amt`
  - `0x4FA3F4`: `ai/mods/p%d/misc offense`
  - `0x4FA410`: `ai/mods/p%d/defense`
  - `0x4FA424`: `ai/mods/p%d/bagotricks`
  - `0x4FA43C`: `ai/mods/p%d/attack power`
  - `0x4FA458`: `ai/mods/p%d/energy and health`
  - `0x4FA478`: `ai/mods/p%d/phys damage`
  - `0x4FA490`: `out of memory`
  - `0x4FA4A0`: `out of memory`
  - `0x4FA4B8`: `out of memory`
- Surrounding 128 bytes: `70 25 64 2f 6d 69 73 63 20 6f 66 66 65 6e 73 65 00 00 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 64 65 66 65 6e 73 65 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 62 61 67 6f 74 72 69 63 6b 73 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 61 74 74 61 63 6b 20 70 6f 77 65 72 00 00 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 65 6e 65 72 67 79 20 61 6e 64 20 68 65 61 6c 74 68 00 00 00 61 69 2f 6d`

## `BOOT.BIN` @ `0x4FA458`: `ai/mods/p%d/energy and health`
- Matched term(s): `health`, `AI`
- Assessment: **meaningful**
- Why it matters: AI/drone behavior label; useful for locating AI setup or event/state code.
- Nearby printable strings:
  - `0x4FA3F4`: `ai/mods/p%d/misc offense`
  - `0x4FA410`: `ai/mods/p%d/defense`
  - `0x4FA424`: `ai/mods/p%d/bagotricks`
  - `0x4FA43C`: `ai/mods/p%d/attack power`
  - `0x4FA458`: `ai/mods/p%d/energy and health`
  - `0x4FA478`: `ai/mods/p%d/phys damage`
  - `0x4FA490`: `out of memory`
  - `0x4FA4A0`: `out of memory`
  - `0x4FA4B8`: `out of memory`
  - `0x4FA4C8`: `MUHAMMAD`
- Surrounding 128 bytes: `70 25 64 2f 64 65 66 65 6e 73 65 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 62 61 67 6f 74 72 69 63 6b 73 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 61 74 74 61 63 6b 20 70 6f 77 65 72 00 00 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 65 6e 65 72 67 79 20 61 6e 64 20 68 65 61 6c 74 68 00 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 70 68 79 73 20 64 61 6d 61 67 65 00 6f 75 74 20 6f 66 20 6d`

## `BOOT.BIN` @ `0x4FA478`: `ai/mods/p%d/phys damage`
- Matched term(s): `damage`, `AI`
- Assessment: **meaningful**
- Why it matters: AI/drone behavior label; useful for locating AI setup or event/state code.
- Nearby printable strings:
  - `0x4FA410`: `ai/mods/p%d/defense`
  - `0x4FA424`: `ai/mods/p%d/bagotricks`
  - `0x4FA43C`: `ai/mods/p%d/attack power`
  - `0x4FA458`: `ai/mods/p%d/energy and health`
  - `0x4FA478`: `ai/mods/p%d/phys damage`
  - `0x4FA490`: `out of memory`
  - `0x4FA4A0`: `out of memory`
  - `0x4FA4B8`: `out of memory`
  - `0x4FA4C8`: `MUHAMMAD`
  - `0x4FA4D8`: `out of memory`
- Surrounding 128 bytes: `6b 73 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 61 74 74 61 63 6b 20 70 6f 77 65 72 00 00 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 65 6e 65 72 67 79 20 61 6e 64 20 68 65 61 6c 74 68 00 00 00 61 69 2f 6d 6f 64 73 2f 70 25 64 2f 70 68 79 73 20 64 61 6d 61 67 65 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 00 00 00 00`

## `BOOT.BIN` @ `0x4FA598`: `Venue Script`
- Matched term(s): `venue`
- Assessment: **meaningful**
- Why it matters: Venue label/table/archive context; may lead to venue selection/loading.
- Nearby printable strings:
  - `0x4FA564`: `%s %s %s %s`
  - `0x4FA570`: `animNum == %d`
  - `0x4FA580`: `out of memory`
  - `0x4FA590`: `trainer`
  - `0x4FA598`: `Venue Script`
  - `0x4FA5A8`: `Entrance Box1 Script`
  - `0x4FA5C0`: `Entrance Box2 Script`
  - `0x4FA5D8`: `Faceoff Script`
  - `0x4FA5E8`: `Decision Announcement Script`
  - `0x4FA608`: `Winner Celebration Script`
- Surrounding 128 bytes: `4e 75 6d 20 3d 3d 20 25 64 00 00 00 25 73 20 25 73 20 25 73 20 25 73 0a 61 6e 69 6d 4e 75 6d 20 3d 3d 20 25 64 0a 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 74 72 61 69 6e 65 72 00 56 65 6e 75 65 20 53 63 72 69 70 74 00 00 00 00 45 6e 74 72 61 6e 63 65 20 42 6f 78 31 20 53 63 72 69 70 74 00 00 00 00 45 6e 74 72 61 6e 63 65 20 42 6f 78 32 20 53 63 72 69 70 74 00 00 00 00`

## `BOOT.BIN` @ `0x4FA6C4`: `Scorecards`
- Matched term(s): `scorecard`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4FA678`: `Corner Script 2`
  - `0x4FA688`: `Knockdown Replay 1`
  - `0x4FA69C`: `Knockdown Replay 2`
  - `0x4FA6B0`: `Knockdown Replay 3`
  - `0x4FA6C4`: `Scorecards`
  - `0x4FA6D0`: `Punch Stats`
  - `0x4FA6DC`: `Unlocked Items`
  - `0x4FA6F0`: `out of memory`
  - `0x4FA770`: `out of memory`
  - `0x4FA78C`: ` 00  00  00`
- Surrounding 128 bytes: `74 20 32 00 4b 6e 6f 63 6b 64 6f 77 6e 20 52 65 70 6c 61 79 20 31 00 00 4b 6e 6f 63 6b 64 6f 77 6e 20 52 65 70 6c 61 79 20 32 00 00 4b 6e 6f 63 6b 64 6f 77 6e 20 52 65 70 6c 61 79 20 33 00 00 53 63 6f 72 65 63 61 72 64 73 00 00 50 75 6e 63 68 20 53 74 61 74 73 00 55 6e 6c 6f 63 6b 65 64 20 49 74 65 6d 73 00 00 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 e8 00 0b 00`

## `BOOT.BIN` @ `0x4FA6D0`: `Punch Stats`
- Matched term(s): `punch`
- Assessment: **meaningful**
- Why it matters: Combat action/control label; xrefs may lead to input/combat state code.
- Nearby printable strings:
  - `0x4FA688`: `Knockdown Replay 1`
  - `0x4FA69C`: `Knockdown Replay 2`
  - `0x4FA6B0`: `Knockdown Replay 3`
  - `0x4FA6C4`: `Scorecards`
  - `0x4FA6D0`: `Punch Stats`
  - `0x4FA6DC`: `Unlocked Items`
  - `0x4FA6F0`: `out of memory`
  - `0x4FA770`: `out of memory`
  - `0x4FA78C`: ` 00  00  00`
  - `0x4FA798`: `Zoom:`
- Surrounding 128 bytes: `6e 20 52 65 70 6c 61 79 20 31 00 00 4b 6e 6f 63 6b 64 6f 77 6e 20 52 65 70 6c 61 79 20 32 00 00 4b 6e 6f 63 6b 64 6f 77 6e 20 52 65 70 6c 61 79 20 33 00 00 53 63 6f 72 65 63 61 72 64 73 00 00 50 75 6e 63 68 20 53 74 61 74 73 00 55 6e 6c 6f 63 6b 65 64 20 49 74 65 6d 73 00 00 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 e8 00 0b 00 f8 00 0b 00 38 01 0b 00 54 01 0b 00`

## `BOOT.BIN` @ `0x4FA8E0`: `cutman`
- Matched term(s): `cutman`, `cut`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x4FA8B4`: `bottleR`
  - `0x4FA8BC`: `armR`
  - `0x4FA8C4`: `wristbandR`
  - `0x4FA8D0`: `out of memory`
  - `0x4FA8E0`: `cutman`
  - `0x4FAAB8`: `out of memory`
  - `0x4FAAC8`: `out of memory`
  - `0x4FAAD8`: `EventNull<%p>`
  - `0x4FAAE8`: `EventStackBase - Suspiciously large number of bit events (%u).  Maybe an unterminated bit array?`
  - `0x4FAB4C`: `EventStackBase - Size cannot be smaller than %u`
- Surrounding 128 bytes: `73 77 65 6c 6c 68 61 6e 64 32 52 00 73 77 61 62 52 00 00 00 62 6f 74 74 6c 65 52 00 61 72 6d 52 00 00 00 00 77 72 69 73 74 62 61 6e 64 52 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 63 75 74 6d 61 6e 00 00 c4 b5 0b 00 04 b6 0b 00 e4 b5 0b 00 a4 b5 0b 00 c4 b5 0b 00 c4 b5 0b 00 04 b6 0b 00 04 b6 0b 00 e4 b5 0b 00 e4 b5 0b 00 a4 b5 0b 00 a4 b5 0b 00 30 b8 0b 00 44 b7 0b 00`

## `BOOT.BIN` @ `0x4FB330`: `anibiscr.zlb`
- Matched term(s): `zlb`
- Assessment: **meaningful**
- Why it matters: ZLB package path/string; likely compressed package/resource reference to trace through loader xrefs.
- Nearby printable strings:
  - `0x4FB2F0`: `anim/procedural/eyes_%X`
  - `0x4FB308`: `anibcore.bin`
  - `0x4FB318`: `anibic.bin`
  - `0x4FB324`: `anibibr.bin`
  - `0x4FB330`: `anibiscr.zlb`
  - `0x4FB340`: `anibitra.bin`
  - `0x4FB350`: `anibispd.bin`
  - `0x4FB360`: `anibibal.bin`
  - `0x4FB370`: `anibipow.bin`
  - `0x4FB380`: `anibiali.bin`
- Surrounding 128 bytes: `61 6e 69 6d 2f 70 72 6f 63 65 64 75 72 61 6c 2f 65 79 65 73 5f 25 58 00 61 6e 69 62 63 6f 72 65 2e 62 69 6e 00 00 00 00 61 6e 69 62 69 63 2e 62 69 6e 00 00 61 6e 69 62 69 62 72 2e 62 69 6e 00 61 6e 69 62 69 73 63 72 2e 7a 6c 62 00 00 00 00 61 6e 69 62 69 74 72 61 2e 62 69 6e 00 00 00 00 61 6e 69 62 69 73 70 64 2e 62 69 6e 00 00 00 00 61 6e 69 62 69 62 61 6c 2e 62 69 6e 00 00 00 00`

## `BOOT.BIN` @ `0x4FB658`: `body_ingame_training`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x4FB608`: `body_core`
  - `0x4FB614`: `body_ingame_common`
  - `0x4FB628`: `body_ingame_betweenrounds`
  - `0x4FB644`: `body_ingame_scripts`
  - `0x4FB658`: `body_ingame_training`
  - `0x4FB670`: `body_ingame_speed`
  - `0x4FB684`: `body_ingame_balanced`
  - `0x4FB69C`: `body_ingame_power`
  - `0x4FB6B0`: `body_ingame_ali`
  - `0x4FB6C0`: `body_ingame_frazier`
- Surrounding 128 bytes: `5f 69 6e 67 61 6d 65 5f 63 6f 6d 6d 6f 6e 00 00 62 6f 64 79 5f 69 6e 67 61 6d 65 5f 62 65 74 77 65 65 6e 72 6f 75 6e 64 73 00 00 00 62 6f 64 79 5f 69 6e 67 61 6d 65 5f 73 63 72 69 70 74 73 00 62 6f 64 79 5f 69 6e 67 61 6d 65 5f 74 72 61 69 6e 69 6e 67 00 00 00 00 62 6f 64 79 5f 69 6e 67 61 6d 65 5f 73 70 65 65 64 00 00 00 62 6f 64 79 5f 69 6e 67 61 6d 65 5f 62 61 6c 61 6e 63 65 64`

## `BOOT.BIN` @ `0x504F10`: `fe_TrainingMeter`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x504ECC`: `fe_keyboard_Nav`
  - `0x504EDC`: `fe_keyboard_back`
  - `0x504EF0`: `fe_keyboard_Accept`
  - `0x504F04`: `fe_Chime`
  - `0x504F10`: `fe_TrainingMeter`
  - `0x504F24`: `fe_TimerBeep`
  - `0x504F34`: `fe_TrainingHeartBeat_Lp`
  - `0x504F4C`: `fe_Stamp_Vs`
  - `0x504F58`: `Global_Vol_Sfx`
  - `0x504F68`: `Global_Crowd_fade`
- Surrounding 128 bytes: `65 79 62 6f 61 72 64 5f 4e 61 76 00 66 65 5f 6b 65 79 62 6f 61 72 64 5f 62 61 63 6b 00 00 00 00 66 65 5f 6b 65 79 62 6f 61 72 64 5f 41 63 63 65 70 74 00 00 66 65 5f 43 68 69 6d 65 00 00 00 00 66 65 5f 54 72 61 69 6e 69 6e 67 4d 65 74 65 72 00 00 00 00 66 65 5f 54 69 6d 65 72 42 65 65 70 00 00 00 00 66 65 5f 54 72 61 69 6e 69 6e 67 48 65 61 72 74 42 65 61 74 5f 4c 70 00 66 65 5f 53`

## `BOOT.BIN` @ `0x504F34`: `fe_TrainingHeartBeat_Lp`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x504EF0`: `fe_keyboard_Accept`
  - `0x504F04`: `fe_Chime`
  - `0x504F10`: `fe_TrainingMeter`
  - `0x504F24`: `fe_TimerBeep`
  - `0x504F34`: `fe_TrainingHeartBeat_Lp`
  - `0x504F4C`: `fe_Stamp_Vs`
  - `0x504F58`: `Global_Vol_Sfx`
  - `0x504F68`: `Global_Crowd_fade`
  - `0x504F7C`: `Global_Pause`
  - `0x504F8C`: `CM_DuckerEvent`
- Surrounding 128 bytes: `65 79 62 6f 61 72 64 5f 41 63 63 65 70 74 00 00 66 65 5f 43 68 69 6d 65 00 00 00 00 66 65 5f 54 72 61 69 6e 69 6e 67 4d 65 74 65 72 00 00 00 00 66 65 5f 54 69 6d 65 72 42 65 65 70 00 00 00 00 66 65 5f 54 72 61 69 6e 69 6e 67 48 65 61 72 74 42 65 61 74 5f 4c 70 00 66 65 5f 53 74 61 6d 70 5f 56 73 00 47 6c 6f 62 61 6c 5f 56 6f 6c 5f 53 66 78 00 00 47 6c 6f 62 61 6c 5f 43 72 6f 77 64`

## `BOOT.BIN` @ `0x5056D0`: `EnvSfx_Training`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x505678`: `EnvSfx_Flu_LightBuzz`
  - `0x505690`: `EnvSfx_Flu_LightMove`
  - `0x5056A8`: `EnvSfx_Flu_Truck`
  - `0x5056BC`: `EnvSfx_Flu_Spark`
  - `0x5056D0`: `EnvSfx_Training`
  - `0x5056E0`: `EnvSfx_TrainMachine`
  - `0x5056F4`: `EnvSfx_TrainMachineRandom`
  - `0x505710`: `EnvSfx_ReplayCamera`
  - `0x505724`: `Envsfx_CameraFlash`
  - `0x505738`: `EntrSfx_Fireworks_Air`
- Surrounding 128 bytes: `45 6e 76 53 66 78 5f 46 6c 75 5f 4c 69 67 68 74 4d 6f 76 65 00 00 00 00 45 6e 76 53 66 78 5f 46 6c 75 5f 54 72 75 63 6b 00 00 00 00 45 6e 76 53 66 78 5f 46 6c 75 5f 53 70 61 72 6b 00 00 00 00 45 6e 76 53 66 78 5f 54 72 61 69 6e 69 6e 67 00 45 6e 76 53 66 78 5f 54 72 61 69 6e 4d 61 63 68 69 6e 65 00 45 6e 76 53 66 78 5f 54 72 61 69 6e 4d 61 63 68 69 6e 65 52 61 6e 64 6f 6d 00 00 00`

## `BOOT.BIN` @ `0x505BCC`: `MenuSfx_MoneyCount_Lp`
- Matched term(s): `money`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x505B88`: `Replaymenu_ZoomOut`
  - `0x505B9C`: `MenuSfx_TCCBeep`
  - `0x505BAC`: `UnconnectedClass`
  - `0x505BC0`: `MenuSfx_PSP`
  - `0x505BCC`: `MenuSfx_MoneyCount_Lp`
  - `0x505BE4`: `Intro_Music_PSP`
  - `0x505BF4`: `C_AngryVolume`
  - `0x505C04`: `C_BooVolume`
  - `0x505C10`: `C_ChantVolume`
  - `0x505C20`: `C_StrmVolume`
- Surrounding 128 bytes: `61 79 6d 65 6e 75 5f 5a 6f 6f 6d 4f 75 74 00 00 4d 65 6e 75 53 66 78 5f 54 43 43 42 65 65 70 00 55 6e 63 6f 6e 6e 65 63 74 65 64 43 6c 61 73 73 00 00 00 00 4d 65 6e 75 53 66 78 5f 50 53 50 00 4d 65 6e 75 53 66 78 5f 4d 6f 6e 65 79 43 6f 75 6e 74 5f 4c 70 00 00 00 49 6e 74 72 6f 5f 4d 75 73 69 63 5f 50 53 50 00 43 5f 41 6e 67 72 79 56 6f 6c 75 6d 65 00 00 00 43 5f 42 6f 6f 56 6f 6c`

## `BOOT.BIN` @ `0x505EC0`: `audio/BEAudio.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x505E18`: `send_master_EntFX_WetDry`
  - `0x505E34`: `Global`
  - `0x505E40`: `AuController::Init() -- Out of Memory creating soundlibbuffer ! `
  - `0x505E84`: `AuController::InitAudio() -- Snd::System::Init() FAILED ! `
  - `0x505EC0`: `audio/BEAudio.viv`
  - `0x505ED4`: `LS%02ddodge.bnk`
  - `0x505EE8`: `Atmosphere_LLp.bnk`
  - `0x505EFC`: `Brasco_LLp.bnk`
  - `0x505F0C`: `Consequence_LLp.bnk`
  - `0x505F20`: `DilatedPeoples_LLp.bnk`
- Surrounding 128 bytes: `0a 00 00 00 41 75 43 6f 6e 74 72 6f 6c 6c 65 72 3a 3a 49 6e 69 74 41 75 64 69 6f 28 29 20 2d 2d 20 53 6e 64 3a 3a 53 79 73 74 65 6d 3a 3a 49 6e 69 74 28 29 20 46 41 49 4c 45 44 20 21 20 0a 00 61 75 64 69 6f 2f 42 45 41 75 64 69 6f 2e 76 69 76 00 00 00 4c 53 25 30 32 64 64 6f 64 67 65 2e 62 6e 6b 00 2f 00 00 00 41 74 6d 6f 73 70 68 65 72 65 5f 4c 4c 70 2e 62 6e 6b 00 00 42 72 61 73`

## `BOOT.BIN` @ `0x506868`: `coreaems.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x5067D8`: `AuAemsManager::Init() -- Failed AEM Bank Load! `
  - `0x50680C`: `AuAemsManager::Init() -- Failed SNDAEMS_addmodulebank! `
  - `0x50684C`: `fe_sfx.abk`
  - `0x506858`: `out of memory`
  - `0x506868`: `coreaems.viv`
  - `0x506878`: `cctrl.abk`
  - `0x506884`: `pmenu.abk`
  - `0x506890`: `steps.abk`
  - `0x50689C`: `bell.abk`
  - `0x5068A8`: `GSfx.abk`
- Surrounding 128 bytes: `6c 65 64 20 53 4e 44 41 45 4d 53 5f 61 64 64 6d 6f 64 75 6c 65 62 61 6e 6b 21 20 0a 00 00 00 00 2f 00 00 00 66 65 5f 73 66 78 2e 61 62 6b 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 63 6f 72 65 61 65 6d 73 2e 76 69 76 00 00 00 00 63 63 74 72 6c 2e 61 62 6b 00 00 00 70 6d 65 6e 75 2e 61 62 6b 00 00 00 73 74 65 70 73 2e 61 62 6b 00 00 00 62 65 6c 6c 2e 61 62 6b 00 00 00 00`

## `BOOT.BIN` @ `0x506998`: `chants.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x506968`: `csakost.abk`
  - `0x506974`: `cminist.abk`
  - `0x506980`: `clarge.abk`
  - `0x50698C`: `clst.abk`
  - `0x506998`: `chants.viv`
  - `0x5069A4`: `chant_PSP_CaB%03d.abk`
  - `0x5069BC`: `chant_PSP_Lic%03d.abk`
  - `0x5069D4`: `Chant_PSP_Gen%03d.abk`
  - `0x5069EC`: `Gsmall.abk`
  - `0x5069F8`: `Gmed.abk`
- Surrounding 128 bytes: `00 00 00 00 63 65 6c 65 73 74 2e 61 62 6b 00 00 63 73 61 6b 6f 73 74 2e 61 62 6b 00 63 6d 69 6e 69 73 74 2e 61 62 6b 00 63 6c 61 72 67 65 2e 61 62 6b 00 00 63 6c 73 74 2e 61 62 6b 00 00 00 00 63 68 61 6e 74 73 2e 76 69 76 00 00 63 68 61 6e 74 5f 50 53 50 5f 43 61 42 25 30 33 64 2e 61 62 6b 00 00 00 63 68 61 6e 74 5f 50 53 50 5f 4c 69 63 25 30 33 64 2e 61 62 6b 00 00 00 43 68 61 6e`

## `BOOT.BIN` @ `0x506C3C`: `trndat.big`
- Matched term(s): `big`
- Assessment: **meaningful**
- Why it matters: BIG archive/file-loader string; xrefs can identify archive/resource mounting code.
- Nearby printable strings:
  - `0x506BC8`: `AuSpeechManager::InitStream() -- Out of Memory creating stream_buffer ! `
  - `0x506C14`: `out of memory`
  - `0x506C24`: `_Clone`
  - `0x506C2C`: `.dat`
  - `0x506C3C`: `trndat.big`
  - `0x506C48`: `trnevt.evt`
  - `0x506C54`: `trnhdr.big`
  - `0x506C60`: `ancdat.big`
  - `0x506C6C`: `ancevt.evt`
  - `0x506C78`: `anchdr.big`
- Surrounding 128 bytes: `69 6e 67 20 73 74 72 65 61 6d 5f 62 75 66 66 65 72 20 21 20 0a 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 5f 43 6c 6f 6e 65 00 00 2e 64 61 74 00 00 00 00 30 30 31 00 2f 00 00 00 74 72 6e 64 61 74 2e 62 69 67 00 00 74 72 6e 65 76 74 2e 65 76 74 00 00 74 72 6e 68 64 72 2e 62 69 67 00 00 61 6e 63 64 61 74 2e 62 69 67 00 00 61 6e 63 65 76 74 2e 65 76 74 00 00 61 6e 63 68`

## `BOOT.BIN` @ `0x506C54`: `trnhdr.big`
- Matched term(s): `big`
- Assessment: **meaningful**
- Why it matters: BIG archive/file-loader string; xrefs can identify archive/resource mounting code.
- Nearby printable strings:
  - `0x506C24`: `_Clone`
  - `0x506C2C`: `.dat`
  - `0x506C3C`: `trndat.big`
  - `0x506C48`: `trnevt.evt`
  - `0x506C54`: `trnhdr.big`
  - `0x506C60`: `ancdat.big`
  - `0x506C6C`: `ancevt.evt`
  - `0x506C78`: `anchdr.big`
  - `0x506C84`: `comdat.big`
  - `0x506C90`: `comevt.evt`
- Surrounding 128 bytes: `6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 5f 43 6c 6f 6e 65 00 00 2e 64 61 74 00 00 00 00 30 30 31 00 2f 00 00 00 74 72 6e 64 61 74 2e 62 69 67 00 00 74 72 6e 65 76 74 2e 65 76 74 00 00 74 72 6e 68 64 72 2e 62 69 67 00 00 61 6e 63 64 61 74 2e 62 69 67 00 00 61 6e 63 65 76 74 2e 65 76 74 00 00 61 6e 63 68 64 72 2e 62 69 67 00 00 63 6f 6d 64 61 74 2e 62 69 67 00 00 63 6f 6d 65`

## `BOOT.BIN` @ `0x506C60`: `ancdat.big`
- Matched term(s): `big`
- Assessment: **meaningful**
- Why it matters: BIG archive/file-loader string; xrefs can identify archive/resource mounting code.
- Nearby printable strings:
  - `0x506C2C`: `.dat`
  - `0x506C3C`: `trndat.big`
  - `0x506C48`: `trnevt.evt`
  - `0x506C54`: `trnhdr.big`
  - `0x506C60`: `ancdat.big`
  - `0x506C6C`: `ancevt.evt`
  - `0x506C78`: `anchdr.big`
  - `0x506C84`: `comdat.big`
  - `0x506C90`: `comevt.evt`
  - `0x506C9C`: `comhdr.big`
- Surrounding 128 bytes: `79 0a 00 00 5f 43 6c 6f 6e 65 00 00 2e 64 61 74 00 00 00 00 30 30 31 00 2f 00 00 00 74 72 6e 64 61 74 2e 62 69 67 00 00 74 72 6e 65 76 74 2e 65 76 74 00 00 74 72 6e 68 64 72 2e 62 69 67 00 00 61 6e 63 64 61 74 2e 62 69 67 00 00 61 6e 63 65 76 74 2e 65 76 74 00 00 61 6e 63 68 64 72 2e 62 69 67 00 00 63 6f 6d 64 61 74 2e 62 69 67 00 00 63 6f 6d 65 76 74 2e 65 76 74 00 00 63 6f 6d 68`

## `BOOT.BIN` @ `0x506C78`: `anchdr.big`
- Matched term(s): `big`
- Assessment: **meaningful**
- Why it matters: BIG archive/file-loader string; xrefs can identify archive/resource mounting code.
- Nearby printable strings:
  - `0x506C48`: `trnevt.evt`
  - `0x506C54`: `trnhdr.big`
  - `0x506C60`: `ancdat.big`
  - `0x506C6C`: `ancevt.evt`
  - `0x506C78`: `anchdr.big`
  - `0x506C84`: `comdat.big`
  - `0x506C90`: `comevt.evt`
  - `0x506C9C`: `comhdr.big`
  - `0x506CA8`: `refcount.bnk`
  - `0x506CBC`: `SUBTITLE ID = %d`
- Surrounding 128 bytes: `2f 00 00 00 74 72 6e 64 61 74 2e 62 69 67 00 00 74 72 6e 65 76 74 2e 65 76 74 00 00 74 72 6e 68 64 72 2e 62 69 67 00 00 61 6e 63 64 61 74 2e 62 69 67 00 00 61 6e 63 65 76 74 2e 65 76 74 00 00 61 6e 63 68 64 72 2e 62 69 67 00 00 63 6f 6d 64 61 74 2e 62 69 67 00 00 63 6f 6d 65 76 74 2e 65 76 74 00 00 63 6f 6d 68 64 72 2e 62 69 67 00 00 72 65 66 63 6f 75 6e 74 2e 62 6e 6b 00 00 00 00`

## `BOOT.BIN` @ `0x506C84`: `comdat.big`
- Matched term(s): `big`
- Assessment: **meaningful**
- Why it matters: BIG archive/file-loader string; xrefs can identify archive/resource mounting code.
- Nearby printable strings:
  - `0x506C54`: `trnhdr.big`
  - `0x506C60`: `ancdat.big`
  - `0x506C6C`: `ancevt.evt`
  - `0x506C78`: `anchdr.big`
  - `0x506C84`: `comdat.big`
  - `0x506C90`: `comevt.evt`
  - `0x506C9C`: `comhdr.big`
  - `0x506CA8`: `refcount.bnk`
  - `0x506CBC`: `SUBTITLE ID = %d`
  - `0x506CD0`: `TCC = MULTI KD`
- Surrounding 128 bytes: `69 67 00 00 74 72 6e 65 76 74 2e 65 76 74 00 00 74 72 6e 68 64 72 2e 62 69 67 00 00 61 6e 63 64 61 74 2e 62 69 67 00 00 61 6e 63 65 76 74 2e 65 76 74 00 00 61 6e 63 68 64 72 2e 62 69 67 00 00 63 6f 6d 64 61 74 2e 62 69 67 00 00 63 6f 6d 65 76 74 2e 65 76 74 00 00 63 6f 6d 68 64 72 2e 62 69 67 00 00 72 65 66 63 6f 75 6e 74 2e 62 6e 6b 00 00 00 00 00 00 00 00 53 55 42 54 49 54 4c 45`

## `BOOT.BIN` @ `0x506C9C`: `comhdr.big`
- Matched term(s): `big`
- Assessment: **meaningful**
- Why it matters: BIG archive/file-loader string; xrefs can identify archive/resource mounting code.
- Nearby printable strings:
  - `0x506C6C`: `ancevt.evt`
  - `0x506C78`: `anchdr.big`
  - `0x506C84`: `comdat.big`
  - `0x506C90`: `comevt.evt`
  - `0x506C9C`: `comhdr.big`
  - `0x506CA8`: `refcount.bnk`
  - `0x506CBC`: `SUBTITLE ID = %d`
  - `0x506CD0`: `TCC = MULTI KD`
  - `0x506CE0`: `TCC = POOR PERFORMANCE`
  - `0x506CF8`: `TCC = WASTED ENERGY`
- Surrounding 128 bytes: `69 67 00 00 61 6e 63 64 61 74 2e 62 69 67 00 00 61 6e 63 65 76 74 2e 65 76 74 00 00 61 6e 63 68 64 72 2e 62 69 67 00 00 63 6f 6d 64 61 74 2e 62 69 67 00 00 63 6f 6d 65 76 74 2e 65 76 74 00 00 63 6f 6d 68 64 72 2e 62 69 67 00 00 72 65 66 63 6f 75 6e 74 2e 62 6e 6b 00 00 00 00 00 00 00 00 53 55 42 54 49 54 4c 45 20 49 44 20 3d 20 25 64 00 00 00 00 54 43 43 20 3d 20 4d 55 4c 54 49 20`

## `BOOT.BIN` @ `0x506D0C`: `TCC = BOXER DAMAGE`
- Matched term(s): `damage`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x506CBC`: `SUBTITLE ID = %d`
  - `0x506CD0`: `TCC = MULTI KD`
  - `0x506CE0`: `TCC = POOR PERFORMANCE`
  - `0x506CF8`: `TCC = WASTED ENERGY`
  - `0x506D0C`: `TCC = BOXER DAMAGE`
  - `0x506D20`: `TCC = BOXER RATING/STYLE`
  - `0x507308`: `TGIntro`
  - `0x507310`: `TGProgressUpdate`
  - `0x507324`: `TGSummary`
  - `0x507330`: `TGCount`
- Surrounding 128 bytes: `00 00 00 00 54 43 43 20 3d 20 4d 55 4c 54 49 20 4b 44 00 00 54 43 43 20 3d 20 50 4f 4f 52 20 50 45 52 46 4f 52 4d 41 4e 43 45 00 00 54 43 43 20 3d 20 57 41 53 54 45 44 20 45 4e 45 52 47 59 00 54 43 43 20 3d 20 42 4f 58 45 52 20 44 41 4d 41 47 45 00 00 54 43 43 20 3d 20 42 4f 58 45 52 20 52 41 54 49 4e 47 2f 53 54 59 4c 45 00 00 00 00 00 00 00 00 54 75 13 00 54 75 13 00 6c 75 13 00`

## `BOOT.BIN` @ `0x5073A0`: `BoxerDamage`
- Matched term(s): `damage`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x507368`: `StartOfRound`
  - `0x507378`: `RefClinch`
  - `0x507384`: `RefStoppage`
  - `0x507390`: `BlockedPunch`
  - `0x5073A0`: `BoxerDamage`
  - `0x5073AC`: `CelebrationSequence`
  - `0x5073C0`: `LackOfAction`
  - `0x5073D0`: `MissedPunch`
  - `0x5073DC`: `PunchCombos`
  - `0x5073E8`: `PunchLanded`
- Surrounding 128 bytes: `00 00 00 00 54 43 43 00 53 74 61 72 74 4f 66 52 6f 75 6e 64 00 00 00 00 52 65 66 43 6c 69 6e 63 68 00 00 00 52 65 66 53 74 6f 70 70 61 67 65 00 42 6c 6f 63 6b 65 64 50 75 6e 63 68 00 00 00 00 42 6f 78 65 72 44 61 6d 61 67 65 00 43 65 6c 65 62 72 61 74 69 6f 6e 53 65 71 75 65 6e 63 65 00 4c 61 63 6b 4f 66 41 63 74 69 6f 6e 00 00 00 00 4d 69 73 73 65 64 50 75 6e 63 68 00 50 75 6e 63`

## `BOOT.BIN` @ `0x507468`: `CareerMode`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50742C`: `FeintingResult`
  - `0x50743C`: `ClinchingResult`
  - `0x50744C`: `Trapped`
  - `0x507454`: `BoxerRoundHistory`
  - `0x507468`: `CareerMode`
  - `0x507474`: `Knockdown`
  - `0x507480`: `IllegalBlows`
  - `0x507490`: `RAFightIntroFlyIn`
  - `0x5074A4`: `RAFightIntroSegment4`
  - `0x5074BC`: `RAFightIntroSegment5`
- Surrounding 128 bytes: `6c 74 00 00 46 65 69 6e 74 69 6e 67 52 65 73 75 6c 74 00 00 43 6c 69 6e 63 68 69 6e 67 52 65 73 75 6c 74 00 54 72 61 70 70 65 64 00 42 6f 78 65 72 52 6f 75 6e 64 48 69 73 74 6f 72 79 00 00 00 43 61 72 65 65 72 4d 6f 64 65 00 00 4b 6e 6f 63 6b 64 6f 77 6e 00 00 00 49 6c 6c 65 67 61 6c 42 6c 6f 77 73 00 00 00 00 52 41 46 69 67 68 74 49 6e 74 72 6f 46 6c 79 49 6e 00 00 00 52 41 46 69`

## `BOOT.BIN` @ `0x5086D4`: `contracts.viv`
- Matched term(s): `contracts`, `contracts.viv`, `viv`, `contract`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x5080D4`: `T_pop_39`
  - `0x5080E4`: `T_pop_80`
  - `0x5080F0`: `INFO_Awards_16`
  - `0x508100`: `INFO_Awards_15`
  - `0x5086D4`: `contracts.viv`
  - `0x5086E8`: `cutman.fnc`
  - `0x5086F8`: `ST_Date_%d`
  - `0x508738`: `basic_string`
  - `0x508748`: `out of memory`
  - `0x508788`: `INFO_Type_7`
- Surrounding 128 bytes: `14 c1 19 00 14 c1 19 00 14 c1 19 00 10 c1 19 00 10 c1 19 00 14 c1 19 00 14 c1 19 00 14 c1 19 00 10 c1 19 00 10 c1 19 00 14 c1 19 00 14 c1 19 00 10 c1 19 00 10 c1 19 00 00 00 00 00 2f 00 00 00 63 6f 6e 74 72 61 63 74 73 2e 76 69 76 00 00 00 00 00 00 00 63 75 74 6d 61 6e 2e 66 6e 63 00 00 00 00 00 00 53 54 5f 44 61 74 65 5f 25 64 00 00 00 00 00 00 20 0f 1a 00 38 0f 1a 00 18 0f 1a 00`

## `BOOT.BIN` @ `0x5086E8`: `cutman.fnc`
- Matched term(s): `cutman`, `fnc`, `cut`
- Assessment: **meaningful**
- Why it matters: Named contract/function script; xrefs should lead to contract/career script loading.
- Nearby printable strings:
  - `0x5080E4`: `T_pop_80`
  - `0x5080F0`: `INFO_Awards_16`
  - `0x508100`: `INFO_Awards_15`
  - `0x5086D4`: `contracts.viv`
  - `0x5086E8`: `cutman.fnc`
  - `0x5086F8`: `ST_Date_%d`
  - `0x508738`: `basic_string`
  - `0x508748`: `out of memory`
  - `0x508788`: `INFO_Type_7`
  - `0x508794`: `INFO_Type_30`
- Surrounding 128 bytes: `14 c1 19 00 14 c1 19 00 14 c1 19 00 10 c1 19 00 10 c1 19 00 14 c1 19 00 14 c1 19 00 10 c1 19 00 10 c1 19 00 00 00 00 00 2f 00 00 00 63 6f 6e 74 72 61 63 74 73 2e 76 69 76 00 00 00 00 00 00 00 63 75 74 6d 61 6e 2e 66 6e 63 00 00 00 00 00 00 53 54 5f 44 61 74 65 5f 25 64 00 00 00 00 00 00 20 0f 1a 00 38 0f 1a 00 18 0f 1a 00 38 0f 1a 00 18 0f 1a 00 38 0f 1a 00 38 0f 1a 00 18 0f 1a 00`

## `BOOT.BIN` @ `0x50882C`: `fights.fnc`
- Matched term(s): `fights`, `fnc`
- Assessment: **meaningful**
- Why it matters: Named contract/function script; xrefs should lead to contract/career script loading.
- Nearby printable strings:
  - `0x5087FC`: `T_pop_53`
  - `0x50880C`: `O_Ok`
  - `0x508814`: `T_pop_48`
  - `0x508820`: `T_pop_49`
  - `0x50882C`: `fights.fnc`
  - `0x508838`: `INFO_Type_5`
  - `0x508844`: `INFO_Type_3`
  - `0x508850`: `INFO_Type_20`
  - `0x508860`: `INFO_Type_21`
  - `0x508870`: `INFO_Type_22`
- Surrounding 128 bytes: `49 4e 46 4f 5f 4c 65 6e 67 74 68 00 5f 25 64 00 54 5f 70 6f 70 5f 35 33 00 00 00 00 31 00 00 00 4f 5f 4f 6b 00 00 00 00 54 5f 70 6f 70 5f 34 38 00 00 00 00 54 5f 70 6f 70 5f 34 39 00 00 00 00 66 69 67 68 74 73 2e 66 6e 63 00 00 49 4e 46 4f 5f 54 79 70 65 5f 35 00 49 4e 46 4f 5f 54 79 70 65 5f 33 00 49 4e 46 4f 5f 54 79 70 65 5f 32 30 00 00 00 00 49 4e 46 4f 5f 54 79 70 65 5f 32 31`

## `BOOT.BIN` @ `0x508E54`: `TL_Most_Career_Earnings`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x508E1C`: `TL_Top_10`
  - `0x508E28`: `TL_Most_Wins`
  - `0x508E38`: `TL_Most_KOs`
  - `0x508E44`: `TL_Fastest_KOs`
  - `0x508E54`: `TL_Most_Career_Earnings`
  - `0x508E6C`: `T_pop_43`
  - `0x508E7C`: `O_Ok`
  - `0x508E88`: `out of memory`
  - `0x508E98`: `common.txt`
  - `0x508EA8`: `GERMAN.loc`
- Surrounding 128 bytes: `79 0a 00 00 25 73 00 00 54 4c 5f 54 6f 70 5f 31 30 00 00 00 54 4c 5f 4d 6f 73 74 5f 57 69 6e 73 00 00 00 00 54 4c 5f 4d 6f 73 74 5f 4b 4f 73 00 54 4c 5f 46 61 73 74 65 73 74 5f 4b 4f 73 00 00 54 4c 5f 4d 6f 73 74 5f 43 61 72 65 65 72 5f 45 61 72 6e 69 6e 67 73 00 54 5f 70 6f 70 5f 34 33 00 00 00 00 31 00 00 00 4f 5f 4f 6b 00 00 00 00 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72`

## `BOOT.BIN` @ `0x5091FC`: `db.viv`
- Matched term(s): `db.viv`, `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x508FC8`: `basic_string`
  - `0x508FD8`: `out of memory`
  - `0x508FF8`: `xloc_gm.`
  - `0x509004`: `xloc_fe.`
  - `0x5091FC`: `db.viv`
  - `0x509204`: `xdbboxr.adf`
  - `0x509210`: `xdbvenue.adf`
  - `0x509220`: `xdbalias.adf`
  - `0x509230`: `xdbevent.adf`
  - `0x509240`: `xdbhmtwn.adf`
- Surrounding 128 bytes: `58 a2 1a 00 dc a3 1a 00 6c a4 1a 00 fc a4 1a 00 9c a5 1a 00 58 a2 1a 00 00 00 00 00 dc a9 1a 00 1c aa 1a 00 1c aa 1a 00 1c aa 1a 00 dc a9 1a 00 1c aa 1a 00 e4 a9 1a 00 00 00 00 00 2f 00 00 00 64 62 2e 76 69 76 00 00 78 64 62 62 6f 78 72 2e 61 64 66 00 78 64 62 76 65 6e 75 65 2e 61 64 66 00 00 00 00 78 64 62 61 6c 69 61 73 2e 61 64 66 00 00 00 00 78 64 62 65 76 65 6e 74 2e 61 64 66`

## `BOOT.BIN` @ `0x509204`: `xdbboxr.adf`
- Matched term(s): `xdbboxr`, `adf`
- Assessment: **meaningful**
- Why it matters: Named database/table member; xrefs should lead to database table open/lookup code.
- Nearby printable strings:
  - `0x508FD8`: `out of memory`
  - `0x508FF8`: `xloc_gm.`
  - `0x509004`: `xloc_fe.`
  - `0x5091FC`: `db.viv`
  - `0x509204`: `xdbboxr.adf`
  - `0x509210`: `xdbvenue.adf`
  - `0x509220`: `xdbalias.adf`
  - `0x509230`: `xdbevent.adf`
  - `0x509240`: `xdbhmtwn.adf`
  - `0x509250`: `xdbstore.adf`
- Surrounding 128 bytes: `6c a4 1a 00 fc a4 1a 00 9c a5 1a 00 58 a2 1a 00 00 00 00 00 dc a9 1a 00 1c aa 1a 00 1c aa 1a 00 1c aa 1a 00 dc a9 1a 00 1c aa 1a 00 e4 a9 1a 00 00 00 00 00 2f 00 00 00 64 62 2e 76 69 76 00 00 78 64 62 62 6f 78 72 2e 61 64 66 00 78 64 62 76 65 6e 75 65 2e 61 64 66 00 00 00 00 78 64 62 61 6c 69 61 73 2e 61 64 66 00 00 00 00 78 64 62 65 76 65 6e 74 2e 61 64 66 00 00 00 00 78 64 62 68`

## `BOOT.BIN` @ `0x509210`: `xdbvenue.adf`
- Matched term(s): `xdbvenue`, `adf`, `venue`
- Assessment: **meaningful**
- Why it matters: Named database/table member; xrefs should lead to database table open/lookup code.
- Nearby printable strings:
  - `0x508FF8`: `xloc_gm.`
  - `0x509004`: `xloc_fe.`
  - `0x5091FC`: `db.viv`
  - `0x509204`: `xdbboxr.adf`
  - `0x509210`: `xdbvenue.adf`
  - `0x509220`: `xdbalias.adf`
  - `0x509230`: `xdbevent.adf`
  - `0x509240`: `xdbhmtwn.adf`
  - `0x509250`: `xdbstore.adf`
  - `0x509260`: `xdbpref.adf`
- Surrounding 128 bytes: `58 a2 1a 00 00 00 00 00 dc a9 1a 00 1c aa 1a 00 1c aa 1a 00 1c aa 1a 00 dc a9 1a 00 1c aa 1a 00 e4 a9 1a 00 00 00 00 00 2f 00 00 00 64 62 2e 76 69 76 00 00 78 64 62 62 6f 78 72 2e 61 64 66 00 78 64 62 76 65 6e 75 65 2e 61 64 66 00 00 00 00 78 64 62 61 6c 69 61 73 2e 61 64 66 00 00 00 00 78 64 62 65 76 65 6e 74 2e 61 64 66 00 00 00 00 78 64 62 68 6d 74 77 6e 2e 61 64 66 00 00 00 00`

## `BOOT.BIN` @ `0x509220`: `xdbalias.adf`
- Matched term(s): `xdbalias`, `adf`
- Assessment: **meaningful**
- Why it matters: Named database/table member; xrefs should lead to database table open/lookup code.
- Nearby printable strings:
  - `0x509004`: `xloc_fe.`
  - `0x5091FC`: `db.viv`
  - `0x509204`: `xdbboxr.adf`
  - `0x509210`: `xdbvenue.adf`
  - `0x509220`: `xdbalias.adf`
  - `0x509230`: `xdbevent.adf`
  - `0x509240`: `xdbhmtwn.adf`
  - `0x509250`: `xdbstore.adf`
  - `0x509260`: `xdbpref.adf`
  - `0x50926C`: `xdbrivl.adf`
- Surrounding 128 bytes: `1c aa 1a 00 1c aa 1a 00 dc a9 1a 00 1c aa 1a 00 e4 a9 1a 00 00 00 00 00 2f 00 00 00 64 62 2e 76 69 76 00 00 78 64 62 62 6f 78 72 2e 61 64 66 00 78 64 62 76 65 6e 75 65 2e 61 64 66 00 00 00 00 78 64 62 61 6c 69 61 73 2e 61 64 66 00 00 00 00 78 64 62 65 76 65 6e 74 2e 61 64 66 00 00 00 00 78 64 62 68 6d 74 77 6e 2e 61 64 66 00 00 00 00 78 64 62 73 74 6f 72 65 2e 61 64 66 00 00 00 00`

## `BOOT.BIN` @ `0x509230`: `xdbevent.adf`
- Matched term(s): `adf`
- Assessment: **meaningful**
- Why it matters: Named database/table member; xrefs should lead to database table open/lookup code.
- Nearby printable strings:
  - `0x5091FC`: `db.viv`
  - `0x509204`: `xdbboxr.adf`
  - `0x509210`: `xdbvenue.adf`
  - `0x509220`: `xdbalias.adf`
  - `0x509230`: `xdbevent.adf`
  - `0x509240`: `xdbhmtwn.adf`
  - `0x509250`: `xdbstore.adf`
  - `0x509260`: `xdbpref.adf`
  - `0x50926C`: `xdbrivl.adf`
  - `0x509278`: `xdbtrain.adf`
- Surrounding 128 bytes: `e4 a9 1a 00 00 00 00 00 2f 00 00 00 64 62 2e 76 69 76 00 00 78 64 62 62 6f 78 72 2e 61 64 66 00 78 64 62 76 65 6e 75 65 2e 61 64 66 00 00 00 00 78 64 62 61 6c 69 61 73 2e 61 64 66 00 00 00 00 78 64 62 65 76 65 6e 74 2e 61 64 66 00 00 00 00 78 64 62 68 6d 74 77 6e 2e 61 64 66 00 00 00 00 78 64 62 73 74 6f 72 65 2e 61 64 66 00 00 00 00 78 64 62 70 72 65 66 2e 61 64 66 00 78 64 62 72`

## `BOOT.BIN` @ `0x509240`: `xdbhmtwn.adf`
- Matched term(s): `adf`
- Assessment: **meaningful**
- Why it matters: Named database/table member; xrefs should lead to database table open/lookup code.
- Nearby printable strings:
  - `0x509204`: `xdbboxr.adf`
  - `0x509210`: `xdbvenue.adf`
  - `0x509220`: `xdbalias.adf`
  - `0x509230`: `xdbevent.adf`
  - `0x509240`: `xdbhmtwn.adf`
  - `0x509250`: `xdbstore.adf`
  - `0x509260`: `xdbpref.adf`
  - `0x50926C`: `xdbrivl.adf`
  - `0x509278`: `xdbtrain.adf`
  - `0x509288`: `xdbcutpn.adf`
- Surrounding 128 bytes: `69 76 00 00 78 64 62 62 6f 78 72 2e 61 64 66 00 78 64 62 76 65 6e 75 65 2e 61 64 66 00 00 00 00 78 64 62 61 6c 69 61 73 2e 61 64 66 00 00 00 00 78 64 62 65 76 65 6e 74 2e 61 64 66 00 00 00 00 78 64 62 68 6d 74 77 6e 2e 61 64 66 00 00 00 00 78 64 62 73 74 6f 72 65 2e 61 64 66 00 00 00 00 78 64 62 70 72 65 66 2e 61 64 66 00 78 64 62 72 69 76 6c 2e 61 64 66 00 78 64 62 74 72 61 69 6e`

## `BOOT.BIN` @ `0x509250`: `xdbstore.adf`
- Matched term(s): `xdbstore`, `adf`
- Assessment: **meaningful**
- Why it matters: Named database/table member; xrefs should lead to database table open/lookup code.
- Nearby printable strings:
  - `0x509210`: `xdbvenue.adf`
  - `0x509220`: `xdbalias.adf`
  - `0x509230`: `xdbevent.adf`
  - `0x509240`: `xdbhmtwn.adf`
  - `0x509250`: `xdbstore.adf`
  - `0x509260`: `xdbpref.adf`
  - `0x50926C`: `xdbrivl.adf`
  - `0x509278`: `xdbtrain.adf`
  - `0x509288`: `xdbcutpn.adf`
  - `0x509298`: `T_Up_Next_%d`
- Surrounding 128 bytes: `78 64 62 76 65 6e 75 65 2e 61 64 66 00 00 00 00 78 64 62 61 6c 69 61 73 2e 61 64 66 00 00 00 00 78 64 62 65 76 65 6e 74 2e 61 64 66 00 00 00 00 78 64 62 68 6d 74 77 6e 2e 61 64 66 00 00 00 00 78 64 62 73 74 6f 72 65 2e 61 64 66 00 00 00 00 78 64 62 70 72 65 66 2e 61 64 66 00 78 64 62 72 69 76 6c 2e 61 64 66 00 78 64 62 74 72 61 69 6e 2e 61 64 66 00 00 00 00 78 64 62 63 75 74 70 6e`

## `BOOT.BIN` @ `0x509260`: `xdbpref.adf`
- Matched term(s): `adf`
- Assessment: **meaningful**
- Why it matters: Named database/table member; xrefs should lead to database table open/lookup code.
- Nearby printable strings:
  - `0x509220`: `xdbalias.adf`
  - `0x509230`: `xdbevent.adf`
  - `0x509240`: `xdbhmtwn.adf`
  - `0x509250`: `xdbstore.adf`
  - `0x509260`: `xdbpref.adf`
  - `0x50926C`: `xdbrivl.adf`
  - `0x509278`: `xdbtrain.adf`
  - `0x509288`: `xdbcutpn.adf`
  - `0x509298`: `T_Up_Next_%d`
  - `0x5092A8`: `RC_%d`
- Surrounding 128 bytes: `78 64 62 61 6c 69 61 73 2e 61 64 66 00 00 00 00 78 64 62 65 76 65 6e 74 2e 61 64 66 00 00 00 00 78 64 62 68 6d 74 77 6e 2e 61 64 66 00 00 00 00 78 64 62 73 74 6f 72 65 2e 61 64 66 00 00 00 00 78 64 62 70 72 65 66 2e 61 64 66 00 78 64 62 72 69 76 6c 2e 61 64 66 00 78 64 62 74 72 61 69 6e 2e 61 64 66 00 00 00 00 78 64 62 63 75 74 70 6e 2e 61 64 66 00 00 00 00 54 5f 55 70 5f 4e 65 78`

## `BOOT.BIN` @ `0x50926C`: `xdbrivl.adf`
- Matched term(s): `xdbrivl`, `adf`
- Assessment: **meaningful**
- Why it matters: Named database/table member; xrefs should lead to database table open/lookup code.
- Nearby printable strings:
  - `0x509230`: `xdbevent.adf`
  - `0x509240`: `xdbhmtwn.adf`
  - `0x509250`: `xdbstore.adf`
  - `0x509260`: `xdbpref.adf`
  - `0x50926C`: `xdbrivl.adf`
  - `0x509278`: `xdbtrain.adf`
  - `0x509288`: `xdbcutpn.adf`
  - `0x509298`: `T_Up_Next_%d`
  - `0x5092A8`: `RC_%d`
  - `0x5092B0`: `INFO_RC_%d`
- Surrounding 128 bytes: `00 00 00 00 78 64 62 65 76 65 6e 74 2e 61 64 66 00 00 00 00 78 64 62 68 6d 74 77 6e 2e 61 64 66 00 00 00 00 78 64 62 73 74 6f 72 65 2e 61 64 66 00 00 00 00 78 64 62 70 72 65 66 2e 61 64 66 00 78 64 62 72 69 76 6c 2e 61 64 66 00 78 64 62 74 72 61 69 6e 2e 61 64 66 00 00 00 00 78 64 62 63 75 74 70 6e 2e 61 64 66 00 00 00 00 54 5f 55 70 5f 4e 65 78 74 5f 25 64 00 00 00 00 52 43 5f 25`

## `BOOT.BIN` @ `0x509278`: `xdbtrain.adf`
- Matched term(s): `xdbtrain`, `adf`, `AI`
- Assessment: **meaningful**
- Why it matters: Named database/table member; xrefs should lead to database table open/lookup code.
- Nearby printable strings:
  - `0x509240`: `xdbhmtwn.adf`
  - `0x509250`: `xdbstore.adf`
  - `0x509260`: `xdbpref.adf`
  - `0x50926C`: `xdbrivl.adf`
  - `0x509278`: `xdbtrain.adf`
  - `0x509288`: `xdbcutpn.adf`
  - `0x509298`: `T_Up_Next_%d`
  - `0x5092A8`: `RC_%d`
  - `0x5092B0`: `INFO_RC_%d`
  - `0x5092BC`: `SUM_%d`
- Surrounding 128 bytes: `2e 61 64 66 00 00 00 00 78 64 62 68 6d 74 77 6e 2e 61 64 66 00 00 00 00 78 64 62 73 74 6f 72 65 2e 61 64 66 00 00 00 00 78 64 62 70 72 65 66 2e 61 64 66 00 78 64 62 72 69 76 6c 2e 61 64 66 00 78 64 62 74 72 61 69 6e 2e 61 64 66 00 00 00 00 78 64 62 63 75 74 70 6e 2e 61 64 66 00 00 00 00 54 5f 55 70 5f 4e 65 78 74 5f 25 64 00 00 00 00 52 43 5f 25 64 00 00 00 49 4e 46 4f 5f 52 43 5f`

## `BOOT.BIN` @ `0x509288`: `xdbcutpn.adf`
- Matched term(s): `xdbcutpn`, `adf`, `cut`
- Assessment: **meaningful**
- Why it matters: Named database/table member; xrefs should lead to database table open/lookup code.
- Nearby printable strings:
  - `0x509250`: `xdbstore.adf`
  - `0x509260`: `xdbpref.adf`
  - `0x50926C`: `xdbrivl.adf`
  - `0x509278`: `xdbtrain.adf`
  - `0x509288`: `xdbcutpn.adf`
  - `0x509298`: `T_Up_Next_%d`
  - `0x5092A8`: `RC_%d`
  - `0x5092B0`: `INFO_RC_%d`
  - `0x5092BC`: `SUM_%d`
  - `0x5092CC`: `gHelpPopup.closePopup`
- Surrounding 128 bytes: `2e 61 64 66 00 00 00 00 78 64 62 73 74 6f 72 65 2e 61 64 66 00 00 00 00 78 64 62 70 72 65 66 2e 61 64 66 00 78 64 62 72 69 76 6c 2e 61 64 66 00 78 64 62 74 72 61 69 6e 2e 61 64 66 00 00 00 00 78 64 62 63 75 74 70 6e 2e 61 64 66 00 00 00 00 54 5f 55 70 5f 4e 65 78 74 5f 25 64 00 00 00 00 52 43 5f 25 64 00 00 00 49 4e 46 4f 5f 52 43 5f 25 64 00 00 53 55 4d 5f 25 64 00 00 00 00 00 00`

## `BOOT.BIN` @ `0x5096F0`: `trainer.fnc`
- Matched term(s): `trainer`, `fnc`, `AI`
- Assessment: **meaningful**
- Why it matters: Named contract/function script; xrefs should lead to contract/career script loading.
- Nearby printable strings:
  - `0x509410`: `INFO_Awards_20`
  - `0x509420`: `INFO_Awards_21`
  - `0x509430`: `INFO_Awards_22`
  - `0x509440`: `INFO_Awards_28`
  - `0x5096F0`: `trainer.fnc`
  - `0x509700`: `PERIODIC`
  - `0x509710`: `strBlueCornerCRO`
  - `0x509724`: `strRedCornerCRO`
  - `0x509734`: `strVenueCRO`
  - `0x509740`: `strLeftCRO`
- Surrounding 128 bytes: `f8 88 1b 00 f8 88 1b 00 f8 88 1b 00 00 89 1b 00 00 89 1b 00 00 89 1b 00 00 89 1b 00 08 89 1b 00 08 89 1b 00 08 89 1b 00 08 89 1b 00 08 89 1b 00 10 89 1b 00 10 89 1b 00 10 89 1b 00 10 89 1b 00 74 72 61 69 6e 65 72 2e 66 6e 63 00 00 00 00 00 50 45 52 49 4f 44 49 43 00 00 00 00 00 00 00 00 73 74 72 42 6c 75 65 43 6f 72 6e 65 72 43 52 4f 00 00 00 00 73 74 72 52 65 64 43 6f 72 6e 65 72`

## `BOOT.BIN` @ `0x509764`: `strCareerBoxer`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x509734`: `strVenueCRO`
  - `0x509740`: `strLeftCRO`
  - `0x50974C`: `strRightCRO`
  - `0x509758`: `strCROBoxer`
  - `0x509764`: `strCareerBoxer`
  - `0x509774`: `strCareerCentralBoxer`
  - `0x50978C`: `beltCRO0`
  - `0x509798`: `beltCRO1`
  - `0x5097A4`: `beltCRO2`
  - `0x5097B0`: `strFightHypeBoxerCRO`
- Surrounding 128 bytes: `73 74 72 52 65 64 43 6f 72 6e 65 72 43 52 4f 00 73 74 72 56 65 6e 75 65 43 52 4f 00 73 74 72 4c 65 66 74 43 52 4f 00 00 73 74 72 52 69 67 68 74 43 52 4f 00 73 74 72 43 52 4f 42 6f 78 65 72 00 73 74 72 43 61 72 65 65 72 42 6f 78 65 72 00 00 73 74 72 43 61 72 65 65 72 43 65 6e 74 72 61 6c 42 6f 78 65 72 00 00 00 62 65 6c 74 43 52 4f 30 00 00 00 00 62 65 6c 74 43 52 4f 31 00 00 00 00`

## `BOOT.BIN` @ `0x509774`: `strCareerCentralBoxer`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x509740`: `strLeftCRO`
  - `0x50974C`: `strRightCRO`
  - `0x509758`: `strCROBoxer`
  - `0x509764`: `strCareerBoxer`
  - `0x509774`: `strCareerCentralBoxer`
  - `0x50978C`: `beltCRO0`
  - `0x509798`: `beltCRO1`
  - `0x5097A4`: `beltCRO2`
  - `0x5097B0`: `strFightHypeBoxerCRO`
  - `0x5097C8`: `fighthype7CRO1`
- Surrounding 128 bytes: `73 74 72 56 65 6e 75 65 43 52 4f 00 73 74 72 4c 65 66 74 43 52 4f 00 00 73 74 72 52 69 67 68 74 43 52 4f 00 73 74 72 43 52 4f 42 6f 78 65 72 00 73 74 72 43 61 72 65 65 72 42 6f 78 65 72 00 00 73 74 72 43 61 72 65 65 72 43 65 6e 74 72 61 6c 42 6f 78 65 72 00 00 00 62 65 6c 74 43 52 4f 30 00 00 00 00 62 65 6c 74 43 52 4f 31 00 00 00 00 62 65 6c 74 43 52 4f 32 00 00 00 00 73 74 72 46`

## `BOOT.BIN` @ `0x5097E8`: `strCareerBlueBoxer`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x5097A4`: `beltCRO2`
  - `0x5097B0`: `strFightHypeBoxerCRO`
  - `0x5097C8`: `fighthype7CRO1`
  - `0x5097D8`: `fighthype7CRO2`
  - `0x5097E8`: `strCareerBlueBoxer`
  - `0x5097FC`: `strCareerRedBoxer`
  - `0x509810`: `strContractCRO`
  - `0x509820`: `fightStoreBoxer`
  - `0x509830`: `English`
  - `0x509838`: `%s.big`
- Surrounding 128 bytes: `43 52 4f 32 00 00 00 00 73 74 72 46 69 67 68 74 48 79 70 65 42 6f 78 65 72 43 52 4f 00 00 00 00 66 69 67 68 74 68 79 70 65 37 43 52 4f 31 00 00 66 69 67 68 74 68 79 70 65 37 43 52 4f 32 00 00 73 74 72 43 61 72 65 65 72 42 6c 75 65 42 6f 78 65 72 00 00 73 74 72 43 61 72 65 65 72 52 65 64 42 6f 78 65 72 00 00 00 73 74 72 43 6f 6e 74 72 61 63 74 43 52 4f 00 00 66 69 67 68 74 53 74 6f`

## `BOOT.BIN` @ `0x5097FC`: `strCareerRedBoxer`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x5097B0`: `strFightHypeBoxerCRO`
  - `0x5097C8`: `fighthype7CRO1`
  - `0x5097D8`: `fighthype7CRO2`
  - `0x5097E8`: `strCareerBlueBoxer`
  - `0x5097FC`: `strCareerRedBoxer`
  - `0x509810`: `strContractCRO`
  - `0x509820`: `fightStoreBoxer`
  - `0x509830`: `English`
  - `0x509838`: `%s.big`
  - `0x509840`: `iLangID`
- Surrounding 128 bytes: `42 6f 78 65 72 43 52 4f 00 00 00 00 66 69 67 68 74 68 79 70 65 37 43 52 4f 31 00 00 66 69 67 68 74 68 79 70 65 37 43 52 4f 32 00 00 73 74 72 43 61 72 65 65 72 42 6c 75 65 42 6f 78 65 72 00 00 73 74 72 43 61 72 65 65 72 52 65 64 42 6f 78 65 72 00 00 00 73 74 72 43 6f 6e 74 72 61 63 74 43 52 4f 00 00 66 69 67 68 74 53 74 6f 72 65 42 6f 78 65 72 00 45 6e 67 6c 69 73 68 00 25 73 2e 62`

## `BOOT.BIN` @ `0x509838`: `%s.big`
- Matched term(s): `big`
- Assessment: **meaningful**
- Why it matters: BIG archive/file-loader string; xrefs can identify archive/resource mounting code.
- Nearby printable strings:
  - `0x5097FC`: `strCareerRedBoxer`
  - `0x509810`: `strContractCRO`
  - `0x509820`: `fightStoreBoxer`
  - `0x509830`: `English`
  - `0x509838`: `%s.big`
  - `0x509840`: `iLangID`
  - `0x50984C`: `in_apt`
  - `0x509854`: `gPlatform`
  - `0x509860`: `gDebugDefine`
  - `0x509870`: `<< Viewer >> Load Animation Completed:  %s %s`
- Surrounding 128 bytes: `65 72 00 00 73 74 72 43 61 72 65 65 72 52 65 64 42 6f 78 65 72 00 00 00 73 74 72 43 6f 6e 74 72 61 63 74 43 52 4f 00 00 66 69 67 68 74 53 74 6f 72 65 42 6f 78 65 72 00 45 6e 67 6c 69 73 68 00 25 73 2e 62 69 67 00 00 69 4c 61 6e 67 49 44 00 25 64 00 00 69 6e 5f 61 70 74 00 00 67 50 6c 61 74 66 6f 72 6d 00 00 00 67 44 65 62 75 67 44 65 66 69 6e 65 00 00 00 00 3c 3c 20 56 69 65 77 65`

## `BOOT.BIN` @ `0x5098D4`: `apt/FEload.zlb`
- Matched term(s): `zlb`, `apt`
- Assessment: **meaningful**
- Why it matters: ZLB package path/string; likely compressed package/resource reference to trace through loader xrefs.
- Nearby printable strings:
  - `0x509870`: `<< Viewer >> Load Animation Completed:  %s %s`
  - `0x5098A0`: `bootFlow/bootLoading`
  - `0x5098B8`: `_level0`
  - `0x5098C0`: `gChyron.InitChyron`
  - `0x5098D4`: `apt/FEload.zlb`
  - `0x5098E4`: `apt/BEload.zlb`
  - `0x5098F4`: `apt\REALfonts.txt`
  - `0x509908`: `apt\FontTable.txt`
  - `0x50991C`: `fonts\`
  - `0x509924`: `.mfn`
- Surrounding 128 bytes: `64 3a 20 20 25 73 20 25 73 0a 00 00 62 6f 6f 74 46 6c 6f 77 2f 62 6f 6f 74 4c 6f 61 64 69 6e 67 00 00 00 00 5f 6c 65 76 65 6c 30 00 67 43 68 79 72 6f 6e 2e 49 6e 69 74 43 68 79 72 6f 6e 00 00 61 70 74 2f 46 45 6c 6f 61 64 2e 7a 6c 62 00 00 61 70 74 2f 42 45 6c 6f 61 64 2e 7a 6c 62 00 00 61 70 74 5c 52 45 41 4c 66 6f 6e 74 73 2e 74 78 74 00 00 00 61 70 74 5c 46 6f 6e 74 54 61 62 6c`

## `BOOT.BIN` @ `0x5098E4`: `apt/BEload.zlb`
- Matched term(s): `zlb`, `apt`
- Assessment: **meaningful**
- Why it matters: ZLB package path/string; likely compressed package/resource reference to trace through loader xrefs.
- Nearby printable strings:
  - `0x5098A0`: `bootFlow/bootLoading`
  - `0x5098B8`: `_level0`
  - `0x5098C0`: `gChyron.InitChyron`
  - `0x5098D4`: `apt/FEload.zlb`
  - `0x5098E4`: `apt/BEload.zlb`
  - `0x5098F4`: `apt\REALfonts.txt`
  - `0x509908`: `apt\FontTable.txt`
  - `0x50991C`: `fonts\`
  - `0x509924`: `.mfn`
  - `0x50992C`: `DisplayLoadingText`
- Surrounding 128 bytes: `46 6c 6f 77 2f 62 6f 6f 74 4c 6f 61 64 69 6e 67 00 00 00 00 5f 6c 65 76 65 6c 30 00 67 43 68 79 72 6f 6e 2e 49 6e 69 74 43 68 79 72 6f 6e 00 00 61 70 74 2f 46 45 6c 6f 61 64 2e 7a 6c 62 00 00 61 70 74 2f 42 45 6c 6f 61 64 2e 7a 6c 62 00 00 61 70 74 5c 52 45 41 4c 66 6f 6e 74 73 2e 74 78 74 00 00 00 61 70 74 5c 46 6f 6e 74 54 61 62 6c 65 2e 74 78 74 00 00 00 66 6f 6e 74 73 5c 00 00`

## `BOOT.BIN` @ `0x5099FC`: `$O_Hire_Cutman`
- Matched term(s): `cutman`, `cut`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x5099A8`: `playNowFE/febeLoadScreen`
  - `0x5099C4`: `DisplayMessageBox`
  - `0x5099DC`: `$T_pop_72`
  - `0x5099EC`: `$O_Use_Default`
  - `0x5099FC`: `$O_Hire_Cutman`
  - `0x509A0C`: `$O_Cancel`
  - `0x509A18`: `MAINMENU`
  - `0x509A24`: `main`
  - `0x509A2C`: `playNowBE/befeLoadScreen`
  - `0x509A48`: `apt\`
- Surrounding 128 bytes: `72 65 65 6e 00 00 00 00 44 69 73 70 6c 61 79 4d 65 73 73 61 67 65 42 6f 78 00 00 00 00 00 00 00 24 54 5f 70 6f 70 5f 37 32 00 00 00 33 00 00 00 24 4f 5f 55 73 65 5f 44 65 66 61 75 6c 74 00 00 24 4f 5f 48 69 72 65 5f 43 75 74 6d 61 6e 00 00 24 4f 5f 43 61 6e 63 65 6c 00 00 00 4d 41 49 4e 4d 45 4e 55 00 00 00 00 6d 61 69 6e 00 00 00 00 70 6c 61 79 4e 6f 77 42 45 2f 62 65 66 65 4c 6f`

## `BOOT.BIN` @ `0x509B88`: `screensfe/cmcareercentral`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x509B48`: `fecblights.lit`
  - `0x509B58`: `fesblights.lit`
  - `0x509B68`: `garbage`
  - `0x509B70`: `screensfe/boxerselect`
  - `0x509B88`: `screensfe/cmcareercentral`
  - `0x509BA4`: `screensfe/cmentrance`
  - `0x509BBC`: `screensfe/cmfightpreps`
  - `0x509BD4`: `screensfe/cmfightstore`
  - `0x509BEC`: `screensfe/cmlegendselect`
  - `0x509C08`: `screensfe/cmrankings`
- Surrounding 128 bytes: `66 65 63 62 6c 69 67 68 74 73 2e 6c 69 74 00 00 66 65 73 62 6c 69 67 68 74 73 2e 6c 69 74 00 00 67 61 72 62 61 67 65 00 73 63 72 65 65 6e 73 66 65 2f 62 6f 78 65 72 73 65 6c 65 63 74 00 00 00 73 63 72 65 65 6e 73 66 65 2f 63 6d 63 61 72 65 65 72 63 65 6e 74 72 61 6c 00 00 00 73 63 72 65 65 6e 73 66 65 2f 63 6d 65 6e 74 72 61 6e 63 65 00 00 00 00 73 63 72 65 65 6e 73 66 65 2f 63 6d`

## `BOOT.BIN` @ `0x509C64`: `screensfe/cmtrainingfocus`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x509C08`: `screensfe/cmrankings`
  - `0x509C20`: `screensfe/cmschedule`
  - `0x509C38`: `screensfe/cmscouting`
  - `0x509C50`: `screensfe/cmsummary`
  - `0x509C64`: `screensfe/cmtrainingfocus`
  - `0x509C80`: `screensfe/cmtrainingquick`
  - `0x509C9C`: `screensfe/controllerconfig`
  - `0x509CB8`: `screensfe/controllerselect`
  - `0x509CD4`: `screensfe/hhcontrollerselect`
  - `0x509CF4`: `screensfe/createboxer`
- Surrounding 128 bytes: `65 6e 73 66 65 2f 63 6d 73 63 68 65 64 75 6c 65 00 00 00 00 73 63 72 65 65 6e 73 66 65 2f 63 6d 73 63 6f 75 74 69 6e 67 00 00 00 00 73 63 72 65 65 6e 73 66 65 2f 63 6d 73 75 6d 6d 61 72 79 00 73 63 72 65 65 6e 73 66 65 2f 63 6d 74 72 61 69 6e 69 6e 67 66 6f 63 75 73 00 00 00 73 63 72 65 65 6e 73 66 65 2f 63 6d 74 72 61 69 6e 69 6e 67 71 75 69 63 6b 00 00 00 73 63 72 65 65 6e 73 66`

## `BOOT.BIN` @ `0x509C80`: `screensfe/cmtrainingquick`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x509C20`: `screensfe/cmschedule`
  - `0x509C38`: `screensfe/cmscouting`
  - `0x509C50`: `screensfe/cmsummary`
  - `0x509C64`: `screensfe/cmtrainingfocus`
  - `0x509C80`: `screensfe/cmtrainingquick`
  - `0x509C9C`: `screensfe/controllerconfig`
  - `0x509CB8`: `screensfe/controllerselect`
  - `0x509CD4`: `screensfe/hhcontrollerselect`
  - `0x509CF4`: `screensfe/createboxer`
  - `0x509D0C`: `screensfe/createboxeraccessories`
- Surrounding 128 bytes: `65 2f 63 6d 73 63 6f 75 74 69 6e 67 00 00 00 00 73 63 72 65 65 6e 73 66 65 2f 63 6d 73 75 6d 6d 61 72 79 00 73 63 72 65 65 6e 73 66 65 2f 63 6d 74 72 61 69 6e 69 6e 67 66 6f 63 75 73 00 00 00 73 63 72 65 65 6e 73 66 65 2f 63 6d 74 72 61 69 6e 69 6e 67 71 75 69 63 6b 00 00 00 73 63 72 65 65 6e 73 66 65 2f 63 6f 6e 74 72 6f 6c 6c 65 72 63 6f 6e 66 69 67 00 00 73 63 72 65 65 6e 73 66`

## `BOOT.BIN` @ `0x509E84`: `screensfe/loadcareer`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x509E30`: `screensfe/eaextras`
  - `0x509E44`: `screensfe/eatrax`
  - `0x509E58`: `screensfe/gamemodes`
  - `0x509E6C`: `screensfe/loadbetofe`
  - `0x509E84`: `screensfe/loadcareer`
  - `0x509E9C`: `screensfe/loademu`
  - `0x509EB0`: `screensfe/loadpoint`
  - `0x509EC4`: `screensfe/loadscrn`
  - `0x509ED8`: `screensfe/loadtip`
  - `0x509EEC`: `screensfe/mainmenu`
- Surrounding 128 bytes: `73 63 72 65 65 6e 73 66 65 2f 65 61 74 72 61 78 00 00 00 00 73 63 72 65 65 6e 73 66 65 2f 67 61 6d 65 6d 6f 64 65 73 00 73 63 72 65 65 6e 73 66 65 2f 6c 6f 61 64 62 65 74 6f 66 65 00 00 00 00 73 63 72 65 65 6e 73 66 65 2f 6c 6f 61 64 63 61 72 65 65 72 00 00 00 00 73 63 72 65 65 6e 73 66 65 2f 6c 6f 61 64 65 6d 75 00 00 00 73 63 72 65 65 6e 73 66 65 2f 6c 6f 61 64 70 6f 69 6e 74 00`

## `BOOT.BIN` @ `0x509FDC`: `screensfe/trainingfocus`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x509F88`: `screensfe/savepoint`
  - `0x509F9C`: `screensfe/settings`
  - `0x509FB0`: `screensfe/storage`
  - `0x509FC4`: `screensfe/titlescreen`
  - `0x509FDC`: `screensfe/trainingfocus`
  - `0x509FF4`: `screensfe/trainingoptions`
  - `0x50A010`: `screensfe/trainingquick`
  - `0x50A028`: `screensfe/trainingsummary`
  - `0x50A044`: `screensfe/venueselect`
  - `0x50A05C`: `screensfe/boxerlist`
- Surrounding 128 bytes: `73 63 72 65 65 6e 73 66 65 2f 73 65 74 74 69 6e 67 73 00 00 73 63 72 65 65 6e 73 66 65 2f 73 74 6f 72 61 67 65 00 00 00 73 63 72 65 65 6e 73 66 65 2f 74 69 74 6c 65 73 63 72 65 65 6e 00 00 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 66 6f 63 75 73 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 6f 70 74 69 6f 6e 73 00 00 00 73 63 72 65 65 6e 73 66 65 2f 74 72`

## `BOOT.BIN` @ `0x509FF4`: `screensfe/trainingoptions`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x509F9C`: `screensfe/settings`
  - `0x509FB0`: `screensfe/storage`
  - `0x509FC4`: `screensfe/titlescreen`
  - `0x509FDC`: `screensfe/trainingfocus`
  - `0x509FF4`: `screensfe/trainingoptions`
  - `0x50A010`: `screensfe/trainingquick`
  - `0x50A028`: `screensfe/trainingsummary`
  - `0x50A044`: `screensfe/venueselect`
  - `0x50A05C`: `screensfe/boxerlist`
  - `0x50A070`: `screensfe/hhboxerselect`
- Surrounding 128 bytes: `65 6e 73 66 65 2f 73 74 6f 72 61 67 65 00 00 00 73 63 72 65 65 6e 73 66 65 2f 74 69 74 6c 65 73 63 72 65 65 6e 00 00 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 66 6f 63 75 73 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 6f 70 74 69 6f 6e 73 00 00 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 71 75 69 63 6b 00 73 63 72 65 65 6e 73 66 65 2f 74 72`

## `BOOT.BIN` @ `0x50A010`: `screensfe/trainingquick`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x509FB0`: `screensfe/storage`
  - `0x509FC4`: `screensfe/titlescreen`
  - `0x509FDC`: `screensfe/trainingfocus`
  - `0x509FF4`: `screensfe/trainingoptions`
  - `0x50A010`: `screensfe/trainingquick`
  - `0x50A028`: `screensfe/trainingsummary`
  - `0x50A044`: `screensfe/venueselect`
  - `0x50A05C`: `screensfe/boxerlist`
  - `0x50A070`: `screensfe/hhboxerselect`
  - `0x50A088`: `screensfe/cmmatchup`
- Surrounding 128 bytes: `74 6c 65 73 63 72 65 65 6e 00 00 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 66 6f 63 75 73 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 6f 70 74 69 6f 6e 73 00 00 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 71 75 69 63 6b 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 73 75 6d 6d 61 72 79 00 00 00 73 63 72 65 65 6e 73 66 65 2f 76 65`

## `BOOT.BIN` @ `0x50A028`: `screensfe/trainingsummary`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x509FC4`: `screensfe/titlescreen`
  - `0x509FDC`: `screensfe/trainingfocus`
  - `0x509FF4`: `screensfe/trainingoptions`
  - `0x50A010`: `screensfe/trainingquick`
  - `0x50A028`: `screensfe/trainingsummary`
  - `0x50A044`: `screensfe/venueselect`
  - `0x50A05C`: `screensfe/boxerlist`
  - `0x50A070`: `screensfe/hhboxerselect`
  - `0x50A088`: `screensfe/cmmatchup`
  - `0x50A09C`: `easn/g7/gui/g7boxerselect`
- Surrounding 128 bytes: `61 69 6e 69 6e 67 66 6f 63 75 73 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 6f 70 74 69 6f 6e 73 00 00 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 71 75 69 63 6b 00 73 63 72 65 65 6e 73 66 65 2f 74 72 61 69 6e 69 6e 67 73 75 6d 6d 61 72 79 00 00 00 73 63 72 65 65 6e 73 66 65 2f 76 65 6e 75 65 73 65 6c 65 63 74 00 00 00 73 63 72 65 65 6e 73 66 65 2f 62 6f`

## `BOOT.BIN` @ `0x50A0EC`: `.msh`
- Matched term(s): `msh`
- Assessment: **meaningful**
- Why it matters: Mesh/model extension string; xrefs can identify model/resource loading paths.
- Nearby printable strings:
  - `0x50A0BC`: `gSM.getCurrentScreenID`
  - `0x50A0D4`: `none`
  - `0x50A0DC`: `bulb`
  - `0x50A0E4`: `bulba%s`
  - `0x50A0EC`: `.msh`
  - `0x50A0F4`: `E:\muon\boxing\main\game\source\boxing\fe\feplayer.cpp`
  - `0x50A12C`: `texture_file`
  - `0x50A13C`: `out of memory`
  - `0x50A388`: `out of memory`
  - `0x50A39C`: `GetStartScreenFromMain`
- Surrounding 128 bytes: `78 65 72 73 65 6c 65 63 74 00 00 00 00 00 00 00 67 53 4d 2e 67 65 74 43 75 72 72 65 6e 74 53 63 72 65 65 6e 49 44 00 00 6e 6f 6e 65 00 00 00 00 62 75 6c 62 00 00 00 00 62 75 6c 62 61 25 73 00 2e 6d 73 68 00 00 00 00 45 3a 5c 6d 75 6f 6e 5c 62 6f 78 69 6e 67 5c 6d 61 69 6e 5c 67 61 6d 65 5c 73 6f 75 72 63 65 5c 62 6f 78 69 6e 67 5c 66 65 5c 66 65 70 6c 61 79 65 72 2e 63 70 70 00 00`

## `BOOT.BIN` @ `0x50A558`: `careerModeFE2/selectALegend`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A530`: `SAVE`
  - `0x50A538`: `LOAD`
  - `0x50A540`: `DELETE`
  - `0x50A548`: `FILEMANAGEMENT`
  - `0x50A558`: `careerModeFE2/selectALegend`
  - `0x50A574`: `careerModeFE2/createChampRatings`
  - `0x50A598`: `careerModeFE2/createChampInfo`
  - `0x50A5B8`: `careerModeFE2/createChampPhysique`
  - `0x50A5DC`: `careerModeFE2/createChampBuild`
  - `0x50A5FC`: `careerModeFE2/createChampHeadShape`
- Surrounding 128 bytes: `53 45 4c 45 43 54 42 4f 58 45 52 00 53 41 56 45 50 52 4f 46 49 4c 45 00 53 41 56 45 00 00 00 00 4c 4f 41 44 00 00 00 00 44 45 4c 45 54 45 00 00 46 49 4c 45 4d 41 4e 41 47 45 4d 45 4e 54 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 73 65 6c 65 63 74 41 4c 65 67 65 6e 64 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 52 61 74 69 6e 67 73 00 00 00 00`

## `BOOT.BIN` @ `0x50A574`: `careerModeFE2/createChampRatings`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A538`: `LOAD`
  - `0x50A540`: `DELETE`
  - `0x50A548`: `FILEMANAGEMENT`
  - `0x50A558`: `careerModeFE2/selectALegend`
  - `0x50A574`: `careerModeFE2/createChampRatings`
  - `0x50A598`: `careerModeFE2/createChampInfo`
  - `0x50A5B8`: `careerModeFE2/createChampPhysique`
  - `0x50A5DC`: `careerModeFE2/createChampBuild`
  - `0x50A5FC`: `careerModeFE2/createChampHeadShape`
  - `0x50A620`: `careerModeFE2/createChampHeadFeatures`
- Surrounding 128 bytes: `00 00 00 00 4c 4f 41 44 00 00 00 00 44 45 4c 45 54 45 00 00 46 49 4c 45 4d 41 4e 41 47 45 4d 45 4e 54 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 73 65 6c 65 63 74 41 4c 65 67 65 6e 64 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 52 61 74 69 6e 67 73 00 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 49 6e 66`

## `BOOT.BIN` @ `0x50A598`: `careerModeFE2/createChampInfo`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A540`: `DELETE`
  - `0x50A548`: `FILEMANAGEMENT`
  - `0x50A558`: `careerModeFE2/selectALegend`
  - `0x50A574`: `careerModeFE2/createChampRatings`
  - `0x50A598`: `careerModeFE2/createChampInfo`
  - `0x50A5B8`: `careerModeFE2/createChampPhysique`
  - `0x50A5DC`: `careerModeFE2/createChampBuild`
  - `0x50A5FC`: `careerModeFE2/createChampHeadShape`
  - `0x50A620`: `careerModeFE2/createChampHeadFeatures`
  - `0x50A648`: `careerModeFE1/fightStore`
- Surrounding 128 bytes: `63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 73 65 6c 65 63 74 41 4c 65 67 65 6e 64 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 52 61 74 69 6e 67 73 00 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 49 6e 66 6f 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 50 68 79 73 69 71 75`

## `BOOT.BIN` @ `0x50A5B8`: `careerModeFE2/createChampPhysique`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A548`: `FILEMANAGEMENT`
  - `0x50A558`: `careerModeFE2/selectALegend`
  - `0x50A574`: `careerModeFE2/createChampRatings`
  - `0x50A598`: `careerModeFE2/createChampInfo`
  - `0x50A5B8`: `careerModeFE2/createChampPhysique`
  - `0x50A5DC`: `careerModeFE2/createChampBuild`
  - `0x50A5FC`: `careerModeFE2/createChampHeadShape`
  - `0x50A620`: `careerModeFE2/createChampHeadFeatures`
  - `0x50A648`: `careerModeFE1/fightStore`
  - `0x50A664`: `OperationComplete`
- Surrounding 128 bytes: `65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 52 61 74 69 6e 67 73 00 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 49 6e 66 6f 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 50 68 79 73 69 71 75 65 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 42 75 69`

## `BOOT.BIN` @ `0x50A5DC`: `careerModeFE2/createChampBuild`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A558`: `careerModeFE2/selectALegend`
  - `0x50A574`: `careerModeFE2/createChampRatings`
  - `0x50A598`: `careerModeFE2/createChampInfo`
  - `0x50A5B8`: `careerModeFE2/createChampPhysique`
  - `0x50A5DC`: `careerModeFE2/createChampBuild`
  - `0x50A5FC`: `careerModeFE2/createChampHeadShape`
  - `0x50A620`: `careerModeFE2/createChampHeadFeatures`
  - `0x50A648`: `careerModeFE1/fightStore`
  - `0x50A664`: `OperationComplete`
  - `0x50A678`: `_root`
- Surrounding 128 bytes: `65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 49 6e 66 6f 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 50 68 79 73 69 71 75 65 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 42 75 69 6c 64 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 48 65 61 64 53 68 61`

## `BOOT.BIN` @ `0x50A5FC`: `careerModeFE2/createChampHeadShape`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A574`: `careerModeFE2/createChampRatings`
  - `0x50A598`: `careerModeFE2/createChampInfo`
  - `0x50A5B8`: `careerModeFE2/createChampPhysique`
  - `0x50A5DC`: `careerModeFE2/createChampBuild`
  - `0x50A5FC`: `careerModeFE2/createChampHeadShape`
  - `0x50A620`: `careerModeFE2/createChampHeadFeatures`
  - `0x50A648`: `careerModeFE1/fightStore`
  - `0x50A664`: `OperationComplete`
  - `0x50A678`: `_root`
  - `0x50A688`: `GetProfileName`
- Surrounding 128 bytes: `65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 50 68 79 73 69 71 75 65 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 42 75 69 6c 64 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 48 65 61 64 53 68 61 70 65 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 48 65 61`

## `BOOT.BIN` @ `0x50A620`: `careerModeFE2/createChampHeadFeatures`
- Matched term(s): `adf`, `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A598`: `careerModeFE2/createChampInfo`
  - `0x50A5B8`: `careerModeFE2/createChampPhysique`
  - `0x50A5DC`: `careerModeFE2/createChampBuild`
  - `0x50A5FC`: `careerModeFE2/createChampHeadShape`
  - `0x50A620`: `careerModeFE2/createChampHeadFeatures`
  - `0x50A648`: `careerModeFE1/fightStore`
  - `0x50A664`: `OperationComplete`
  - `0x50A678`: `_root`
  - `0x50A688`: `GetProfileName`
  - `0x50A698`: `GetCareerCentralInfo`
- Surrounding 128 bytes: `65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 42 75 69 6c 64 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 48 65 61 64 53 68 61 70 65 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 48 65 61 64 46 65 61 74 75 72 65 73 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 31 2f 66 69 67 68 74 53 74 6f 72 65`

## `BOOT.BIN` @ `0x50A648`: `careerModeFE1/fightStore`
- Matched term(s): `fights`, `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A5B8`: `careerModeFE2/createChampPhysique`
  - `0x50A5DC`: `careerModeFE2/createChampBuild`
  - `0x50A5FC`: `careerModeFE2/createChampHeadShape`
  - `0x50A620`: `careerModeFE2/createChampHeadFeatures`
  - `0x50A648`: `careerModeFE1/fightStore`
  - `0x50A664`: `OperationComplete`
  - `0x50A678`: `_root`
  - `0x50A688`: `GetProfileName`
  - `0x50A698`: `GetCareerCentralInfo`
  - `0x50A6B0`: `GetCareerMode`
- Surrounding 128 bytes: `32 2f 63 72 65 61 74 65 43 68 61 6d 70 48 65 61 64 53 68 61 70 65 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 63 72 65 61 74 65 43 68 61 6d 70 48 65 61 64 46 65 61 74 75 72 65 73 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 31 2f 66 69 67 68 74 53 74 6f 72 65 00 00 00 00 4f 70 65 72 61 74 69 6f 6e 43 6f 6d 70 6c 65 74 65 00 00 00 5f 72 6f 6f 74 00 00 00 30 00 00 00 31 00 00 00`

## `BOOT.BIN` @ `0x50A698`: `GetCareerCentralInfo`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A648`: `careerModeFE1/fightStore`
  - `0x50A664`: `OperationComplete`
  - `0x50A678`: `_root`
  - `0x50A688`: `GetProfileName`
  - `0x50A698`: `GetCareerCentralInfo`
  - `0x50A6B0`: `GetCareerMode`
  - `0x50A6C0`: `GetNextEventState`
  - `0x50A6D4`: `SXBScreenSelected`
  - `0x50A6E8`: `PlayFESfx`
  - `0x50A6F4`: `ScreenReady`
- Surrounding 128 bytes: `67 68 74 53 74 6f 72 65 00 00 00 00 4f 70 65 72 61 74 69 6f 6e 43 6f 6d 70 6c 65 74 65 00 00 00 5f 72 6f 6f 74 00 00 00 30 00 00 00 31 00 00 00 47 65 74 50 72 6f 66 69 6c 65 4e 61 6d 65 00 00 47 65 74 43 61 72 65 65 72 43 65 6e 74 72 61 6c 49 6e 66 6f 00 00 00 00 47 65 74 43 61 72 65 65 72 4d 6f 64 65 00 00 00 47 65 74 4e 65 78 74 45 76 65 6e 74 53 74 61 74 65 00 00 00 53 58 42 53`

## `BOOT.BIN` @ `0x50A6B0`: `GetCareerMode`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A664`: `OperationComplete`
  - `0x50A678`: `_root`
  - `0x50A688`: `GetProfileName`
  - `0x50A698`: `GetCareerCentralInfo`
  - `0x50A6B0`: `GetCareerMode`
  - `0x50A6C0`: `GetNextEventState`
  - `0x50A6D4`: `SXBScreenSelected`
  - `0x50A6E8`: `PlayFESfx`
  - `0x50A6F4`: `ScreenReady`
  - `0x50A700`: `SetCareerMode`
- Surrounding 128 bytes: `70 6c 65 74 65 00 00 00 5f 72 6f 6f 74 00 00 00 30 00 00 00 31 00 00 00 47 65 74 50 72 6f 66 69 6c 65 4e 61 6d 65 00 00 47 65 74 43 61 72 65 65 72 43 65 6e 74 72 61 6c 49 6e 66 6f 00 00 00 00 47 65 74 43 61 72 65 65 72 4d 6f 64 65 00 00 00 47 65 74 4e 65 78 74 45 76 65 6e 74 53 74 61 74 65 00 00 00 53 58 42 53 63 72 65 65 6e 53 65 6c 65 63 74 65 64 00 00 00 50 6c 61 79 46 45 53 66`

## `BOOT.BIN` @ `0x50A700`: `SetCareerMode`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A6C0`: `GetNextEventState`
  - `0x50A6D4`: `SXBScreenSelected`
  - `0x50A6E8`: `PlayFESfx`
  - `0x50A6F4`: `ScreenReady`
  - `0x50A700`: `SetCareerMode`
  - `0x50A710`: `OnBoxerPoseChange`
  - `0x50A724`: `StartDemoLoop`
  - `0x50A734`: `StopDemoLoop`
  - `0x50A744`: `SetFEMainMenuData`
  - `0x50A758`: `GetFEMainMenuData`
- Surrounding 128 bytes: `47 65 74 4e 65 78 74 45 76 65 6e 74 53 74 61 74 65 00 00 00 53 58 42 53 63 72 65 65 6e 53 65 6c 65 63 74 65 64 00 00 00 50 6c 61 79 46 45 53 66 78 00 00 00 53 63 72 65 65 6e 52 65 61 64 79 00 53 65 74 43 61 72 65 65 72 4d 6f 64 65 00 00 00 4f 6e 42 6f 78 65 72 50 6f 73 65 43 68 61 6e 67 65 00 00 00 53 74 61 72 74 44 65 6d 6f 4c 6f 6f 70 00 00 00 53 74 6f 70 44 65 6d 6f 4c 6f 6f 70`

## `BOOT.BIN` @ `0x50A784`: `OnExitCareerMode`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A734`: `StopDemoLoop`
  - `0x50A744`: `SetFEMainMenuData`
  - `0x50A758`: `GetFEMainMenuData`
  - `0x50A76C`: `OnProfileSelectPopup`
  - `0x50A784`: `OnExitCareerMode`
  - `0x50A798`: `StartAutosave`
  - `0x50A7A8`: `Game.GetLocale`
  - `0x50A7B8`: `iProfileExists`
  - `0x50A7C8`: `T_None`
  - `0x50A7D0`: `HT_Active_Profile`
- Surrounding 128 bytes: `53 65 74 46 45 4d 61 69 6e 4d 65 6e 75 44 61 74 61 00 00 00 47 65 74 46 45 4d 61 69 6e 4d 65 6e 75 44 61 74 61 00 00 00 4f 6e 50 72 6f 66 69 6c 65 53 65 6c 65 63 74 50 6f 70 75 70 00 00 00 00 4f 6e 45 78 69 74 43 61 72 65 65 72 4d 6f 64 65 00 00 00 00 53 74 61 72 74 41 75 74 6f 73 61 76 65 00 00 00 47 61 6d 65 2e 47 65 74 4c 6f 63 61 6c 65 00 00 69 50 72 6f 66 69 6c 65 45 78 69 73`

## `BOOT.BIN` @ `0x50A810`: `iCareerMode`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A7D0`: `HT_Active_Profile`
  - `0x50A7E4`: `strProfileName`
  - `0x50A7F4`: `strProfileNamePopup`
  - `0x50A808`: `iNew`
  - `0x50A810`: `iCareerMode`
  - `0x50A81C`: `iCareerGameMode`
  - `0x50A82C`: `iTrainerContractSigned`
  - `0x50A844`: `iNextEvent`
  - `0x50A850`: `aData`
  - `0x50A858`: `iChoice`
- Surrounding 128 bytes: `48 54 5f 41 63 74 69 76 65 5f 50 72 6f 66 69 6c 65 00 00 00 73 74 72 50 72 6f 66 69 6c 65 4e 61 6d 65 00 00 73 74 72 50 72 6f 66 69 6c 65 4e 61 6d 65 50 6f 70 75 70 00 69 4e 65 77 00 00 00 00 69 43 61 72 65 65 72 4d 6f 64 65 00 69 43 61 72 65 65 72 47 61 6d 65 4d 6f 64 65 00 69 54 72 61 69 6e 65 72 43 6f 6e 74 72 61 63 74 53 69 67 6e 65 64 00 00 69 4e 65 78 74 45 76 65 6e 74 00 00`

## `BOOT.BIN` @ `0x50A81C`: `iCareerGameMode`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A7E4`: `strProfileName`
  - `0x50A7F4`: `strProfileNamePopup`
  - `0x50A808`: `iNew`
  - `0x50A810`: `iCareerMode`
  - `0x50A81C`: `iCareerGameMode`
  - `0x50A82C`: `iTrainerContractSigned`
  - `0x50A844`: `iNextEvent`
  - `0x50A850`: `aData`
  - `0x50A858`: `iChoice`
  - `0x50A860`: `AIPNet_GoToScreen`
- Surrounding 128 bytes: `6f 66 69 6c 65 00 00 00 73 74 72 50 72 6f 66 69 6c 65 4e 61 6d 65 00 00 73 74 72 50 72 6f 66 69 6c 65 4e 61 6d 65 50 6f 70 75 70 00 69 4e 65 77 00 00 00 00 69 43 61 72 65 65 72 4d 6f 64 65 00 69 43 61 72 65 65 72 47 61 6d 65 4d 6f 64 65 00 69 54 72 61 69 6e 65 72 43 6f 6e 74 72 61 63 74 53 69 67 6e 65 64 00 00 69 4e 65 78 74 45 76 65 6e 74 00 00 61 44 61 74 61 00 00 00 69 43 68 6f`

## `BOOT.BIN` @ `0x50A874`: `SELECTCAREERMODE`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50A844`: `iNextEvent`
  - `0x50A850`: `aData`
  - `0x50A858`: `iChoice`
  - `0x50A860`: `AIPNet_GoToScreen`
  - `0x50A874`: `SELECTCAREERMODE`
  - `0x50A888`: `MAINMENU`
  - `0x50A894`: `iYes`
  - `0x50A89C`: `iEnterScreen`
  - `0x50A8AC`: `iLocale`
  - `0x50A8B4`: `out of memory`
- Surrounding 128 bytes: `43 6f 6e 74 72 61 63 74 53 69 67 6e 65 64 00 00 69 4e 65 78 74 45 76 65 6e 74 00 00 61 44 61 74 61 00 00 00 69 43 68 6f 69 63 65 00 41 49 50 4e 65 74 5f 47 6f 54 6f 53 63 72 65 65 6e 00 00 00 53 45 4c 45 43 54 43 41 52 45 45 52 4d 4f 44 45 00 00 00 00 4d 41 49 4e 4d 45 4e 55 00 00 00 00 69 59 65 73 00 00 00 00 69 45 6e 74 65 72 53 63 72 65 65 6e 00 00 00 00 69 4c 6f 63 61 6c 65 00`

## `BOOT.BIN` @ `0x50A9FC`: `strMoney`
- Matched term(s): `money`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x50A9C4`: `ST_Record#`
  - `0x50A9D0`: `strWinLossRecord`
  - `0x50A9E4`: `M_Unranked`
  - `0x50A9F4`: `strRank`
  - `0x50A9FC`: `strMoney`
  - `0x50AA08`: `strRivalName`
  - `0x50AA18`: `T_NA`
  - `0x50AA20`: `strCROBoxer`
  - `0x50AA2C`: `strCareerBoxer`
  - `0x50AA3C`: `strCareerCentralBoxer`
- Surrounding 128 bytes: `6c 61 73 73 5f 36 00 00 53 54 5f 52 65 63 6f 72 64 23 00 00 73 74 72 57 69 6e 4c 6f 73 73 52 65 63 6f 72 64 00 00 00 00 4d 5f 55 6e 72 61 6e 6b 65 64 00 00 25 64 00 00 73 74 72 52 61 6e 6b 00 73 74 72 4d 6f 6e 65 79 00 00 00 00 73 74 72 52 69 76 61 6c 4e 61 6d 65 00 00 00 00 54 5f 4e 41 00 00 00 00 73 74 72 43 52 4f 42 6f 78 65 72 00 73 74 72 43 61 72 65 65 72 42 6f 78 65 72 00 00`

## `BOOT.BIN` @ `0x50ACD0`: `Money`
- Matched term(s): `money`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x50AC9C`: `Timercount`
  - `0x50ACA8`: `Timeup`
  - `0x50ACB0`: `StartFastcount`
  - `0x50ACC0`: `StopFastcount`
  - `0x50ACD0`: `Money`
  - `0x50ACD8`: `Negapplause`
  - `0x50ACE4`: `Applause1`
  - `0x50ACF0`: `Applause2`
  - `0x50ACFC`: `Applause3`
  - `0x50AD08`: `Stamp2`
- Surrounding 128 bytes: `74 30 00 00 53 74 61 6d 70 00 00 00 54 69 6d 65 72 63 6f 75 6e 74 00 00 54 69 6d 65 75 70 00 00 53 74 61 72 74 46 61 73 74 63 6f 75 6e 74 00 00 53 74 6f 70 46 61 73 74 63 6f 75 6e 74 00 00 00 4d 6f 6e 65 79 00 00 00 4e 65 67 61 70 70 6c 61 75 73 65 00 41 70 70 6c 61 75 73 65 31 00 00 00 41 70 70 6c 61 75 73 65 32 00 00 00 41 70 70 6c 61 75 73 65 33 00 00 00 53 74 61 6d 70 32 00 00`

## `BOOT.BIN` @ `0x50AD20`: `careerModeBE/Paycheck`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50ACFC`: `Applause3`
  - `0x50AD08`: `Stamp2`
  - `0x50AD10`: `Stamp3`
  - `0x50AD18`: `strCS`
  - `0x50AD20`: `careerModeBE/Paycheck`
  - `0x50AD38`: `T_pop_51`
  - `0x50AD48`: `O_Rematch`
  - `0x50AD54`: `O_Dont_Rematch`
  - `0x50AD64`: `T_pop_48`
  - `0x50AD70`: `menu/debugMenu`
- Surrounding 128 bytes: `75 73 65 00 41 70 70 6c 61 75 73 65 31 00 00 00 41 70 70 6c 61 75 73 65 32 00 00 00 41 70 70 6c 61 75 73 65 33 00 00 00 53 74 61 6d 70 32 00 00 53 74 61 6d 70 33 00 00 73 74 72 43 53 00 00 00 63 61 72 65 65 72 4d 6f 64 65 42 45 2f 50 61 79 63 68 65 63 6b 00 00 00 54 5f 70 6f 70 5f 35 31 00 00 00 00 32 00 00 00 4f 5f 52 65 6d 61 74 63 68 00 00 00 4f 5f 44 6f 6e 74 5f 52 65 6d 61 74`

## `BOOT.BIN` @ `0x50AD98`: `careerModeFE2/trainingResults`
- Matched term(s): `AI`, `career`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x50AD54`: `O_Dont_Rematch`
  - `0x50AD64`: `T_pop_48`
  - `0x50AD70`: `menu/debugMenu`
  - `0x50AD80`: `fightHype/fightHype0`
  - `0x50AD98`: `careerModeFE2/trainingResults`
  - `0x50ADB8`: `rivalChallenge/rivalChallengeFE`
  - `0x50ADD8`: `menu/MainMenu`
  - `0x50ADE8`: `ChangeScreenToCareerCentral`
  - `0x50AE04`: `strCO`
  - `0x50AE0C`: `menu/tutorialOverlay`
- Surrounding 128 bytes: `6e 74 5f 52 65 6d 61 74 63 68 00 00 54 5f 70 6f 70 5f 34 38 00 00 00 00 6d 65 6e 75 2f 64 65 62 75 67 4d 65 6e 75 00 00 66 69 67 68 74 48 79 70 65 2f 66 69 67 68 74 48 79 70 65 30 00 00 00 00 63 61 72 65 65 72 4d 6f 64 65 46 45 32 2f 74 72 61 69 6e 69 6e 67 52 65 73 75 6c 74 73 00 00 00 72 69 76 61 6c 43 68 61 6c 6c 65 6e 67 65 2f 72 69 76 61 6c 43 68 61 6c 6c 65 6e 67 65 46 45 00`

## `BOOT.BIN` @ `0x50ADE8`: `ChangeScreenToCareerCentral`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50AD80`: `fightHype/fightHype0`
  - `0x50AD98`: `careerModeFE2/trainingResults`
  - `0x50ADB8`: `rivalChallenge/rivalChallengeFE`
  - `0x50ADD8`: `menu/MainMenu`
  - `0x50ADE8`: `ChangeScreenToCareerCentral`
  - `0x50AE04`: `strCO`
  - `0x50AE0C`: `menu/tutorialOverlay`
  - `0x50AE24`: `gChyron.HideChyron`
  - `0x50AE38`: `DisplayMessageBox`
  - `0x50AE4C`: `$FS_T_Network_Error`
- Surrounding 128 bytes: `61 69 6e 69 6e 67 52 65 73 75 6c 74 73 00 00 00 72 69 76 61 6c 43 68 61 6c 6c 65 6e 67 65 2f 72 69 76 61 6c 43 68 61 6c 6c 65 6e 67 65 46 45 00 6d 65 6e 75 2f 4d 61 69 6e 4d 65 6e 75 00 00 00 43 68 61 6e 67 65 53 63 72 65 65 6e 54 6f 43 61 72 65 65 72 43 65 6e 74 72 61 6c 00 73 74 72 43 4f 00 00 00 6d 65 6e 75 2f 74 75 74 6f 72 69 61 6c 4f 76 65 72 6c 61 79 00 00 00 00 67 43 68 79`

## `BOOT.BIN` @ `0x50AFE8`: `iStamina`
- Matched term(s): `stamina`
- Assessment: **meaningful**
- Why it matters: Direct stamina label; search xrefs and runtime writes for stamina systems.
- Nearby printable strings:
  - `0x50AFC4`: `iCorner`
  - `0x50AFCC`: `iPower`
  - `0x50AFD4`: `iSpeed`
  - `0x50AFDC`: `iAgility`
  - `0x50AFE8`: `iStamina`
  - `0x50AFF4`: `iChin`
  - `0x50AFFC`: `iBody`
  - `0x50B004`: `iHeart`
  - `0x50B00C`: `iCuts`
  - `0x50B014`: `iOverall`
- Surrounding 128 bytes: `6e 64 6f 6d 42 6f 78 65 72 49 6e 66 6f 00 00 00 69 42 6f 78 65 72 49 44 00 00 00 00 69 43 6f 72 6e 65 72 00 69 50 6f 77 65 72 00 00 69 53 70 65 65 64 00 00 69 41 67 69 6c 69 74 79 00 00 00 00 69 53 74 61 6d 69 6e 61 00 00 00 00 69 43 68 69 6e 00 00 00 69 42 6f 64 79 00 00 00 69 48 65 61 72 74 00 00 69 43 75 74 73 00 00 00 69 4f 76 65 72 61 6c 6c 00 00 00 00 69 43 6f 72 6e 65 72 49`

## `BOOT.BIN` @ `0x50BC58`: `GetMyCareerStatsInfo`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50BC10`: `strCRORightBoxer`
  - `0x50BC24`: `strRedCornerCRO`
  - `0x50BC34`: `iRivalMatchup`
  - `0x50BC44`: `iIsScoutingReport`
  - `0x50BC58`: `GetMyCareerStatsInfo`
  - `0x50BC70`: `iRank`
  - `0x50BC78`: `aiRankRating`
  - `0x50BC88`: `astrCareerRecord`
  - `0x50BC9C`: `astrCurrentRival`
  - `0x50BCB0`: `astrRivalFightRecord`
- Surrounding 128 bytes: `67 68 74 42 6f 78 65 72 00 00 00 00 73 74 72 52 65 64 43 6f 72 6e 65 72 43 52 4f 00 69 52 69 76 61 6c 4d 61 74 63 68 75 70 00 00 00 69 49 73 53 63 6f 75 74 69 6e 67 52 65 70 6f 72 74 00 00 00 47 65 74 4d 79 43 61 72 65 65 72 53 74 61 74 73 49 6e 66 6f 00 00 00 00 69 52 61 6e 6b 00 00 00 61 69 52 61 6e 6b 52 61 74 69 6e 67 00 00 00 00 61 73 74 72 43 61 72 65 65 72 52 65 63 6f 72 64`

## `BOOT.BIN` @ `0x50BC88`: `astrCareerRecord`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50BC44`: `iIsScoutingReport`
  - `0x50BC58`: `GetMyCareerStatsInfo`
  - `0x50BC70`: `iRank`
  - `0x50BC78`: `aiRankRating`
  - `0x50BC88`: `astrCareerRecord`
  - `0x50BC9C`: `astrCurrentRival`
  - `0x50BCB0`: `astrRivalFightRecord`
  - `0x50BCC8`: `aiTitleBeltsWon`
  - `0x50BCD8`: `aiTitleBeltsDefended`
  - `0x50BCF0`: `aiTitleBeltsLost`
- Surrounding 128 bytes: `63 6f 75 74 69 6e 67 52 65 70 6f 72 74 00 00 00 47 65 74 4d 79 43 61 72 65 65 72 53 74 61 74 73 49 6e 66 6f 00 00 00 00 69 52 61 6e 6b 00 00 00 61 69 52 61 6e 6b 52 61 74 69 6e 67 00 00 00 00 61 73 74 72 43 61 72 65 65 72 52 65 63 6f 72 64 00 00 00 00 61 73 74 72 43 75 72 72 65 6e 74 52 69 76 61 6c 00 00 00 00 61 73 74 72 52 69 76 61 6c 46 69 67 68 74 52 65 63 6f 72 64 00 00 00 00`

## `BOOT.BIN` @ `0x50C838`: `GetTrainingInfo`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x50C800`: `strCROBoxer`
  - `0x50C80C`: `iRatingType`
  - `0x50C818`: `iValue`
  - `0x50C820`: `iRemainingPoints`
  - `0x50C838`: `GetTrainingInfo`
  - `0x50C848`: `SetTrainingInfo`
  - `0x50C858`: `LeaveTraining`
  - `0x50C868`: `aStats`
  - `0x50C870`: `strCROBoxer`
  - `0x50C87C`: `iIntensity`
- Surrounding 128 bytes: `72 61 6c 6c 00 00 00 00 73 74 72 43 52 4f 42 6f 78 65 72 00 69 52 61 74 69 6e 67 54 79 70 65 00 69 56 61 6c 75 65 00 00 69 52 65 6d 61 69 6e 69 6e 67 50 6f 69 6e 74 73 00 00 00 00 00 00 00 00 47 65 74 54 72 61 69 6e 69 6e 67 49 6e 66 6f 00 53 65 74 54 72 61 69 6e 69 6e 67 49 6e 66 6f 00 4c 65 61 76 65 54 72 61 69 6e 69 6e 67 00 00 00 61 53 74 61 74 73 00 00 73 74 72 43 52 4f 42 6f`

## `BOOT.BIN` @ `0x50C848`: `SetTrainingInfo`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x50C80C`: `iRatingType`
  - `0x50C818`: `iValue`
  - `0x50C820`: `iRemainingPoints`
  - `0x50C838`: `GetTrainingInfo`
  - `0x50C848`: `SetTrainingInfo`
  - `0x50C858`: `LeaveTraining`
  - `0x50C868`: `aStats`
  - `0x50C870`: `strCROBoxer`
  - `0x50C87C`: `iIntensity`
  - `0x50C888`: `iFocus`
- Surrounding 128 bytes: `78 65 72 00 69 52 61 74 69 6e 67 54 79 70 65 00 69 56 61 6c 75 65 00 00 69 52 65 6d 61 69 6e 69 6e 67 50 6f 69 6e 74 73 00 00 00 00 00 00 00 00 47 65 74 54 72 61 69 6e 69 6e 67 49 6e 66 6f 00 53 65 74 54 72 61 69 6e 69 6e 67 49 6e 66 6f 00 4c 65 61 76 65 54 72 61 69 6e 69 6e 67 00 00 00 61 53 74 61 74 73 00 00 73 74 72 43 52 4f 42 6f 78 65 72 00 69 49 6e 74 65 6e 73 69 74 79 00 00`

## `BOOT.BIN` @ `0x50C858`: `LeaveTraining`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x50C818`: `iValue`
  - `0x50C820`: `iRemainingPoints`
  - `0x50C838`: `GetTrainingInfo`
  - `0x50C848`: `SetTrainingInfo`
  - `0x50C858`: `LeaveTraining`
  - `0x50C868`: `aStats`
  - `0x50C870`: `strCROBoxer`
  - `0x50C87C`: `iIntensity`
  - `0x50C888`: `iFocus`
  - `0x50C890`: `GetTrainingResultsInfo`
- Surrounding 128 bytes: `69 56 61 6c 75 65 00 00 69 52 65 6d 61 69 6e 69 6e 67 50 6f 69 6e 74 73 00 00 00 00 00 00 00 00 47 65 74 54 72 61 69 6e 69 6e 67 49 6e 66 6f 00 53 65 74 54 72 61 69 6e 69 6e 67 49 6e 66 6f 00 4c 65 61 76 65 54 72 61 69 6e 69 6e 67 00 00 00 61 53 74 61 74 73 00 00 73 74 72 43 52 4f 42 6f 78 65 72 00 69 49 6e 74 65 6e 73 69 74 79 00 00 69 46 6f 63 75 73 00 00 47 65 74 54 72 61 69 6e`

## `BOOT.BIN` @ `0x50C890`: `GetTrainingResultsInfo`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x50C868`: `aStats`
  - `0x50C870`: `strCROBoxer`
  - `0x50C87C`: `iIntensity`
  - `0x50C888`: `iFocus`
  - `0x50C890`: `GetTrainingResultsInfo`
  - `0x50C8A8`: `OnMeasuringResultsFinished`
  - `0x50C8C4`: `UserExitingTrainingResults`
  - `0x50C8E0`: `ContinueWithExit`
  - `0x50C8F4`: `gMainScreen`
  - `0x50C904`: `INFO_Division_1`
- Surrounding 128 bytes: `69 6e 67 49 6e 66 6f 00 4c 65 61 76 65 54 72 61 69 6e 69 6e 67 00 00 00 61 53 74 61 74 73 00 00 73 74 72 43 52 4f 42 6f 78 65 72 00 69 49 6e 74 65 6e 73 69 74 79 00 00 69 46 6f 63 75 73 00 00 47 65 74 54 72 61 69 6e 69 6e 67 52 65 73 75 6c 74 73 49 6e 66 6f 00 00 4f 6e 4d 65 61 73 75 72 69 6e 67 52 65 73 75 6c 74 73 46 69 6e 69 73 68 65 64 00 00 55 73 65 72 45 78 69 74 69 6e 67 54`

## `BOOT.BIN` @ `0x50C8C4`: `UserExitingTrainingResults`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x50C87C`: `iIntensity`
  - `0x50C888`: `iFocus`
  - `0x50C890`: `GetTrainingResultsInfo`
  - `0x50C8A8`: `OnMeasuringResultsFinished`
  - `0x50C8C4`: `UserExitingTrainingResults`
  - `0x50C8E0`: `ContinueWithExit`
  - `0x50C8F4`: `gMainScreen`
  - `0x50C904`: `INFO_Division_1`
  - `0x50C914`: `INFO_Division_2`
  - `0x50C924`: `INFO_Division_3`
- Surrounding 128 bytes: `74 79 00 00 69 46 6f 63 75 73 00 00 47 65 74 54 72 61 69 6e 69 6e 67 52 65 73 75 6c 74 73 49 6e 66 6f 00 00 4f 6e 4d 65 61 73 75 72 69 6e 67 52 65 73 75 6c 74 73 46 69 6e 69 73 68 65 64 00 00 55 73 65 72 45 78 69 74 69 6e 67 54 72 61 69 6e 69 6e 67 52 65 73 75 6c 74 73 00 00 43 6f 6e 74 69 6e 75 65 57 69 74 68 45 78 69 74 00 00 00 00 67 4d 61 69 6e 53 63 72 65 65 6e 00 00 00 00 00`

## `BOOT.BIN` @ `0x50CCC0`: `feCRO/vnecro.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x50CC74`: `O_Entourage_%d`
  - `0x50CC84`: `INFO_Entourage_%d`
  - `0x50CC98`: `strCROBoxer`
  - `0x50CCA4`: `iTrainerContractSigned`
  - `0x50CCC0`: `feCRO/vnecro.viv`
  - `0x50CCD4`: `feCRO/fhcro.viv`
  - `0x50CCE4`: `%s%s.%s`
  - `0x50CCEC`: `feCRO/vnecro.viv|`
  - `0x50CD08`: `feCRO/fhcro.viv|`
  - `0x50CD1C`: `3_00`
- Surrounding 128 bytes: `25 64 00 00 49 4e 46 4f 5f 45 6e 74 6f 75 72 61 67 65 5f 25 64 00 00 00 73 74 72 43 52 4f 42 6f 78 65 72 00 69 54 72 61 69 6e 65 72 43 6f 6e 74 72 61 63 74 53 69 67 6e 65 64 00 00 00 00 00 00 66 65 43 52 4f 2f 76 6e 65 63 72 6f 2e 76 69 76 00 00 00 00 66 65 43 52 4f 2f 66 68 63 72 6f 2e 76 69 76 00 25 73 25 73 2e 25 73 00 66 65 43 52 4f 2f 76 6e 65 63 72 6f 2e 76 69 76 7c 00 00 00`

## `BOOT.BIN` @ `0x50CCD4`: `feCRO/fhcro.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x50CC84`: `INFO_Entourage_%d`
  - `0x50CC98`: `strCROBoxer`
  - `0x50CCA4`: `iTrainerContractSigned`
  - `0x50CCC0`: `feCRO/vnecro.viv`
  - `0x50CCD4`: `feCRO/fhcro.viv`
  - `0x50CCE4`: `%s%s.%s`
  - `0x50CCEC`: `feCRO/vnecro.viv|`
  - `0x50CD08`: `feCRO/fhcro.viv|`
  - `0x50CD1C`: `3_00`
  - `0x50CD24`: `feCRO/carbxrcro.viv|`
- Surrounding 128 bytes: `64 00 00 00 73 74 72 43 52 4f 42 6f 78 65 72 00 69 54 72 61 69 6e 65 72 43 6f 6e 74 72 61 63 74 53 69 67 6e 65 64 00 00 00 00 00 00 66 65 43 52 4f 2f 76 6e 65 63 72 6f 2e 76 69 76 00 00 00 00 66 65 43 52 4f 2f 66 68 63 72 6f 2e 76 69 76 00 25 73 25 73 2e 25 73 00 66 65 43 52 4f 2f 76 6e 65 63 72 6f 2e 76 69 76 7c 00 00 00 6d 73 68 00 30 39 00 00 66 65 43 52 4f 2f 66 68 63 72 6f 2e`

## `BOOT.BIN` @ `0x50CCEC`: `feCRO/vnecro.viv|`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x50CCA4`: `iTrainerContractSigned`
  - `0x50CCC0`: `feCRO/vnecro.viv`
  - `0x50CCD4`: `feCRO/fhcro.viv`
  - `0x50CCE4`: `%s%s.%s`
  - `0x50CCEC`: `feCRO/vnecro.viv|`
  - `0x50CD08`: `feCRO/fhcro.viv|`
  - `0x50CD1C`: `3_00`
  - `0x50CD24`: `feCRO/carbxrcro.viv|`
  - `0x50CD40`: `LoadingScreenReady`
  - `0x50CD58`: `$M_Win_KO`
- Surrounding 128 bytes: `43 6f 6e 74 72 61 63 74 53 69 67 6e 65 64 00 00 00 00 00 00 66 65 43 52 4f 2f 76 6e 65 63 72 6f 2e 76 69 76 00 00 00 00 66 65 43 52 4f 2f 66 68 63 72 6f 2e 76 69 76 00 25 73 25 73 2e 25 73 00 66 65 43 52 4f 2f 76 6e 65 63 72 6f 2e 76 69 76 7c 00 00 00 6d 73 68 00 30 39 00 00 66 65 43 52 4f 2f 66 68 63 72 6f 2e 76 69 76 7c 00 00 00 00 33 5f 30 30 00 00 00 00 66 65 43 52 4f 2f 63 61`

## `BOOT.BIN` @ `0x50CD08`: `feCRO/fhcro.viv|`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x50CCC0`: `feCRO/vnecro.viv`
  - `0x50CCD4`: `feCRO/fhcro.viv`
  - `0x50CCE4`: `%s%s.%s`
  - `0x50CCEC`: `feCRO/vnecro.viv|`
  - `0x50CD08`: `feCRO/fhcro.viv|`
  - `0x50CD1C`: `3_00`
  - `0x50CD24`: `feCRO/carbxrcro.viv|`
  - `0x50CD40`: `LoadingScreenReady`
  - `0x50CD58`: `$M_Win_KO`
  - `0x50CD64`: `$M_Win_Decision`
- Surrounding 128 bytes: `65 63 72 6f 2e 76 69 76 00 00 00 00 66 65 43 52 4f 2f 66 68 63 72 6f 2e 76 69 76 00 25 73 25 73 2e 25 73 00 66 65 43 52 4f 2f 76 6e 65 63 72 6f 2e 76 69 76 7c 00 00 00 6d 73 68 00 30 39 00 00 66 65 43 52 4f 2f 66 68 63 72 6f 2e 76 69 76 7c 00 00 00 00 33 5f 30 30 00 00 00 00 66 65 43 52 4f 2f 63 61 72 62 78 72 63 72 6f 2e 76 69 76 7c 00 00 00 00 00 00 00 00 4c 6f 61 64 69 6e 67 53`

## `BOOT.BIN` @ `0x50CD24`: `feCRO/carbxrcro.viv|`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x50CCE4`: `%s%s.%s`
  - `0x50CCEC`: `feCRO/vnecro.viv|`
  - `0x50CD08`: `feCRO/fhcro.viv|`
  - `0x50CD1C`: `3_00`
  - `0x50CD24`: `feCRO/carbxrcro.viv|`
  - `0x50CD40`: `LoadingScreenReady`
  - `0x50CD58`: `$M_Win_KO`
  - `0x50CD64`: `$M_Win_Decision`
  - `0x50CD74`: `$M_Loss_KO`
  - `0x50CD80`: `$M_Loss_Decision`
- Surrounding 128 bytes: `25 73 25 73 2e 25 73 00 66 65 43 52 4f 2f 76 6e 65 63 72 6f 2e 76 69 76 7c 00 00 00 6d 73 68 00 30 39 00 00 66 65 43 52 4f 2f 66 68 63 72 6f 2e 76 69 76 7c 00 00 00 00 33 5f 30 30 00 00 00 00 66 65 43 52 4f 2f 63 61 72 62 78 72 63 72 6f 2e 76 69 76 7c 00 00 00 00 00 00 00 00 4c 6f 61 64 69 6e 67 53 63 72 65 65 6e 52 65 61 64 79 00 00 00 00 00 00 24 4d 5f 57 69 6e 5f 4b 4f 00 00 00`

## `BOOT.BIN` @ `0x50CD9C`: `GetCareerHistoryInfo`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50CD64`: `$M_Win_Decision`
  - `0x50CD74`: `$M_Loss_KO`
  - `0x50CD80`: `$M_Loss_Decision`
  - `0x50CD94`: `$M_Draw`
  - `0x50CD9C`: `GetCareerHistoryInfo`
  - `0x50CDB4`: `GetAdhocRivalsUserInfo`
  - `0x50CDCC`: `GetAdhocRivalsInfo`
  - `0x50CDE0`: `GetRecordBooksInfo`
  - `0x50CDF4`: `iClass`
  - `0x50CDFC`: `iCurrentClass`
- Surrounding 128 bytes: `69 6e 5f 4b 4f 00 00 00 24 4d 5f 57 69 6e 5f 44 65 63 69 73 69 6f 6e 00 24 4d 5f 4c 6f 73 73 5f 4b 4f 00 00 24 4d 5f 4c 6f 73 73 5f 44 65 63 69 73 69 6f 6e 00 00 00 00 24 4d 5f 44 72 61 77 00 47 65 74 43 61 72 65 65 72 48 69 73 74 6f 72 79 49 6e 66 6f 00 00 00 00 47 65 74 41 64 68 6f 63 52 69 76 61 6c 73 55 73 65 72 49 6e 66 6f 00 00 47 65 74 41 64 68 6f 63 52 69 76 61 6c 73 49 6e`

## `BOOT.BIN` @ `0x50D770`: `astrCareers`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50D70C`: `aSettings`
  - `0x50D740`: `GetHallofFameInfo`
  - `0x50D754`: `astrBoxerNames`
  - `0x50D764`: `astrRecords`
  - `0x50D770`: `astrCareers`
  - `0x50D77C`: `%s %s`
  - `0x50D784`: `ST_Record#`
  - `0x50D790`: `%d-%d`
  - `0x50D798`: `GetTrophyCaseInfo`
  - `0x50D7AC`: `GetTrophyInfo`
- Surrounding 128 bytes: `4c b9 1f 00 44 b9 1f 00 44 b9 1f 00 00 00 00 00 47 65 74 48 61 6c 6c 6f 66 46 61 6d 65 49 6e 66 6f 00 00 00 61 73 74 72 42 6f 78 65 72 4e 61 6d 65 73 00 00 61 73 74 72 52 65 63 6f 72 64 73 00 61 73 74 72 43 61 72 65 65 72 73 00 25 73 20 25 73 00 00 00 53 54 5f 52 65 63 6f 72 64 23 00 00 25 64 2d 25 64 00 00 00 47 65 74 54 72 6f 70 68 79 43 61 73 65 49 6e 66 6f 00 00 00 47 65 74 54`

## `BOOT.BIN` @ `0x50DB54`: `astrContractPurse`
- Matched term(s): `purse`, `contract`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x50DB08`: `aContractID`
  - `0x50DB14`: `astrContractGoals`
  - `0x50DB28`: `astrContractRanks`
  - `0x50DB3C`: `astrContractOpponents`
  - `0x50DB54`: `astrContractPurse`
  - `0x50DB68`: `GetFightContractInfo`
  - `0x50DB80`: `GetIndividualContractInfo`
  - `0x50DB9C`: `OnSelectFightContract`
  - `0x50DBB4`: `OnSelectFightContractConfirm`
  - `0x50DBD4`: `GetFinePrintInfo`
- Surrounding 128 bytes: `61 73 74 72 43 6f 6e 74 72 61 63 74 47 6f 61 6c 73 00 00 00 61 73 74 72 43 6f 6e 74 72 61 63 74 52 61 6e 6b 73 00 00 00 61 73 74 72 43 6f 6e 74 72 61 63 74 4f 70 70 6f 6e 65 6e 74 73 00 00 00 61 73 74 72 43 6f 6e 74 72 61 63 74 50 75 72 73 65 00 00 00 47 65 74 46 69 67 68 74 43 6f 6e 74 72 61 63 74 49 6e 66 6f 00 00 00 00 47 65 74 49 6e 64 69 76 69 64 75 61 6c 43 6f 6e 74 72 61 63`

## `BOOT.BIN` @ `0x50DD30`: `$INFO_Money`
- Matched term(s): `money`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x50DCE0`: `INFO_Awards_7`
  - `0x50DCF0`: `INFO_Awards_Unknown`
  - `0x50DD08`: `iRetireContractID`
  - `0x50DD1C`: `iGoProContractID`
  - `0x50DD30`: `$INFO_Money`
  - `0x50DD3C`: `$INFO_Rank`
  - `0x50DD48`: `$INFO_Go_Pro`
  - `0x50DD58`: `%s %s`
  - `0x50DD64`: `iCareerStage`
  - `0x50DD74`: `iContractSigned`
- Surrounding 128 bytes: `49 4e 46 4f 5f 41 77 61 72 64 73 5f 55 6e 6b 6e 6f 77 6e 00 2d 2d 00 00 69 52 65 74 69 72 65 43 6f 6e 74 72 61 63 74 49 44 00 00 00 69 47 6f 50 72 6f 43 6f 6e 74 72 61 63 74 49 44 00 00 00 00 24 49 4e 46 4f 5f 4d 6f 6e 65 79 00 24 49 4e 46 4f 5f 52 61 6e 6b 00 00 24 49 4e 46 4f 5f 47 6f 5f 50 72 6f 00 00 00 00 25 73 20 25 73 00 00 00 25 64 00 00 69 43 61 72 65 65 72 53 74 61 67 65`

## `BOOT.BIN` @ `0x50DD64`: `iCareerStage`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50DD30`: `$INFO_Money`
  - `0x50DD3C`: `$INFO_Rank`
  - `0x50DD48`: `$INFO_Go_Pro`
  - `0x50DD58`: `%s %s`
  - `0x50DD64`: `iCareerStage`
  - `0x50DD74`: `iContractSigned`
  - `0x50DD84`: `INFO_Earnings`
  - `0x50DD94`: `strEarnings`
  - `0x50DDA0`: `INFO_Bank`
  - `0x50DDAC`: `strAccount`
- Surrounding 128 bytes: `6e 74 72 61 63 74 49 44 00 00 00 00 24 49 4e 46 4f 5f 4d 6f 6e 65 79 00 24 49 4e 46 4f 5f 52 61 6e 6b 00 00 24 49 4e 46 4f 5f 47 6f 5f 50 72 6f 00 00 00 00 25 73 20 25 73 00 00 00 25 64 00 00 69 43 61 72 65 65 72 53 74 61 67 65 00 00 00 00 69 43 6f 6e 74 72 61 63 74 53 69 67 6e 65 64 00 49 4e 46 4f 5f 45 61 72 6e 69 6e 67 73 00 00 00 73 74 72 45 61 72 6e 69 6e 67 73 00 49 4e 46 4f`

## `BOOT.BIN` @ `0x50DE7C`: `strPurseCut`
- Matched term(s): `cut`, `purse`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x50DE50`: `strRank`
  - `0x50DE58`: `INFO_Date`
  - `0x50DE64`: `strDate`
  - `0x50DE6C`: `strFightType`
  - `0x50DE7C`: `strPurseCut`
  - `0x50DE8C`: `strRankChange`
  - `0x50DE9C`: `strDivision`
  - `0x50DEA8`: `strVenue`
  - `0x50DEB4`: `strTimetoFight`
  - `0x50DEC4`: `INFO_Your_Cut`
- Surrounding 128 bytes: `5f 36 00 00 49 4e 46 4f 5f 59 6f 75 72 5f 52 61 6e 6b 00 00 73 74 72 52 61 6e 6b 00 49 4e 46 4f 5f 44 61 74 65 00 00 00 73 74 72 44 61 74 65 00 73 74 72 46 69 67 68 74 54 79 70 65 00 00 00 00 73 74 72 50 75 72 73 65 43 75 74 00 00 00 00 00 73 74 72 52 61 6e 6b 43 68 61 6e 67 65 00 00 00 73 74 72 44 69 76 69 73 69 6f 6e 00 73 74 72 56 65 6e 75 65 00 00 00 00 73 74 72 54 69 6d 65 74`

## `BOOT.BIN` @ `0x50E890`: `GetCareerSummaryInfo`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50E84C`: `strContractCRO`
  - `0x50E85C`: `strBank`
  - `0x50E864`: `iContractType`
  - `0x50E874`: `iSignedContractPerson`
  - `0x50E890`: `GetCareerSummaryInfo`
  - `0x50E8A8`: `iRank`
  - `0x50E8B0`: `strBoxerFirstName`
  - `0x50E8C4`: `strBoxerLastName`
  - `0x50E8D8`: `astrSummaryInfo`
  - `0x50E8EC`: `%d-%d`
- Surrounding 128 bytes: `6f 6e 74 72 61 63 74 43 52 4f 00 00 73 74 72 42 61 6e 6b 00 69 43 6f 6e 74 72 61 63 74 54 79 70 65 00 00 00 69 53 69 67 6e 65 64 43 6f 6e 74 72 61 63 74 50 65 72 73 6f 6e 00 00 00 00 00 00 00 47 65 74 43 61 72 65 65 72 53 75 6d 6d 61 72 79 49 6e 66 6f 00 00 00 00 69 52 61 6e 6b 00 00 00 73 74 72 42 6f 78 65 72 46 69 72 73 74 4e 61 6d 65 00 00 00 73 74 72 42 6f 78 65 72 4c 61 73 74`

## `BOOT.BIN` @ `0x50EB48`: `re_Purse`
- Matched term(s): `purse`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x50EB04`: `strVenueName`
  - `0x50EB14`: `INFO_15_Untimed`
  - `0x50EB24`: `INFO_Minute_Rounds`
  - `0x50EB38`: `strRoundInfo`
  - `0x50EB48`: `re_Purse`
  - `0x50EB54`: `%s %s (%s)`
  - `0x50EB60`: `strCutPercentage`
  - `0x50EB74`: `INFO_Awards_0`
  - `0x50EB84`: `INFO_Awards_1`
  - `0x50EB94`: `INFO_Awards_15`
- Surrounding 128 bytes: `65 6e 75 65 4e 61 6d 65 00 00 00 00 49 4e 46 4f 5f 31 35 5f 55 6e 74 69 6d 65 64 00 49 4e 46 4f 5f 4d 69 6e 75 74 65 5f 52 6f 75 6e 64 73 00 00 73 74 72 52 6f 75 6e 64 49 6e 66 6f 00 00 00 00 72 65 5f 50 75 72 73 65 00 00 00 00 25 73 20 25 73 20 28 25 73 29 00 00 73 74 72 43 75 74 50 65 72 63 65 6e 74 61 67 65 00 00 00 00 49 4e 46 4f 5f 41 77 61 72 64 73 5f 30 00 00 00 49 4e 46 4f`

## `BOOT.BIN` @ `0x50EC94`: `O_Hire_Cutman`
- Matched term(s): `cutman`, `cut`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50EC5C`: `INFO_Only_Ref`
  - `0x50EC6C`: `M_3_Knockdown_Rule`
  - `0x50EC80`: `strRules`
  - `0x50EC8C`: `button`
  - `0x50EC94`: `O_Hire_Cutman`
  - `0x50ECA4`: `triggerExitAnimation`
  - `0x50ECBC`: `gMainScreen`
  - `0x50ECC8`: `T_pop_48`
  - `0x50ECD8`: `O_Ok`
  - `0x50ECE0`: `ContinueWithExit`
- Surrounding 128 bytes: `5f 52 75 6c 65 73 00 00 49 4e 46 4f 5f 4f 6e 6c 79 5f 52 65 66 00 00 00 4d 5f 33 5f 4b 6e 6f 63 6b 64 6f 77 6e 5f 52 75 6c 65 00 00 73 74 72 52 75 6c 65 73 00 00 00 00 62 75 74 74 6f 6e 00 00 4f 5f 48 69 72 65 5f 43 75 74 6d 61 6e 00 00 00 74 72 69 67 67 65 72 45 78 69 74 41 6e 69 6d 61 74 69 6f 6e 00 00 00 00 67 4d 61 69 6e 53 63 72 65 65 6e 00 54 5f 70 6f 70 5f 34 38 00 00 00 00`

## `BOOT.BIN` @ `0x50EE64`: `StartCareerInfo`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50ECC8`: `T_pop_48`
  - `0x50ECD8`: `O_Ok`
  - `0x50ECE0`: `ContinueWithExit`
  - `0x50EE50`: `GetHangGlovesInfo`
  - `0x50EE64`: `StartCareerInfo`
  - `0x50EE74`: `StartCareer`
  - `0x50EE80`: `IsMultiplayerFlow`
  - `0x50EE94`: `IsMultiPlayerFlow`
  - `0x50EEA8`: `strHangGlove`
  - `0x50EEB8`: `T_Hangs_Up_Gloves`
- Surrounding 128 bytes: `38 5c 20 00 38 5c 20 00 30 5c 20 00 58 5e 20 00 b8 5e 20 00 58 5e 20 00 58 5e 20 00 58 5e 20 00 58 5e 20 00 58 5e 20 00 88 5e 20 00 47 65 74 48 61 6e 67 47 6c 6f 76 65 73 49 6e 66 6f 00 00 00 53 74 61 72 74 43 61 72 65 65 72 49 6e 66 6f 00 53 74 61 72 74 43 61 72 65 65 72 00 49 73 4d 75 6c 74 69 70 6c 61 79 65 72 46 6c 6f 77 00 00 00 49 73 4d 75 6c 74 69 50 6c 61 79 65 72 46 6c 6f`

## `BOOT.BIN` @ `0x50EE74`: `StartCareer`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50ECD8`: `O_Ok`
  - `0x50ECE0`: `ContinueWithExit`
  - `0x50EE50`: `GetHangGlovesInfo`
  - `0x50EE64`: `StartCareerInfo`
  - `0x50EE74`: `StartCareer`
  - `0x50EE80`: `IsMultiplayerFlow`
  - `0x50EE94`: `IsMultiPlayerFlow`
  - `0x50EEA8`: `strHangGlove`
  - `0x50EEB8`: `T_Hangs_Up_Gloves`
  - `0x50EECC`: `strBoxerCRO`
- Surrounding 128 bytes: `b8 5e 20 00 58 5e 20 00 58 5e 20 00 58 5e 20 00 58 5e 20 00 58 5e 20 00 88 5e 20 00 47 65 74 48 61 6e 67 47 6c 6f 76 65 73 49 6e 66 6f 00 00 00 53 74 61 72 74 43 61 72 65 65 72 49 6e 66 6f 00 53 74 61 72 74 43 61 72 65 65 72 00 49 73 4d 75 6c 74 69 70 6c 61 79 65 72 46 6c 6f 77 00 00 00 49 73 4d 75 6c 74 69 50 6c 61 79 65 72 46 6c 6f 77 00 00 00 73 74 72 48 61 6e 67 47 6c 6f 76 65`

## `BOOT.BIN` @ `0x50EF00`: `iCareerStatus`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50EECC`: `strBoxerCRO`
  - `0x50EED8`: `strLeftCRO`
  - `0x50EEE4`: `strFirstName`
  - `0x50EEF4`: `strLastName`
  - `0x50EF00`: `iCareerStatus`
  - `0x50EF10`: `isMutltiplayer`
  - `0x50EF20`: `%s%s.loc`
  - `0x50EF2C`: `%s%s`
  - `0x50EF34`: `string.idx`
  - `0x50EF40`: `%d%c%03d%c%03d`
- Surrounding 128 bytes: `55 70 5f 47 6c 6f 76 65 73 00 00 00 73 74 72 42 6f 78 65 72 43 52 4f 00 73 74 72 4c 65 66 74 43 52 4f 00 00 73 74 72 46 69 72 73 74 4e 61 6d 65 00 00 00 00 73 74 72 4c 61 73 74 4e 61 6d 65 00 69 43 61 72 65 65 72 53 74 61 74 75 73 00 00 00 69 73 4d 75 74 6c 74 69 70 6c 61 79 65 72 00 00 25 73 25 73 2e 6c 6f 63 00 00 00 00 25 73 25 73 00 00 00 00 73 74 72 69 6e 67 2e 69 64 78 00 00`

## `BOOT.BIN` @ `0x50F048`: `strTotalPurse`
- Matched term(s): `purse`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x50EFE0`: `GetGameMode`
  - `0x50EFEC`: `iGameMode`
  - `0x50F020`: `GetEarningsDetailsInfo`
  - `0x50F038`: `out of memory`
  - `0x50F048`: `strTotalPurse`
  - `0x50F058`: `T_Total_Purse`
  - `0x50F068`: `strBoxerLastName1`
  - `0x50F07C`: `strBoxerLastName2`
  - `0x50F090`: `strBoxerPurseRate1`
  - `0x50F0A4`: `strBoxerAmount1`
- Surrounding 128 bytes: `3c 77 20 00 80 77 20 00 70 77 20 00 80 77 20 00 78 77 20 00 00 00 00 00 47 65 74 45 61 72 6e 69 6e 67 73 44 65 74 61 69 6c 73 49 6e 66 6f 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 73 74 72 54 6f 74 61 6c 50 75 72 73 65 00 00 00 54 5f 54 6f 74 61 6c 5f 50 75 72 73 65 00 00 00 73 74 72 42 6f 78 65 72 4c 61 73 74 4e 61 6d 65 31 00 00 00 73 74 72 42 6f 78 65 72 4c 61 73 74`

## `BOOT.BIN` @ `0x50F058`: `T_Total_Purse`
- Matched term(s): `purse`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x50EFEC`: `iGameMode`
  - `0x50F020`: `GetEarningsDetailsInfo`
  - `0x50F038`: `out of memory`
  - `0x50F048`: `strTotalPurse`
  - `0x50F058`: `T_Total_Purse`
  - `0x50F068`: `strBoxerLastName1`
  - `0x50F07C`: `strBoxerLastName2`
  - `0x50F090`: `strBoxerPurseRate1`
  - `0x50F0A4`: `strBoxerAmount1`
  - `0x50F0B4`: `strBoxerPurseRate2`
- Surrounding 128 bytes: `78 77 20 00 00 00 00 00 47 65 74 45 61 72 6e 69 6e 67 73 44 65 74 61 69 6c 73 49 6e 66 6f 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 73 74 72 54 6f 74 61 6c 50 75 72 73 65 00 00 00 54 5f 54 6f 74 61 6c 5f 50 75 72 73 65 00 00 00 73 74 72 42 6f 78 65 72 4c 61 73 74 4e 61 6d 65 31 00 00 00 73 74 72 42 6f 78 65 72 4c 61 73 74 4e 61 6d 65 32 00 00 00 73 74 72 42 6f 78 65 72`

## `BOOT.BIN` @ `0x50F090`: `strBoxerPurseRate1`
- Matched term(s): `purse`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x50F048`: `strTotalPurse`
  - `0x50F058`: `T_Total_Purse`
  - `0x50F068`: `strBoxerLastName1`
  - `0x50F07C`: `strBoxerLastName2`
  - `0x50F090`: `strBoxerPurseRate1`
  - `0x50F0A4`: `strBoxerAmount1`
  - `0x50F0B4`: `strBoxerPurseRate2`
  - `0x50F0C8`: `strBoxerAmount2`
  - `0x50F0D8`: `strPromoterRate`
  - `0x50F0E8`: `strPromoterAmount`
- Surrounding 128 bytes: `50 75 72 73 65 00 00 00 54 5f 54 6f 74 61 6c 5f 50 75 72 73 65 00 00 00 73 74 72 42 6f 78 65 72 4c 61 73 74 4e 61 6d 65 31 00 00 00 73 74 72 42 6f 78 65 72 4c 61 73 74 4e 61 6d 65 32 00 00 00 73 74 72 42 6f 78 65 72 50 75 72 73 65 52 61 74 65 31 00 00 73 74 72 42 6f 78 65 72 41 6d 6f 75 6e 74 31 00 73 74 72 42 6f 78 65 72 50 75 72 73 65 52 61 74 65 32 00 00 73 74 72 42 6f 78 65 72`

## `BOOT.BIN` @ `0x50F0B4`: `strBoxerPurseRate2`
- Matched term(s): `purse`
- Assessment: **meaningful**
- Why it matters: Career economy label; xrefs may lead to purse/money storage or UI formatting.
- Nearby printable strings:
  - `0x50F068`: `strBoxerLastName1`
  - `0x50F07C`: `strBoxerLastName2`
  - `0x50F090`: `strBoxerPurseRate1`
  - `0x50F0A4`: `strBoxerAmount1`
  - `0x50F0B4`: `strBoxerPurseRate2`
  - `0x50F0C8`: `strBoxerAmount2`
  - `0x50F0D8`: `strPromoterRate`
  - `0x50F0E8`: `strPromoterAmount`
  - `0x50F0FC`: `strTrainerRate`
  - `0x50F10C`: `strTrainerAmount`
- Surrounding 128 bytes: `4e 61 6d 65 31 00 00 00 73 74 72 42 6f 78 65 72 4c 61 73 74 4e 61 6d 65 32 00 00 00 73 74 72 42 6f 78 65 72 50 75 72 73 65 52 61 74 65 31 00 00 73 74 72 42 6f 78 65 72 41 6d 6f 75 6e 74 31 00 73 74 72 42 6f 78 65 72 50 75 72 73 65 52 61 74 65 32 00 00 73 74 72 42 6f 78 65 72 41 6d 6f 75 6e 74 32 00 73 74 72 50 72 6f 6d 6f 74 65 72 52 61 74 65 00 73 74 72 50 72 6f 6d 6f 74 65 72 41`

## `BOOT.BIN` @ `0x50F120`: `strCutmanRate`
- Matched term(s): `cutman`, `cut`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50F0D8`: `strPromoterRate`
  - `0x50F0E8`: `strPromoterAmount`
  - `0x50F0FC`: `strTrainerRate`
  - `0x50F10C`: `strTrainerAmount`
  - `0x50F120`: `strCutmanRate`
  - `0x50F130`: `strCutmanAmount`
  - `0x50F140`: `strEntranceMusicAmount`
  - `0x50F15C`: `strEntranceEffectsAmount`
  - `0x50F178`: `strEntourageAmount`
  - `0x50F18C`: `strTotalExpenses`
- Surrounding 128 bytes: `74 65 72 52 61 74 65 00 73 74 72 50 72 6f 6d 6f 74 65 72 41 6d 6f 75 6e 74 00 00 00 73 74 72 54 72 61 69 6e 65 72 52 61 74 65 00 00 73 74 72 54 72 61 69 6e 65 72 41 6d 6f 75 6e 74 00 00 00 00 73 74 72 43 75 74 6d 61 6e 52 61 74 65 00 00 00 73 74 72 43 75 74 6d 61 6e 41 6d 6f 75 6e 74 00 73 74 72 45 6e 74 72 61 6e 63 65 4d 75 73 69 63 41 6d 6f 75 6e 74 00 00 00 00 00 00 73 74 72 45`

## `BOOT.BIN` @ `0x50F130`: `strCutmanAmount`
- Matched term(s): `cutman`, `cut`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50F0E8`: `strPromoterAmount`
  - `0x50F0FC`: `strTrainerRate`
  - `0x50F10C`: `strTrainerAmount`
  - `0x50F120`: `strCutmanRate`
  - `0x50F130`: `strCutmanAmount`
  - `0x50F140`: `strEntranceMusicAmount`
  - `0x50F15C`: `strEntranceEffectsAmount`
  - `0x50F178`: `strEntourageAmount`
  - `0x50F18C`: `strTotalExpenses`
  - `0x50F1A0`: `strNetPay`
- Surrounding 128 bytes: `74 65 72 41 6d 6f 75 6e 74 00 00 00 73 74 72 54 72 61 69 6e 65 72 52 61 74 65 00 00 73 74 72 54 72 61 69 6e 65 72 41 6d 6f 75 6e 74 00 00 00 00 73 74 72 43 75 74 6d 61 6e 52 61 74 65 00 00 00 73 74 72 43 75 74 6d 61 6e 41 6d 6f 75 6e 74 00 73 74 72 45 6e 74 72 61 6e 63 65 4d 75 73 69 63 41 6d 6f 75 6e 74 00 00 00 00 00 00 73 74 72 45 6e 74 72 61 6e 63 65 45 66 66 65 63 74 73 41 6d`

## `BOOT.BIN` @ `0x50FB70`: `CareerStatus_ViewMatchup`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50FADC`: `L_we`
  - `0x50FAE4`: `L_li`
  - `0x50FAEC`: `L_fe`
  - `0x50FAF4`: `%s %s`
  - `0x50FB70`: `CareerStatus_ViewMatchup`
  - `0x50FB8C`: `iMatchup`
  - `0x50FB98`: `MinigameTutorial_Start`
  - `0x50FBB0`: `iTutorial`
  - `0x50FBBC`: `out of memory`
  - `0x50FBD0`: `AeoAnimation`
- Surrounding 128 bytes: `e0 d3 21 00 58 d6 21 00 58 d6 21 00 58 d6 21 00 58 d6 21 00 58 d6 21 00 58 d6 21 00 58 d6 21 00 58 d6 21 00 58 d6 21 00 e4 d4 21 00 a4 d5 21 00 fc d3 21 00 c4 d3 21 00 a8 d3 21 00 00 00 00 00 43 61 72 65 65 72 53 74 61 74 75 73 5f 56 69 65 77 4d 61 74 63 68 75 70 00 00 00 00 69 4d 61 74 63 68 75 70 00 00 00 00 4d 69 6e 69 67 61 6d 65 54 75 74 6f 72 69 61 6c 5f 53 74 61 72 74 00 00`

## `BOOT.BIN` @ `0x50FEC0`: `fnhud.hud`
- Matched term(s): `hud`, `fnhud`
- Assessment: **meaningful**
- Why it matters: UI/HUD/resource format label; useful for UI loader xrefs.
- Nearby printable strings:
  - `0x50FE84`: `basic_string`
  - `0x50FE94`: `out of memory`
  - `0x50FEA8`: `test text`
  - `0x50FEB4`: `fuihud`
  - `0x50FEC0`: `fnhud.hud`
  - `0x50FECC`: `blnk`
  - `0x50FF30`: `RETIREHANGGLOVES`
  - `0x50FF44`: `FIGHTHYPE7`
  - `0x50FF50`: `FIGHTHYPE0`
  - `0x50FF5C`: `FIGHTHYPE9`
- Surrounding 128 bytes: `25 73 00 00 62 61 73 69 63 5f 73 74 72 69 6e 67 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 74 65 73 74 20 74 65 78 74 00 00 00 66 75 69 68 75 64 00 00 2f 00 00 00 66 6e 68 75 64 2e 68 75 64 00 00 00 62 6c 6e 6b 00 00 00 00 00 00 00 00 60 d2 22 00 c8 d4 22 00 ec d1 22 00 2c d2 22 00 c8 d4 22 00 ac d1 22 00 c8 d4 22 00 c8 d4 22 00 c8 d4 22 00 c8 d4 22 00`

## `BOOT.BIN` @ `0x50FF88`: `CONFIRMCAREER`
- Matched term(s): `career`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x50FF50`: `FIGHTHYPE0`
  - `0x50FF5C`: `FIGHTHYPE9`
  - `0x50FF68`: `INTERNETMAINMENU`
  - `0x50FF7C`: `ADHOC_LOBBY`
  - `0x50FF88`: `CONFIRMCAREER`
  - `0x50FF98`: `MAINMENU`
  - `0x50FFA4`: `RIVALCHALLENGE`
  - `0x50FFB4`: `ClearPauseStateBE`
  - `0x50FFC8`: `_root`
  - `0x50FFD4`: `out of memory`
- Surrounding 128 bytes: `54 48 59 50 45 37 00 00 46 49 47 48 54 48 59 50 45 30 00 00 46 49 47 48 54 48 59 50 45 39 00 00 49 4e 54 45 52 4e 45 54 4d 41 49 4e 4d 45 4e 55 00 00 00 00 41 44 48 4f 43 5f 4c 4f 42 42 59 00 43 4f 4e 46 49 52 4d 43 41 52 45 45 52 00 00 00 4d 41 49 4e 4d 45 4e 55 00 00 00 00 52 49 56 41 4c 43 48 41 4c 4c 45 4e 47 45 00 00 43 6c 65 61 72 50 61 75 73 65 53 74 61 74 65 42 45 00 00 00`

## `BOOT.BIN` @ `0x510318`: `HT_Swelling`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x5102B4`: `UNKNOWN OVERLAY: %d`
  - `0x5102C8`: `S_%d`
  - `0x5102D4`: `%d%%`
  - `0x5102DC`: `%d %%`
  - `0x510318`: `HT_Swelling`
  - `0x510324`: `HT_Cuts`
  - `0x51032C`: `out of memory`
  - `0x510340`: `HT_Auto`
  - `0x510348`: `HT_Movement`
  - `0x510354`: `E:\muon\boxing\main\game\source\boxing\hud\fui\fuitccgame.cpp`
- Surrounding 128 bytes: `00 00 00 00 25 64 20 25 25 00 00 00 30 25 00 00 30 20 25 00 00 00 00 00 98 d7 23 00 18 d8 23 00 04 d9 23 00 f0 d9 23 00 d4 db 23 00 b8 dd 23 00 34 de 23 00 b0 de 23 00 2c df 23 00 00 00 00 00 48 54 5f 53 77 65 6c 6c 69 6e 67 00 48 54 5f 43 75 74 73 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 25 64 00 00 48 54 5f 41 75 74 6f 00 48 54 5f 4d 6f 76 65 6d 65 6e 74 00 45 3a 5c 6d`

## `BOOT.BIN` @ `0x510394`: `damageText`
- Matched term(s): `damage`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x51032C`: `out of memory`
  - `0x510340`: `HT_Auto`
  - `0x510348`: `HT_Movement`
  - `0x510354`: `E:\muon\boxing\main\game\source\boxing\hud\fui\fuitccgame.cpp`
  - `0x510394`: `damageText`
  - `0x5103A8`: `layout`
  - `0x5103B0`: `MinigameTutorial_End`
  - `0x5103C8`: `gMainScreen`
  - `0x5103D4`: `TL_Cutman_Tutorial`
  - `0x5103E8`: `INFO_Cutman_Tutorial_1`
- Surrounding 128 bytes: `45 3a 5c 6d 75 6f 6e 5c 62 6f 78 69 6e 67 5c 6d 61 69 6e 5c 67 61 6d 65 5c 73 6f 75 72 63 65 5c 62 6f 78 69 6e 67 5c 68 75 64 5c 66 75 69 5c 66 75 69 74 63 63 67 61 6d 65 2e 63 70 70 00 00 00 64 61 6d 61 67 65 54 65 78 74 00 00 58 58 00 00 00 00 00 00 6c 61 79 6f 75 74 00 00 4d 69 6e 69 67 61 6d 65 54 75 74 6f 72 69 61 6c 5f 45 6e 64 00 00 00 00 67 4d 61 69 6e 53 63 72 65 65 6e 00`

## `BOOT.BIN` @ `0x5103D4`: `TL_Cutman_Tutorial`
- Matched term(s): `cutman`, `cut`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x510394`: `damageText`
  - `0x5103A8`: `layout`
  - `0x5103B0`: `MinigameTutorial_End`
  - `0x5103C8`: `gMainScreen`
  - `0x5103D4`: `TL_Cutman_Tutorial`
  - `0x5103E8`: `INFO_Cutman_Tutorial_1`
  - `0x510400`: `INFO_Cutman_Tutorial_2`
  - `0x510418`: `INFO_Cutman_Tutorial_3`
  - `0x510430`: `INFO_Cutman_Tutorial_4`
  - `0x510448`: `INFO_Future_Reference`
- Surrounding 128 bytes: `64 61 6d 61 67 65 54 65 78 74 00 00 58 58 00 00 00 00 00 00 6c 61 79 6f 75 74 00 00 4d 69 6e 69 67 61 6d 65 54 75 74 6f 72 69 61 6c 5f 45 6e 64 00 00 00 00 67 4d 61 69 6e 53 63 72 65 65 6e 00 54 4c 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 31 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c`

## `BOOT.BIN` @ `0x5103E8`: `INFO_Cutman_Tutorial_1`
- Matched term(s): `cutman`, `cut`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x5103A8`: `layout`
  - `0x5103B0`: `MinigameTutorial_End`
  - `0x5103C8`: `gMainScreen`
  - `0x5103D4`: `TL_Cutman_Tutorial`
  - `0x5103E8`: `INFO_Cutman_Tutorial_1`
  - `0x510400`: `INFO_Cutman_Tutorial_2`
  - `0x510418`: `INFO_Cutman_Tutorial_3`
  - `0x510430`: `INFO_Cutman_Tutorial_4`
  - `0x510448`: `INFO_Future_Reference`
  - `0x510460`: `HT_Skip_Tutorial`
- Surrounding 128 bytes: `6c 61 79 6f 75 74 00 00 4d 69 6e 69 67 61 6d 65 54 75 74 6f 72 69 61 6c 5f 45 6e 64 00 00 00 00 67 4d 61 69 6e 53 63 72 65 65 6e 00 54 4c 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 31 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 32 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f`

## `BOOT.BIN` @ `0x510400`: `INFO_Cutman_Tutorial_2`
- Matched term(s): `cutman`, `cut`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x5103B0`: `MinigameTutorial_End`
  - `0x5103C8`: `gMainScreen`
  - `0x5103D4`: `TL_Cutman_Tutorial`
  - `0x5103E8`: `INFO_Cutman_Tutorial_1`
  - `0x510400`: `INFO_Cutman_Tutorial_2`
  - `0x510418`: `INFO_Cutman_Tutorial_3`
  - `0x510430`: `INFO_Cutman_Tutorial_4`
  - `0x510448`: `INFO_Future_Reference`
  - `0x510460`: `HT_Skip_Tutorial`
  - `0x510474`: `HT_Back`
- Surrounding 128 bytes: `5f 45 6e 64 00 00 00 00 67 4d 61 69 6e 53 63 72 65 65 6e 00 54 4c 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 31 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 32 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 33 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f`

## `BOOT.BIN` @ `0x510418`: `INFO_Cutman_Tutorial_3`
- Matched term(s): `cutman`, `cut`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x5103C8`: `gMainScreen`
  - `0x5103D4`: `TL_Cutman_Tutorial`
  - `0x5103E8`: `INFO_Cutman_Tutorial_1`
  - `0x510400`: `INFO_Cutman_Tutorial_2`
  - `0x510418`: `INFO_Cutman_Tutorial_3`
  - `0x510430`: `INFO_Cutman_Tutorial_4`
  - `0x510448`: `INFO_Future_Reference`
  - `0x510460`: `HT_Skip_Tutorial`
  - `0x510474`: `HT_Back`
  - `0x51047C`: `HT_Play`
- Surrounding 128 bytes: `75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 31 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 32 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 33 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 34 00 00 49 4e 46 4f 5f 46 75 74 75 72 65 5f 52 65 66 65`

## `BOOT.BIN` @ `0x510430`: `INFO_Cutman_Tutorial_4`
- Matched term(s): `cutman`, `cut`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x5103D4`: `TL_Cutman_Tutorial`
  - `0x5103E8`: `INFO_Cutman_Tutorial_1`
  - `0x510400`: `INFO_Cutman_Tutorial_2`
  - `0x510418`: `INFO_Cutman_Tutorial_3`
  - `0x510430`: `INFO_Cutman_Tutorial_4`
  - `0x510448`: `INFO_Future_Reference`
  - `0x510460`: `HT_Skip_Tutorial`
  - `0x510474`: `HT_Back`
  - `0x51047C`: `HT_Play`
  - `0x510484`: `HT_Continue`
- Surrounding 128 bytes: `6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 31 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 32 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 33 00 00 49 4e 46 4f 5f 43 75 74 6d 61 6e 5f 54 75 74 6f 72 69 61 6c 5f 34 00 00 49 4e 46 4f 5f 46 75 74 75 72 65 5f 52 65 66 65 72 65 6e 63 65 00 00 00 48 54 5f 53 6b 69 70 5f 54 75 74 6f 72 69 61 6c`

## `BOOT.BIN` @ `0x517CB0`: `FEAnim.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x517C28`: `Module %d not loaded. Sony Err: [%d]`
  - `0x517C50`: `Module %d unloaded successfully`
  - `0x517C74`: `Module %d not unloaded. Sony Err: [%d]`
  - `0x517CA0`: `out of memory`
  - `0x517CB0`: `FEAnim.viv`
  - `0x517CBC`: `BEAnim.viv`
  - `0x517CC8`: `out of memory`
  - `0x517CD8`: `audiocodec`
  - `0x517CE4`: `mpegbase`
  - `0x517CF0`: `sc_sascore`
- Surrounding 128 bytes: `00 00 00 00 4d 6f 64 75 6c 65 20 25 64 20 6e 6f 74 20 75 6e 6c 6f 61 64 65 64 2e 20 53 6f 6e 79 20 45 72 72 3a 20 5b 25 64 5d 0a 00 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 46 45 41 6e 69 6d 2e 76 69 76 00 00 42 45 41 6e 69 6d 2e 76 69 76 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 61 75 64 69 6f 63 6f 64 65 63 00 00 6d 70 65 67 62 61 73 65 00 00 00 00`

## `BOOT.BIN` @ `0x517CBC`: `BEAnim.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x517C50`: `Module %d unloaded successfully`
  - `0x517C74`: `Module %d not unloaded. Sony Err: [%d]`
  - `0x517CA0`: `out of memory`
  - `0x517CB0`: `FEAnim.viv`
  - `0x517CBC`: `BEAnim.viv`
  - `0x517CC8`: `out of memory`
  - `0x517CD8`: `audiocodec`
  - `0x517CE4`: `mpegbase`
  - `0x517CF0`: `sc_sascore`
  - `0x517CFC`: `videocodec`
- Surrounding 128 bytes: `64 20 6e 6f 74 20 75 6e 6c 6f 61 64 65 64 2e 20 53 6f 6e 79 20 45 72 72 3a 20 5b 25 64 5d 0a 00 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 46 45 41 6e 69 6d 2e 76 69 76 00 00 42 45 41 6e 69 6d 2e 76 69 76 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 61 75 64 69 6f 63 6f 64 65 63 00 00 6d 70 65 67 62 61 73 65 00 00 00 00 73 63 5f 73 61 73 63 6f 72 65 00 00`

## `BOOT.BIN` @ `0x51B080`: `tpage00.msh`
- Matched term(s): `msh`
- Assessment: **meaningful**
- Why it matters: Mesh/model extension string; xrefs can identify model/resource loading paths.
- Nearby printable strings:
  - `0x51B01C`: `fx_Smoke%i.fx_%02i.jdi`
  - `0x51B034`: `fx_Ground_fireworks%i.fx_%02i.jdi`
  - `0x51B058`: `fx_Fireballs%i.fx_%02i.jdi`
  - `0x51B078`: `.jdi`
  - `0x51B080`: `tpage00.msh`
  - `0x51B090`: `Fluids`
  - `0x51B0E8`: `%04x`
  - `0x51B0F0`: `EaVisVisColorCycler`
  - `0x51B104`: `bubbles`
  - `0x51B110`: `multilayertoptoplayer`
- Surrounding 128 bytes: `72 65 77 6f 72 6b 73 25 69 2e 66 78 5f 25 30 32 69 2e 6a 64 69 00 00 00 66 78 5f 46 69 72 65 62 61 6c 6c 73 25 69 2e 66 78 5f 25 30 32 69 2e 6a 64 69 00 00 66 78 5f 00 2e 6a 64 69 00 00 00 00 74 70 61 67 65 30 30 2e 6d 73 68 00 25 73 00 00 46 6c 75 69 64 73 00 00 c0 c2 28 00 c0 c2 28 00 c0 c2 28 00 88 c2 28 00 88 c2 28 00 88 c2 28 00 dc c2 28 00 dc c2 28 00 dc c2 28 00 a4 c2 28 00`

## `BOOT.BIN` @ `0x51BFFC`: `SWELLING_LEFT_EYE`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x51BFAC`: `BLOOD_RIGHT_MOUTH`
  - `0x51BFC0`: `BLOOD_RIGHT_NOSTRIL`
  - `0x51BFD4`: `BLOOD_LEFT_NOSTRIL`
  - `0x51BFE8`: `BLOOD_LEFT_MOUTH`
  - `0x51BFFC`: `SWELLING_LEFT_EYE`
  - `0x51C010`: `SWELLING_RIGHT_EYE`
  - `0x51C024`: `SWELLING_LEFT_JAW`
  - `0x51C038`: `SWELLING_RIGHT_JAW`
  - `0x51C04C`: `SWELLING_LEFT_NOSE`
  - `0x51C060`: `SWELLING_RIGHT_NOSE`
- Surrounding 128 bytes: `48 00 00 00 42 4c 4f 4f 44 5f 52 49 47 48 54 5f 4e 4f 53 54 52 49 4c 00 42 4c 4f 4f 44 5f 4c 45 46 54 5f 4e 4f 53 54 52 49 4c 00 00 42 4c 4f 4f 44 5f 4c 45 46 54 5f 4d 4f 55 54 48 00 00 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 45 59 45 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 45 59 45 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4a 41 57 00 00 00 53 57 45 4c`

## `BOOT.BIN` @ `0x51C010`: `SWELLING_RIGHT_EYE`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x51BFC0`: `BLOOD_RIGHT_NOSTRIL`
  - `0x51BFD4`: `BLOOD_LEFT_NOSTRIL`
  - `0x51BFE8`: `BLOOD_LEFT_MOUTH`
  - `0x51BFFC`: `SWELLING_LEFT_EYE`
  - `0x51C010`: `SWELLING_RIGHT_EYE`
  - `0x51C024`: `SWELLING_LEFT_JAW`
  - `0x51C038`: `SWELLING_RIGHT_JAW`
  - `0x51C04C`: `SWELLING_LEFT_NOSE`
  - `0x51C060`: `SWELLING_RIGHT_NOSE`
  - `0x51C074`: `SWELLING_LEFT_MOUTH`
- Surrounding 128 bytes: `52 49 4c 00 42 4c 4f 4f 44 5f 4c 45 46 54 5f 4e 4f 53 54 52 49 4c 00 00 42 4c 4f 4f 44 5f 4c 45 46 54 5f 4d 4f 55 54 48 00 00 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 45 59 45 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 45 59 45 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4a 41 57 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4a 41 57 00 00 53 57 45 4c`

## `BOOT.BIN` @ `0x51C024`: `SWELLING_LEFT_JAW`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x51BFD4`: `BLOOD_LEFT_NOSTRIL`
  - `0x51BFE8`: `BLOOD_LEFT_MOUTH`
  - `0x51BFFC`: `SWELLING_LEFT_EYE`
  - `0x51C010`: `SWELLING_RIGHT_EYE`
  - `0x51C024`: `SWELLING_LEFT_JAW`
  - `0x51C038`: `SWELLING_RIGHT_JAW`
  - `0x51C04C`: `SWELLING_LEFT_NOSE`
  - `0x51C060`: `SWELLING_RIGHT_NOSE`
  - `0x51C074`: `SWELLING_LEFT_MOUTH`
  - `0x51C088`: `SWELLING_RIGHT_MOUTH`
- Surrounding 128 bytes: `49 4c 00 00 42 4c 4f 4f 44 5f 4c 45 46 54 5f 4d 4f 55 54 48 00 00 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 45 59 45 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 45 59 45 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4a 41 57 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4a 41 57 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4e 4f 53 45 00 00 53 57 45 4c`

## `BOOT.BIN` @ `0x51C038`: `SWELLING_RIGHT_JAW`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x51BFE8`: `BLOOD_LEFT_MOUTH`
  - `0x51BFFC`: `SWELLING_LEFT_EYE`
  - `0x51C010`: `SWELLING_RIGHT_EYE`
  - `0x51C024`: `SWELLING_LEFT_JAW`
  - `0x51C038`: `SWELLING_RIGHT_JAW`
  - `0x51C04C`: `SWELLING_LEFT_NOSE`
  - `0x51C060`: `SWELLING_RIGHT_NOSE`
  - `0x51C074`: `SWELLING_LEFT_MOUTH`
  - `0x51C088`: `SWELLING_RIGHT_MOUTH`
  - `0x51C0A0`: `out of memory`
- Surrounding 128 bytes: `00 00 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 45 59 45 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 45 59 45 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4a 41 57 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4a 41 57 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4e 4f 53 45 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4e 4f 53 45 00 53 57 45 4c`

## `BOOT.BIN` @ `0x51C04C`: `SWELLING_LEFT_NOSE`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x51BFFC`: `SWELLING_LEFT_EYE`
  - `0x51C010`: `SWELLING_RIGHT_EYE`
  - `0x51C024`: `SWELLING_LEFT_JAW`
  - `0x51C038`: `SWELLING_RIGHT_JAW`
  - `0x51C04C`: `SWELLING_LEFT_NOSE`
  - `0x51C060`: `SWELLING_RIGHT_NOSE`
  - `0x51C074`: `SWELLING_LEFT_MOUTH`
  - `0x51C088`: `SWELLING_RIGHT_MOUTH`
  - `0x51C0A0`: `out of memory`
  - `0x51C170`: `tmp.out`
- Surrounding 128 bytes: `45 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 45 59 45 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4a 41 57 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4a 41 57 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4e 4f 53 45 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4e 4f 53 45 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4d 4f 55 54 48 00 53 57 45 4c`

## `BOOT.BIN` @ `0x51C060`: `SWELLING_RIGHT_NOSE`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x51C010`: `SWELLING_RIGHT_EYE`
  - `0x51C024`: `SWELLING_LEFT_JAW`
  - `0x51C038`: `SWELLING_RIGHT_JAW`
  - `0x51C04C`: `SWELLING_LEFT_NOSE`
  - `0x51C060`: `SWELLING_RIGHT_NOSE`
  - `0x51C074`: `SWELLING_LEFT_MOUTH`
  - `0x51C088`: `SWELLING_RIGHT_MOUTH`
  - `0x51C0A0`: `out of memory`
  - `0x51C170`: `tmp.out`
  - `0x51C178`: `AnimEdit`
- Surrounding 128 bytes: `59 45 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4a 41 57 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4a 41 57 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4e 4f 53 45 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4e 4f 53 45 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4d 4f 55 54 48 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4d 4f 55 54 48 00 00 00 00`

## `BOOT.BIN` @ `0x51C074`: `SWELLING_LEFT_MOUTH`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x51C024`: `SWELLING_LEFT_JAW`
  - `0x51C038`: `SWELLING_RIGHT_JAW`
  - `0x51C04C`: `SWELLING_LEFT_NOSE`
  - `0x51C060`: `SWELLING_RIGHT_NOSE`
  - `0x51C074`: `SWELLING_LEFT_MOUTH`
  - `0x51C088`: `SWELLING_RIGHT_MOUTH`
  - `0x51C0A0`: `out of memory`
  - `0x51C170`: `tmp.out`
  - `0x51C178`: `AnimEdit`
  - `0x51C184`: `Anim[%d] %s  %d of %d  `
- Surrounding 128 bytes: `57 00 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4a 41 57 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4e 4f 53 45 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4e 4f 53 45 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4d 4f 55 54 48 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4d 4f 55 54 48 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 5c cb 2a 00`

## `BOOT.BIN` @ `0x51C088`: `SWELLING_RIGHT_MOUTH`
- Matched term(s): `swelling`
- Assessment: **meaningful**
- Why it matters: Potential code/resource label; inspect xrefs before assigning semantics.
- Nearby printable strings:
  - `0x51C038`: `SWELLING_RIGHT_JAW`
  - `0x51C04C`: `SWELLING_LEFT_NOSE`
  - `0x51C060`: `SWELLING_RIGHT_NOSE`
  - `0x51C074`: `SWELLING_LEFT_MOUTH`
  - `0x51C088`: `SWELLING_RIGHT_MOUTH`
  - `0x51C0A0`: `out of memory`
  - `0x51C170`: `tmp.out`
  - `0x51C178`: `AnimEdit`
  - `0x51C184`: `Anim[%d] %s  %d of %d  `
  - `0x51C19C`: `FaceAnim[%d] %s  %d of %d  `
- Surrounding 128 bytes: `41 57 00 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4e 4f 53 45 00 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4e 4f 53 45 00 53 57 45 4c 4c 49 4e 47 5f 4c 45 46 54 5f 4d 4f 55 54 48 00 53 57 45 4c 4c 49 4e 47 5f 52 49 47 48 54 5f 4d 4f 55 54 48 00 00 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 5c cb 2a 00 5c cb 2a 00 78 cb 2a 00 78 cb 2a 00 24 cb 2a 00 24 cb 2a 00`

## `BOOT.BIN` @ `0x51C308`: `.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C2C4`: `dove_vertexanim`
  - `0x51C2D4`: `dove`
  - `0x51C2DC`: `%s_dove_vertexanim.sfx`
  - `0x51C2F4`: `out of memory`
  - `0x51C308`: `.viv`
  - `0x51C310`: `%s%s.viv`
  - `0x51C320`: `misc.viv`
  - `0x51C32C`: `boxersh.viv`
  - `0x51C338`: `actors.viv`
  - `0x51C344`: `cboxshr.viv`
- Surrounding 128 bytes: `5f 76 65 72 74 65 78 61 6e 69 6d 00 64 6f 76 65 00 00 00 00 25 73 5f 64 6f 76 65 5f 76 65 72 74 65 78 61 6e 69 6d 2e 73 66 78 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 2e 76 69 76 00 00 00 00 25 73 25 73 2e 76 69 76 00 00 00 00 2f 00 00 00 6d 69 73 63 2e 76 69 76 00 00 00 00 62 6f 78 65 72 73 68 2e 76 69 76 00 61 63 74 6f 72 73 2e 76 69 76 00 00 63 62 6f 78`

## `BOOT.BIN` @ `0x51C310`: `%s%s.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C2D4`: `dove`
  - `0x51C2DC`: `%s_dove_vertexanim.sfx`
  - `0x51C2F4`: `out of memory`
  - `0x51C308`: `.viv`
  - `0x51C310`: `%s%s.viv`
  - `0x51C320`: `misc.viv`
  - `0x51C32C`: `boxersh.viv`
  - `0x51C338`: `actors.viv`
  - `0x51C344`: `cboxshr.viv`
  - `0x51C350`: `boxerpre.viv`
- Surrounding 128 bytes: `6e 69 6d 00 64 6f 76 65 00 00 00 00 25 73 5f 64 6f 76 65 5f 76 65 72 74 65 78 61 6e 69 6d 2e 73 66 78 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 2e 76 69 76 00 00 00 00 25 73 25 73 2e 76 69 76 00 00 00 00 2f 00 00 00 6d 69 73 63 2e 76 69 76 00 00 00 00 62 6f 78 65 72 73 68 2e 76 69 76 00 61 63 74 6f 72 73 2e 76 69 76 00 00 63 62 6f 78 73 68 72 2e 76 69 76 00`

## `BOOT.BIN` @ `0x51C320`: `misc.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C2DC`: `%s_dove_vertexanim.sfx`
  - `0x51C2F4`: `out of memory`
  - `0x51C308`: `.viv`
  - `0x51C310`: `%s%s.viv`
  - `0x51C320`: `misc.viv`
  - `0x51C32C`: `boxersh.viv`
  - `0x51C338`: `actors.viv`
  - `0x51C344`: `cboxshr.viv`
  - `0x51C350`: `boxerpre.viv`
  - `0x51C360`: `allhair.viv`
- Surrounding 128 bytes: `6f 76 65 5f 76 65 72 74 65 78 61 6e 69 6d 2e 73 66 78 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 2e 76 69 76 00 00 00 00 25 73 25 73 2e 76 69 76 00 00 00 00 2f 00 00 00 6d 69 73 63 2e 76 69 76 00 00 00 00 62 6f 78 65 72 73 68 2e 76 69 76 00 61 63 74 6f 72 73 2e 76 69 76 00 00 63 62 6f 78 73 68 72 2e 76 69 76 00 62 6f 78 65 72 70 72 65 2e 76 69 76 00 00 00 00`

## `BOOT.BIN` @ `0x51C32C`: `boxersh.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C2F4`: `out of memory`
  - `0x51C308`: `.viv`
  - `0x51C310`: `%s%s.viv`
  - `0x51C320`: `misc.viv`
  - `0x51C32C`: `boxersh.viv`
  - `0x51C338`: `actors.viv`
  - `0x51C344`: `cboxshr.viv`
  - `0x51C350`: `boxerpre.viv`
  - `0x51C360`: `allhair.viv`
  - `0x51C36C`: `boxmisc.viv`
- Surrounding 128 bytes: `69 6d 2e 73 66 78 00 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 2e 76 69 76 00 00 00 00 25 73 25 73 2e 76 69 76 00 00 00 00 2f 00 00 00 6d 69 73 63 2e 76 69 76 00 00 00 00 62 6f 78 65 72 73 68 2e 76 69 76 00 61 63 74 6f 72 73 2e 76 69 76 00 00 63 62 6f 78 73 68 72 2e 76 69 76 00 62 6f 78 65 72 70 72 65 2e 76 69 76 00 00 00 00 61 6c 6c 68 61 69 72 2e 76 69 76 00`

## `BOOT.BIN` @ `0x51C338`: `actors.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C308`: `.viv`
  - `0x51C310`: `%s%s.viv`
  - `0x51C320`: `misc.viv`
  - `0x51C32C`: `boxersh.viv`
  - `0x51C338`: `actors.viv`
  - `0x51C344`: `cboxshr.viv`
  - `0x51C350`: `boxerpre.viv`
  - `0x51C360`: `allhair.viv`
  - `0x51C36C`: `boxmisc.viv`
  - `0x51C378`: `boxmisc2.viv`
- Surrounding 128 bytes: `6f 66 20 6d 65 6d 6f 72 79 0a 00 00 00 00 00 00 2e 76 69 76 00 00 00 00 25 73 25 73 2e 76 69 76 00 00 00 00 2f 00 00 00 6d 69 73 63 2e 76 69 76 00 00 00 00 62 6f 78 65 72 73 68 2e 76 69 76 00 61 63 74 6f 72 73 2e 76 69 76 00 00 63 62 6f 78 73 68 72 2e 76 69 76 00 62 6f 78 65 72 70 72 65 2e 76 69 76 00 00 00 00 61 6c 6c 68 61 69 72 2e 76 69 76 00 62 6f 78 6d 69 73 63 2e 76 69 76 00`

## `BOOT.BIN` @ `0x51C344`: `cboxshr.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C310`: `%s%s.viv`
  - `0x51C320`: `misc.viv`
  - `0x51C32C`: `boxersh.viv`
  - `0x51C338`: `actors.viv`
  - `0x51C344`: `cboxshr.viv`
  - `0x51C350`: `boxerpre.viv`
  - `0x51C360`: `allhair.viv`
  - `0x51C36C`: `boxmisc.viv`
  - `0x51C378`: `boxmisc2.viv`
  - `0x51C388`: `tables.viv`
- Surrounding 128 bytes: `00 00 00 00 2e 76 69 76 00 00 00 00 25 73 25 73 2e 76 69 76 00 00 00 00 2f 00 00 00 6d 69 73 63 2e 76 69 76 00 00 00 00 62 6f 78 65 72 73 68 2e 76 69 76 00 61 63 74 6f 72 73 2e 76 69 76 00 00 63 62 6f 78 73 68 72 2e 76 69 76 00 62 6f 78 65 72 70 72 65 2e 76 69 76 00 00 00 00 61 6c 6c 68 61 69 72 2e 76 69 76 00 62 6f 78 6d 69 73 63 2e 76 69 76 00 62 6f 78 6d 69 73 63 32 2e 76 69 76`

## `BOOT.BIN` @ `0x51C350`: `boxerpre.viv`
- Matched term(s): `boxerpre.viv`, `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C320`: `misc.viv`
  - `0x51C32C`: `boxersh.viv`
  - `0x51C338`: `actors.viv`
  - `0x51C344`: `cboxshr.viv`
  - `0x51C350`: `boxerpre.viv`
  - `0x51C360`: `allhair.viv`
  - `0x51C36C`: `boxmisc.viv`
  - `0x51C378`: `boxmisc2.viv`
  - `0x51C388`: `tables.viv`
  - `0x51C394`: `%s.ord`
- Surrounding 128 bytes: `25 73 25 73 2e 76 69 76 00 00 00 00 2f 00 00 00 6d 69 73 63 2e 76 69 76 00 00 00 00 62 6f 78 65 72 73 68 2e 76 69 76 00 61 63 74 6f 72 73 2e 76 69 76 00 00 63 62 6f 78 73 68 72 2e 76 69 76 00 62 6f 78 65 72 70 72 65 2e 76 69 76 00 00 00 00 61 6c 6c 68 61 69 72 2e 76 69 76 00 62 6f 78 6d 69 73 63 2e 76 69 76 00 62 6f 78 6d 69 73 63 32 2e 76 69 76 00 00 00 00 74 61 62 6c 65 73 2e 76`

## `BOOT.BIN` @ `0x51C360`: `allhair.viv`
- Matched term(s): `viv`, `AI`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C32C`: `boxersh.viv`
  - `0x51C338`: `actors.viv`
  - `0x51C344`: `cboxshr.viv`
  - `0x51C350`: `boxerpre.viv`
  - `0x51C360`: `allhair.viv`
  - `0x51C36C`: `boxmisc.viv`
  - `0x51C378`: `boxmisc2.viv`
  - `0x51C388`: `tables.viv`
  - `0x51C394`: `%s.ord`
  - `0x51C39C`: `%s.orl`
- Surrounding 128 bytes: `6d 69 73 63 2e 76 69 76 00 00 00 00 62 6f 78 65 72 73 68 2e 76 69 76 00 61 63 74 6f 72 73 2e 76 69 76 00 00 63 62 6f 78 73 68 72 2e 76 69 76 00 62 6f 78 65 72 70 72 65 2e 76 69 76 00 00 00 00 61 6c 6c 68 61 69 72 2e 76 69 76 00 62 6f 78 6d 69 73 63 2e 76 69 76 00 62 6f 78 6d 69 73 63 32 2e 76 69 76 00 00 00 00 74 61 62 6c 65 73 2e 76 69 76 00 00 25 73 2e 6f 72 64 00 00 25 73 2e 6f`

## `BOOT.BIN` @ `0x51C36C`: `boxmisc.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C338`: `actors.viv`
  - `0x51C344`: `cboxshr.viv`
  - `0x51C350`: `boxerpre.viv`
  - `0x51C360`: `allhair.viv`
  - `0x51C36C`: `boxmisc.viv`
  - `0x51C378`: `boxmisc2.viv`
  - `0x51C388`: `tables.viv`
  - `0x51C394`: `%s.ord`
  - `0x51C39C`: `%s.orl`
  - `0x51C3A4`: `%s.o`
- Surrounding 128 bytes: `62 6f 78 65 72 73 68 2e 76 69 76 00 61 63 74 6f 72 73 2e 76 69 76 00 00 63 62 6f 78 73 68 72 2e 76 69 76 00 62 6f 78 65 72 70 72 65 2e 76 69 76 00 00 00 00 61 6c 6c 68 61 69 72 2e 76 69 76 00 62 6f 78 6d 69 73 63 2e 76 69 76 00 62 6f 78 6d 69 73 63 32 2e 76 69 76 00 00 00 00 74 61 62 6c 65 73 2e 76 69 76 00 00 25 73 2e 6f 72 64 00 00 25 73 2e 6f 72 6c 00 00 25 73 2e 6f 00 00 00 00`

## `BOOT.BIN` @ `0x51C378`: `boxmisc2.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C344`: `cboxshr.viv`
  - `0x51C350`: `boxerpre.viv`
  - `0x51C360`: `allhair.viv`
  - `0x51C36C`: `boxmisc.viv`
  - `0x51C378`: `boxmisc2.viv`
  - `0x51C388`: `tables.viv`
  - `0x51C394`: `%s.ord`
  - `0x51C39C`: `%s.orl`
  - `0x51C3A4`: `%s.o`
  - `0x51C3AC`: `%s%s`
- Surrounding 128 bytes: `61 63 74 6f 72 73 2e 76 69 76 00 00 63 62 6f 78 73 68 72 2e 76 69 76 00 62 6f 78 65 72 70 72 65 2e 76 69 76 00 00 00 00 61 6c 6c 68 61 69 72 2e 76 69 76 00 62 6f 78 6d 69 73 63 2e 76 69 76 00 62 6f 78 6d 69 73 63 32 2e 76 69 76 00 00 00 00 74 61 62 6c 65 73 2e 76 69 76 00 00 25 73 2e 6f 72 64 00 00 25 73 2e 6f 72 6c 00 00 25 73 2e 6f 00 00 00 00 25 73 25 73 00 00 00 00 2e 6d 73 68`

## `BOOT.BIN` @ `0x51C388`: `tables.viv`
- Matched term(s): `tables`, `tables.viv`, `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51C350`: `boxerpre.viv`
  - `0x51C360`: `allhair.viv`
  - `0x51C36C`: `boxmisc.viv`
  - `0x51C378`: `boxmisc2.viv`
  - `0x51C388`: `tables.viv`
  - `0x51C394`: `%s.ord`
  - `0x51C39C`: `%s.orl`
  - `0x51C3A4`: `%s.o`
  - `0x51C3AC`: `%s%s`
  - `0x51C3B4`: `.msh`
- Surrounding 128 bytes: `73 68 72 2e 76 69 76 00 62 6f 78 65 72 70 72 65 2e 76 69 76 00 00 00 00 61 6c 6c 68 61 69 72 2e 76 69 76 00 62 6f 78 6d 69 73 63 2e 76 69 76 00 62 6f 78 6d 69 73 63 32 2e 76 69 76 00 00 00 00 74 61 62 6c 65 73 2e 76 69 76 00 00 25 73 2e 6f 72 64 00 00 25 73 2e 6f 72 6c 00 00 25 73 2e 6f 00 00 00 00 25 73 25 73 00 00 00 00 2e 6d 73 68 00 00 00 00 6e 6f 6e 65 00 00 00 00 00 00 00 00`

## `BOOT.BIN` @ `0x51C9D0`: `damage_%d`
- Matched term(s): `damage`
- Assessment: **meaningful**
- Why it matters: Gameplay damage modifier/label; useful for locating combat calculation or perk/modifier code.
- Nearby printable strings:
  - `0x51C98C`: `mor_base_shoes_%s.o`
  - `0x51C9A0`: `mor_base_head_hair_%s.o`
  - `0x51C9B8`: `trh_%s.bin`
  - `0x51C9C4`: `trb_0.bin`
  - `0x51C9D0`: `damage_%d`
  - `0x51C9DC`: `hdbd`
  - `0x51C9E4`: `bhbx`
  - `0x51C9EC`: `hd2d`
  - `0x51C9F4`: `shbx`
  - `0x51C9FC`: `bdbd`
- Surrounding 128 bytes: `62 61 73 65 5f 73 68 6f 65 73 5f 25 73 2e 6f 00 6d 6f 72 5f 62 61 73 65 5f 68 65 61 64 5f 68 61 69 72 5f 25 73 2e 6f 00 74 72 68 5f 25 73 2e 62 69 6e 00 00 74 72 62 5f 30 2e 62 69 6e 00 00 00 64 61 6d 61 67 65 5f 25 64 00 00 00 68 64 62 64 00 00 00 00 62 68 62 78 00 00 00 00 68 64 32 64 00 00 00 00 73 68 62 78 00 00 00 00 62 64 62 64 00 00 00 00 62 62 62 78 00 00 00 00 62 64 32 64`

## `BOOT.BIN` @ `0x51D680`: `%s\%s.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51D650`: `_ingame_2DCrowd`
  - `0x51D660`: `sparrin`
  - `0x51D668`: `trainin`
  - `0x51D670`: `out of memory`
  - `0x51D680`: `%s\%s.viv`
  - `0x51D68C`: `%s\%s.zlb`
  - `0x51D698`: `%s\%sz.viv`
  - `0x51D6A4`: `%s\%st.viv`
  - `0x51D6B0`: `%s\%st.zlb`
  - `0x51D6BC`: `%s_entrance_particles.big`
- Surrounding 128 bytes: `64 5f 70 6c 61 63 65 6d 65 6e 74 2e 73 66 78 00 5f 69 6e 67 61 6d 65 5f 32 44 43 72 6f 77 64 00 73 70 61 72 72 69 6e 00 74 72 61 69 6e 69 6e 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 25 73 5c 25 73 2e 76 69 76 00 00 00 25 73 5c 25 73 2e 7a 6c 62 00 00 00 25 73 5c 25 73 7a 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 7a 6c 62 00 00 25 73 5f 65`

## `BOOT.BIN` @ `0x51D68C`: `%s\%s.zlb`
- Matched term(s): `zlb`
- Assessment: **meaningful**
- Why it matters: ZLB package path/string; likely compressed package/resource reference to trace through loader xrefs.
- Nearby printable strings:
  - `0x51D660`: `sparrin`
  - `0x51D668`: `trainin`
  - `0x51D670`: `out of memory`
  - `0x51D680`: `%s\%s.viv`
  - `0x51D68C`: `%s\%s.zlb`
  - `0x51D698`: `%s\%sz.viv`
  - `0x51D6A4`: `%s\%st.viv`
  - `0x51D6B0`: `%s\%st.zlb`
  - `0x51D6BC`: `%s_entrance_particles.big`
  - `0x51D6D8`: `%s_particles.big`
- Surrounding 128 bytes: `73 66 78 00 5f 69 6e 67 61 6d 65 5f 32 44 43 72 6f 77 64 00 73 70 61 72 72 69 6e 00 74 72 61 69 6e 69 6e 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 25 73 5c 25 73 2e 76 69 76 00 00 00 25 73 5c 25 73 2e 7a 6c 62 00 00 00 25 73 5c 25 73 7a 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 7a 6c 62 00 00 25 73 5f 65 6e 74 72 61 6e 63 65 5f 70 61 72 74`

## `BOOT.BIN` @ `0x51D698`: `%s\%sz.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51D668`: `trainin`
  - `0x51D670`: `out of memory`
  - `0x51D680`: `%s\%s.viv`
  - `0x51D68C`: `%s\%s.zlb`
  - `0x51D698`: `%s\%sz.viv`
  - `0x51D6A4`: `%s\%st.viv`
  - `0x51D6B0`: `%s\%st.zlb`
  - `0x51D6BC`: `%s_entrance_particles.big`
  - `0x51D6D8`: `%s_particles.big`
  - `0x51D6EC`: `%s_skybox`
- Surrounding 128 bytes: `32 44 43 72 6f 77 64 00 73 70 61 72 72 69 6e 00 74 72 61 69 6e 69 6e 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 25 73 5c 25 73 2e 76 69 76 00 00 00 25 73 5c 25 73 2e 7a 6c 62 00 00 00 25 73 5c 25 73 7a 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 7a 6c 62 00 00 25 73 5f 65 6e 74 72 61 6e 63 65 5f 70 61 72 74 69 63 6c 65 73 2e 62 69 67 00 00 00`

## `BOOT.BIN` @ `0x51D6A4`: `%s\%st.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51D670`: `out of memory`
  - `0x51D680`: `%s\%s.viv`
  - `0x51D68C`: `%s\%s.zlb`
  - `0x51D698`: `%s\%sz.viv`
  - `0x51D6A4`: `%s\%st.viv`
  - `0x51D6B0`: `%s\%st.zlb`
  - `0x51D6BC`: `%s_entrance_particles.big`
  - `0x51D6D8`: `%s_particles.big`
  - `0x51D6EC`: `%s_skybox`
  - `0x51D6F8`: `%s_locked`
- Surrounding 128 bytes: `72 69 6e 00 74 72 61 69 6e 69 6e 00 6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 25 73 5c 25 73 2e 76 69 76 00 00 00 25 73 5c 25 73 2e 7a 6c 62 00 00 00 25 73 5c 25 73 7a 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 7a 6c 62 00 00 25 73 5f 65 6e 74 72 61 6e 63 65 5f 70 61 72 74 69 63 6c 65 73 2e 62 69 67 00 00 00 25 73 5f 70 61 72 74 69 63 6c 65 73`

## `BOOT.BIN` @ `0x51D6B0`: `%s\%st.zlb`
- Matched term(s): `zlb`
- Assessment: **meaningful**
- Why it matters: ZLB package path/string; likely compressed package/resource reference to trace through loader xrefs.
- Nearby printable strings:
  - `0x51D680`: `%s\%s.viv`
  - `0x51D68C`: `%s\%s.zlb`
  - `0x51D698`: `%s\%sz.viv`
  - `0x51D6A4`: `%s\%st.viv`
  - `0x51D6B0`: `%s\%st.zlb`
  - `0x51D6BC`: `%s_entrance_particles.big`
  - `0x51D6D8`: `%s_particles.big`
  - `0x51D6EC`: `%s_skybox`
  - `0x51D6F8`: `%s_locked`
  - `0x51D704`: `%s_unlocked`
- Surrounding 128 bytes: `6f 75 74 20 6f 66 20 6d 65 6d 6f 72 79 0a 00 00 25 73 5c 25 73 2e 76 69 76 00 00 00 25 73 5c 25 73 2e 7a 6c 62 00 00 00 25 73 5c 25 73 7a 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 7a 6c 62 00 00 25 73 5f 65 6e 74 72 61 6e 63 65 5f 70 61 72 74 69 63 6c 65 73 2e 62 69 67 00 00 00 25 73 5f 70 61 72 74 69 63 6c 65 73 2e 62 69 67 00 00 00 00 25 73 5f 73`

## `BOOT.BIN` @ `0x51D6BC`: `%s_entrance_particles.big`
- Matched term(s): `big`
- Assessment: **meaningful**
- Why it matters: BIG archive/file-loader string; xrefs can identify archive/resource mounting code.
- Nearby printable strings:
  - `0x51D68C`: `%s\%s.zlb`
  - `0x51D698`: `%s\%sz.viv`
  - `0x51D6A4`: `%s\%st.viv`
  - `0x51D6B0`: `%s\%st.zlb`
  - `0x51D6BC`: `%s_entrance_particles.big`
  - `0x51D6D8`: `%s_particles.big`
  - `0x51D6EC`: `%s_skybox`
  - `0x51D6F8`: `%s_locked`
  - `0x51D704`: `%s_unlocked`
  - `0x51D710`: `%s_lockable`
- Surrounding 128 bytes: `79 0a 00 00 25 73 5c 25 73 2e 76 69 76 00 00 00 25 73 5c 25 73 2e 7a 6c 62 00 00 00 25 73 5c 25 73 7a 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 7a 6c 62 00 00 25 73 5f 65 6e 74 72 61 6e 63 65 5f 70 61 72 74 69 63 6c 65 73 2e 62 69 67 00 00 00 25 73 5f 70 61 72 74 69 63 6c 65 73 2e 62 69 67 00 00 00 00 25 73 5f 73 6b 79 62 6f 78 00 00 00 25 73 5f 6c`

## `BOOT.BIN` @ `0x51D6D8`: `%s_particles.big`
- Matched term(s): `big`
- Assessment: **meaningful**
- Why it matters: BIG archive/file-loader string; xrefs can identify archive/resource mounting code.
- Nearby printable strings:
  - `0x51D698`: `%s\%sz.viv`
  - `0x51D6A4`: `%s\%st.viv`
  - `0x51D6B0`: `%s\%st.zlb`
  - `0x51D6BC`: `%s_entrance_particles.big`
  - `0x51D6D8`: `%s_particles.big`
  - `0x51D6EC`: `%s_skybox`
  - `0x51D6F8`: `%s_locked`
  - `0x51D704`: `%s_unlocked`
  - `0x51D710`: `%s_lockable`
  - `0x51D71C`: `%s_alpha2`
- Surrounding 128 bytes: `25 73 5c 25 73 7a 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 76 69 76 00 00 25 73 5c 25 73 74 2e 7a 6c 62 00 00 25 73 5f 65 6e 74 72 61 6e 63 65 5f 70 61 72 74 69 63 6c 65 73 2e 62 69 67 00 00 00 25 73 5f 70 61 72 74 69 63 6c 65 73 2e 62 69 67 00 00 00 00 25 73 5f 73 6b 79 62 6f 78 00 00 00 25 73 5f 6c 6f 63 6b 65 64 00 00 00 25 73 5f 75 6e 6c 6f 63 6b 65 64 00 25 73 5f 6c 6f 63 6b 61`

## `BOOT.BIN` @ `0x51D780`: `training`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x51D740`: `jmbo`
  - `0x51D748`: `%s%i_placement.txt`
  - `0x51D75C`: `%s%i_vertexanim`
  - `0x51D76C`: `%s%i_placement.sfx`
  - `0x51D780`: `training`
  - `0x51D78C`: `entrance`
  - `0x51D798`: `%s_%s_3DCrowd_placement.txt`
  - `0x51D7B4`: `%s_%s_3DCrowd_placement.sfx`
  - `0x51D7D0`: `_%s_2DCrowd`
  - `0x51D7DC`: `%s_spec`
- Surrounding 128 bytes: `6a 6d 62 6f 00 00 00 00 25 73 25 69 5f 70 6c 61 63 65 6d 65 6e 74 2e 74 78 74 00 00 25 73 25 69 5f 76 65 72 74 65 78 61 6e 69 6d 00 25 73 25 69 5f 70 6c 61 63 65 6d 65 6e 74 2e 73 66 78 00 00 74 72 61 69 6e 69 6e 67 00 00 00 00 65 6e 74 72 61 6e 63 65 00 00 00 00 25 73 5f 25 73 5f 33 44 43 72 6f 77 64 5f 70 6c 61 63 65 6d 65 6e 74 2e 74 78 74 00 25 73 5f 25 73 5f 33 44 43 72 6f 77`

## `BOOT.BIN` @ `0x51EA2C`: `ScrAnim.viv`
- Matched term(s): `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51E988`: `addanims`
  - `0x51E9E8`: `out of memory`
  - `0x51E9F8`: `.bin`
  - `0x51EA00`: `SCRIPT ERROR: UNABLE TO LOAD SCRIPT BANK`
  - `0x51EA2C`: `ScrAnim.viv`
  - `0x51EA38`: `SCRIPT ERROR: INVALID VERSION - CANNOT PLAY`
  - `0x51EA68`: `Script Code Version - %d`
  - `0x51EA84`: `Script Data Version - %d`
  - `0x51EAA0`: `Script Start. Num Sequences %d`
  - `0x51EAC0`: `StartPlay...`
- Surrounding 128 bytes: `6f 66 20 6d 65 6d 6f 72 79 0a 00 00 2e 62 69 6e 00 00 00 00 53 43 52 49 50 54 20 45 52 52 4f 52 3a 20 55 4e 41 42 4c 45 20 54 4f 20 4c 4f 41 44 20 53 43 52 49 50 54 20 42 41 4e 4b 0a 00 00 00 53 63 72 41 6e 69 6d 2e 76 69 76 00 53 43 52 49 50 54 20 45 52 52 4f 52 3a 20 49 4e 56 41 4c 49 44 20 56 45 52 53 49 4f 4e 20 2d 20 43 41 4e 4e 4f 54 20 50 4c 41 59 0a 00 00 00 00 53 63 72 69`

## `BOOT.BIN` @ `0x51EC04`: `bootpreloads.viv`
- Matched term(s): `bootpreloads.viv`, `viv`
- Assessment: **meaningful**
- Why it matters: Named archive path/string; search xrefs to find archive loading or preload setup.
- Nearby printable strings:
  - `0x51EAD0`: `EndPlay... starting next script in queue`
  - `0x51EAFC`: `EndPlay...`
  - `0x51EB08`: `actor`
  - `0x51EB10`: `out of memory`
  - `0x51EC04`: `bootpreloads.viv`
  - `0x51EC1C`: `%s.bh`
  - `0x51EC28`: `Header :: %s`
  - `0x51EC38`: `%s@%d: %s`
  - `0x51EC48`: `anim`
  - `0x51EC50`: `audio/AEMS`
- Surrounding 128 bytes: `c0 92 33 00 d0 90 33 00 40 91 33 00 70 91 33 00 9c 91 33 00 a4 91 33 00 d4 91 33 00 dc 91 33 00 0c 92 33 00 14 92 33 00 64 92 33 00 6c 92 33 00 9c 92 33 00 c0 92 33 00 00 00 00 00 2f 00 00 00 62 6f 6f 74 70 72 65 6c 6f 61 64 73 2e 76 69 76 00 00 00 00 61 62 63 00 25 73 2e 62 68 00 00 00 62 68 00 00 48 65 61 64 65 72 20 3a 3a 20 25 73 00 00 00 00 25 73 40 25 64 3a 20 25 73 00 00 00`

## `BOOT.BIN` @ `0x5254D8`: `%s%s.big`
- Matched term(s): `big`
- Assessment: **meaningful**
- Why it matters: BIG archive/file-loader string; xrefs can identify archive/resource mounting code.
- Nearby printable strings:
  - `0x525464`: `Matrix::%d::TextureMatrix`
  - `0x525484`: `external command: %s('%s')`
  - `0x5254A0`: `getBytesTotal - '%s' '%d`
  - `0x5254BC`: `strlen(szFileName) < 250`
  - `0x5254D8`: `%s%s.big`
  - `0x5254E4`: `getBytesLoaded - '%s' '%d`
  - `0x525500`: `sendVariables : '%s' at target '%s ----%s ----%s '`
  - `0x525534`: `loadVariables: called with NULL parameters`
  - `0x525564`: `couldn't loadVariables '%s'`
  - `0x525584`: `in_apt`
- Surrounding 128 bytes: `28 27 25 73 27 29 0a 00 67 65 74 42 79 74 65 73 54 6f 74 61 6c 20 2d 20 27 25 73 27 20 27 25 64 0a 00 00 00 73 74 72 6c 65 6e 28 73 7a 46 69 6c 65 4e 61 6d 65 29 20 3c 20 32 35 30 00 00 00 00 25 73 25 73 2e 62 69 67 00 00 00 00 67 65 74 42 79 74 65 73 4c 6f 61 64 65 64 20 2d 20 27 25 73 27 20 27 25 64 0a 00 00 73 65 6e 64 56 61 72 69 61 62 6c 65 73 20 3a 20 27 25 73 27 20 61 74 20`

## `BOOT.BIN` @ `0x52582C`: `.apt`
- Matched term(s): `apt`
- Assessment: **meaningful**
- Why it matters: APT UI/resource string; xrefs can identify UI load/render functions.
- Nearby printable strings:
  - `0x5257D4`: `g_pfnAptAuxAlloc`
  - `0x5257E8`: `ppAptData`
  - `0x5257F4`: `ppConstData`
  - `0x525800`: `i < pCurrentAptAuxParams->iLevelInfoSize`
  - `0x52582C`: `.apt`
  - `0x525834`: `.const`
  - `0x52583C`: `couldn't load '%s'!`
  - `0x525854`: `GUI::%s`
  - `0x52585C`: `pData != NULL`
  - `0x52586C`: `AptFontTextureMemoryPool`
- Surrounding 128 bytes: `74 44 61 74 61 00 00 00 70 70 43 6f 6e 73 74 44 61 74 61 00 69 20 3c 20 70 43 75 72 72 65 6e 74 41 70 74 41 75 78 50 61 72 61 6d 73 2d 3e 69 4c 65 76 65 6c 49 6e 66 6f 53 69 7a 65 00 00 00 00 2e 61 70 74 00 00 00 00 2e 63 6f 6e 73 74 00 00 63 6f 75 6c 64 6e 27 74 20 6c 6f 61 64 20 27 25 73 27 21 0a 00 00 00 00 47 55 49 3a 3a 25 73 00 70 44 61 74 61 20 21 3d 20 4e 55 4c 4c 00 00 00`

## `BOOT.BIN` @ `0x53A704`: `TRAINING SPARRING`
- Matched term(s): `AI`, `training`
- Assessment: **meaningful**
- Why it matters: Training/trainer label; may lead to career training scripts or results.
- Nearby printable strings:
  - `0x53A314`: `SLUG - STALKER`
  - `0x53A464`: `SPEED - AGGRO STICK/MOVE`
  - `0x53A50C`: `SPEED - EVADE STICK/MOVE`
  - `0x53A5B4`: `SPEED - JAB EVADE STICK/MOVE`
  - `0x53A704`: `TRAINING SPARRING`
  - `0x53A854`: `TEST`
  - `0x53A8FC`: `SPEED - ALI`
  - `0x53CEB4`: `33s@`
  - `0x53CEDE`: `@?33`
  - `0x53CEEC`: `ff6@`
- Surrounding 128 bytes: `00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 05 00 00 00 03 00 00 00 03 00 00 00 03 00 00 00 03 00 00 00 03 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 54 52 41 49 4e 49 4e 47 20 53 50 41 52 52 49 4e 47 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ff ff ff ff 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00`

## `EBOOT.BIN` @ `0x523B7D`: `hud`
- Matched term(s): `hud`
- Assessment: **likely noise**
- Why it matters: Short token appears in encrypted/high-entropy EBOOT payload without domain-readable context; use decrypted BOOT.BIN instead.
- Nearby printable strings:
  - `0x52392B`: `0>B<`
  - `0x5239BB`: `n\PQ`
  - `0x5239D6`: `ezqd`
  - `0x5239F9`: `whIa`
  - `0x523AED`: `Z; 7F`
  - `0x523B96`: `z9C-`
  - `0x523BAA`: `"nd `
  - `0x523BD6`: `i;_r`
  - `0x523C3E`: `nDdR`
  - `0x523C48`: `<p=y`
- Surrounding 128 bytes: `90 f6 19 5a d6 67 0b 0c 6d bc f2 f1 ed 88 f6 1b e2 06 43 8f ba a9 69 4d 58 ee 0d 27 9b af 4a a0 24 28 33 99 a5 a6 a7 cc 77 1b 7a c8 aa 9a 01 99 b1 ca 49 20 30 87 4e f7 bb de 86 58 c6 1e a9 94 48 75 64 a6 01 d3 bf 85 a8 68 93 96 3c 51 e0 a7 6e d4 d8 cb 8b 33 a2 4b af 7a 39 43 2d 11 5c 29 40 df 81 82 82 c0 bf d2 9b d3 80 2f fd 22 6e 64 20 da 59 6d 22 19 2d 01 cf 2b 38 28 0c 7e c0 84`

## EBOOT.BIN diagnostic short-token hits

These are included to show that apparent short matches exist but are not actionable without decrypting/unpacking EBOOT.

- `0x5C257E` `CUt+` matched ['cut']: **likely noise: hit is inside high-entropy PSP container; no readable domain context**. Surrounding 128 bytes: `c2 99 6a 20 ae 42 f8 84 c7 f5 d8 81 f5 2f 07 84 cc 78 5d ec 8e 0a 1f 16 31 71 33 74 74 23 3f c7 d9 e8 61 ea 4e ef 2f d9 05 88 75 e6 ae 04 72 d5 74 52 78 43 4d 23 35 35 d3 ec bc 9a 8d 29 71 e3 43 55 74 2b 00 df 96 63 18 6f 56 55 ae 31 da 0c 3a 23 4e 64 a1 87 db 6f 51 dd 31 fe 44 3f af 9c 6f 62 d6 7a da ba 39 d3 0a c0 44 e3 34 20 75 97 2c 8e af e1 30 45 d3 a9 4d 94 59 b8 a5 3d 7e e6`
- `0x3DAD8` `ZLbh` matched ['zlb']: **likely noise**. Surrounding 128 bytes: `a8 3e 6a 85 0b 78 7f dc 70 12 ca 51 a5 32 5d 94 09 83 1d cf a0 31 4b 61 bd d4 3e 66 82 22 fb c0 04 6d 91 26 af ad a9 f6 26 c9 e7 cf ed 49 ca 20 58 69 49 e2 36 d3 f9 31 a9 35 01 c0 d2 c3 00 ad 5a 4c 62 68 1e 76 93 79 f7 7a 10 a6 1f df d9 19 8e 3d e6 f3 af 28 6c 93 0a ee a6 f4 10 e3 34 b5 d2 46 6a c4 77 34 57 d4 4a 1c a2 fb 17 23 cc 14 ee 8f d2 89 52 e0 6c 4d d0 4b 35 fc a2 c5 a9 69`
- `0x61AEF2` `[jbig` matched ['big']: **likely noise**. Surrounding 128 bytes: `de a4 5b 3f 6f 68 3e 67 56 8e d2 71 e9 4e 80 01 fe 77 ef 86 62 51 ef 84 59 a4 98 5b cc 2e 3b 5a 6b 60 4f 15 97 fb 70 0b 4e 8b 96 c0 85 95 a2 9c d7 ad da 05 b4 96 ea d9 c9 51 8b 8c 0b 89 5b 6a 62 69 67 b4 61 fc d2 85 e3 a9 0b 9c 47 06 6f c6 71 34 ae bb 9a ab 15 3b e9 4f 66 bf 7b 85 2d e0 e2 0b 3a 86 00 96 a5 c0 5d 4c c9 86 c0 99 b4 4f 4c 90 de 02 e0 5c 8e 69 bd 4c a9 f8 18 cc 49 79`
- `0x2738AE` `viv` matched ['viv']: **likely noise**. Surrounding 128 bytes: `03 59 b3 bf 36 7b 7c 65 1a 3f 7c 5e 15 32 2e a0 62 d8 aa 51 df 18 3d d9 a9 e4 db 03 ad 50 20 f3 8d e5 bc 18 a1 12 a0 05 16 fa 75 b4 10 b1 a8 eb 92 51 dc ca 4e 84 5b 8d f2 f3 db 06 57 05 9f 12 76 69 56 9a af e4 c7 12 2f f8 36 74 ea bf 31 0e 46 fb f8 7e 8b 24 0c e6 3b 30 54 2b 03 b4 96 38 82 f6 cf db 1f 70 66 22 a1 2a bc cb 7a 10 91 45 c4 94 e1 f1 66 8f e3 c5 01 5d d0 26 ee 9b 9f c3`
- `0x30670` `i[ADf` matched ['adf']: **likely noise**. Surrounding 128 bytes: `4a 21 c6 1d 53 a5 a0 d5 fb 38 0d 8b e0 96 6f 50 b7 83 fa 18 51 36 02 9f ab 47 6d 75 50 91 a2 41 57 13 00 16 ed 1b 98 ff 5e 1f 86 42 5f 85 e3 b1 de 54 dd 03 17 ad 3d 20 45 70 19 9f 8b ae 69 5b 41 44 66 e0 5c b3 6d a9 42 64 87 0f 62 18 8d d8 8a 98 39 e5 77 9d df 37 d6 a7 70 26 a8 8b b3 80 c5 6e dc f8 e7 03 e8 af 5b c3 6f de 46 e8 a9 dd 74 09 e0 19 75 5c 4c 8d 9c f3 ea 45 c5 2e e6 df`
- `0x5BEF3` `fnc` matched ['fnc']: **likely noise**. Surrounding 128 bytes: `03 67 6c 13 a7 02 69 05 66 39 01 6d be 17 8b 3f 23 5a 9b d0 1d a5 8b c0 37 bf d3 32 04 8d 1a 51 f0 23 40 93 cb 82 d9 7e 10 a8 85 2b 24 02 17 a3 8f 23 a9 33 2d 24 87 36 03 96 ac 57 66 6a b1 f9 46 4e 63 90 50 94 2d e7 cf 39 b4 a4 bf cc 7a fc f1 2c d2 ad fc b5 f2 4c e1 24 aa 54 ff a4 b3 cc a8 f7 15 88 3c f7 63 5c c8 df 52 be 73 ca 29 4f 18 70 f2 5b ad 0a 3d c7 d2 ea b6 51 68 5f 81 a0`
- `0x3A3D0` `aPTS@` matched ['apt']: **likely noise**. Surrounding 128 bytes: `10 07 b5 af 0c 25 f7 b6 66 f0 44 2c 37 51 0b db 0b 16 01 bd a9 dc 8f 71 cb 74 9f d4 2f 57 b6 67 db d0 f5 40 c3 f1 57 f9 c1 a1 eb 74 d8 3d 30 ac 16 bf 01 98 11 30 59 cc 0c 27 2a 84 79 a7 db 1c 61 50 54 53 40 1e ee f9 48 4c 9c ac 8f b6 5f 04 4a fb f7 8a bd 72 2a 31 8e 58 97 e1 08 2a a3 e9 cd b0 02 5a fc 45 a3 83 36 19 a6 3c 6b 6c 44 dd 0e e2 71 4b c7 4a 9c 5d cf 9a 10 1a 81 9c 8b 4c`
- `0x300788` `gmsHC` matched ['msh']: **likely noise**. Surrounding 128 bytes: `d1 ca 82 1f 22 f5 6e 67 d1 9d 30 85 3a aa 4f d7 48 11 8d d4 dd aa ad 54 b3 72 aa a0 37 97 ff e3 b4 66 2d b1 df f6 e4 e1 2d a5 e6 8b 26 b0 7a ae 3d b3 bb d2 14 9d 27 1b 83 7f f9 ff 16 2f df 67 6d 73 48 43 9c 27 f3 3e 9b 42 1d 76 69 15 ab f8 61 7e 98 71 19 a1 2a 81 10 4b 54 2c 81 4f 2f 65 b3 97 25 27 fb 3e 4b f5 3a 8e 95 ac 70 57 98 6e e5 3f 10 e0 19 66 78 09 01 30 65 16 16 44 68 45`
- `0x523B7D` `hud` matched ['hud']: **likely noise**. Surrounding 128 bytes: `90 f6 19 5a d6 67 0b 0c 6d bc f2 f1 ed 88 f6 1b e2 06 43 8f ba a9 69 4d 58 ee 0d 27 9b af 4a a0 24 28 33 99 a5 a6 a7 cc 77 1b 7a c8 aa 9a 01 99 b1 ca 49 20 30 87 4e f7 bb de 86 58 c6 1e a9 94 48 75 64 a6 01 d3 bf 85 a8 68 93 96 3c 51 e0 a7 6e d4 d8 cb 8b 33 a2 4b af 7a 39 43 2d 11 5c 29 40 df 81 82 82 c0 bf d2 9b d3 80 2f fd 22 6e 64 20 da 59 6d 22 19 2d 01 cf 2b 38 28 0c 7e c0 84`
- `0x1F3AD9` `jab` matched ['jab']: **likely noise**. Surrounding 128 bytes: `8b a2 1a e9 2d 04 4f 49 e8 9e 41 ec 06 23 e8 36 83 ab 38 7c 56 0c b1 b6 a1 fb a5 b2 30 d6 ec 62 4a 0d b6 de d4 05 5d af a8 c8 79 8b 99 06 d7 0a 6e 60 44 c1 1a 8d 35 d1 7f 04 3e 73 c4 2b be fc 6a 61 42 00 f1 55 a5 d1 63 17 9c 89 aa 40 d4 aa b7 a0 86 a6 8c 12 86 f8 d1 8d 1b 95 ab 48 99 d8 f4 a5 d1 37 35 e1 a6 72 67 7b f7 bf 40 b7 24 fa 25 17 a1 9c d5 5d 79 2d bc b2 ff 37 c1 a0 94 d9`
- `0x5C257E` `CUt+` matched ['cut']: **likely noise**. Surrounding 128 bytes: `c2 99 6a 20 ae 42 f8 84 c7 f5 d8 81 f5 2f 07 84 cc 78 5d ec 8e 0a 1f 16 31 71 33 74 74 23 3f c7 d9 e8 61 ea 4e ef 2f d9 05 88 75 e6 ae 04 72 d5 74 52 78 43 4d 23 35 35 d3 ec bc 9a 8d 29 71 e3 43 55 74 2b 00 df 96 63 18 6f 56 55 ae 31 da 0c 3a 23 4e 64 a1 87 db 6f 51 dd 31 fe 44 3f af 9c 6f 62 d6 7a da ba 39 d3 0a c0 44 e3 34 20 75 97 2c 8e af e1 30 45 d3 a9 4d 94 59 b8 a5 3d 7e e6`
- `0x8753` `AI` matched ['AI']: **likely noise**. Surrounding 128 bytes: `6c d6 50 3f 21 56 52 25 d8 aa d7 0d 5a cb 90 51 ab 56 d8 4a ed 25 04 44 c4 75 69 d3 9e 0e 07 32 17 db b4 8e 65 10 5d 9e 3d f0 2d 57 f3 2c f5 6f 08 e7 a2 72 3a 88 7b 94 6f d5 07 0e 77 09 6b ea 41 69 e2 a8 5b 05 d6 62 7d 81 9a 70 86 98 61 de 59 25 af f8 0f e1 a2 93 70 f3 c1 a3 99 5b c6 b8 c6 8c 86 98 a9 cf 4b fc bb 91 71 ed 25 b9 3f 40 d2 df 0f 6f f2 f1 4b 05 56 c4 d7 7c 0d 03 10 29`
- `0x42A69` `1cpu` matched ['CPU']: **likely noise**. Surrounding 128 bytes: `08 cc 1d 4c d3 43 e5 09 02 ed 68 9d ea ee 7c 22 21 33 59 47 8f a1 a4 35 5f 98 96 8d 43 bc 87 0f 89 7e f5 6c b9 04 57 3e 07 7a 39 8f 78 9c 44 90 c9 4a 89 81 7d 5a fd 7a 4a 73 b9 00 68 80 b8 31 63 70 75 0f 5b 43 93 ca 6e 87 1c 02 b4 3a 0b 94 31 8a 3c 2b d8 2a 9e 63 3a 8c c9 6c ad ac 3b ee db 57 cb f5 6d 74 55 c2 8a dc 47 9d 07 89 bf 43 33 c5 7f 70 c5 bc d6 01 a5 19 11 7d 20 04 04 38`