# Ghidra setup plan

## Load this executable first

Load root `BOOT.BIN` first. It begins with ELF magic (`7F 45 4C 46`), has ELF32/little-endian header bytes, lower entropy than `EBOOT.BIN`, and contains domain-readable strings for archives, databases, UI, AI, and gameplay modifiers. Root `EBOOT.BIN` should be treated as a PSP `~PSP` container that likely needs decryption/unpacking before it is useful for static Ghidra work.

## Expected import settings

- File: `BOOT.BIN`
- Format: ELF
- CPU architecture: MIPS / Allegrex-compatible PSP MIPS.
- Endian mode: little-endian.
- Bitness: 32-bit.
- PSP/MIPS settings: use MIPS32 little-endian if no PSP/Allegrex loader is available; if a PSP loader/extension is installed, use it so syscall/import patterns are labeled.
- Decryption needed: not for `BOOT.BIN` based on its plain ELF header. `EBOOT.BIN` may need PSP decryption/unpacking first; this report does not attempt that.

## Strings to search immediately after import

Search for these first because they provide high-value xrefs:

- Archive roots: `preload/db.viv`, `preload/tables.viv`, `contract/contracts.viv`, `scripts.viv`, `boxerpre.viv`, `bootpreloads.viv`.
- Database/table leaves: `xdbboxr.adf`, `xdbtrain.adf`, `xdbvenue.adf`, `xdbstore.adf`, `xdbalias.adf`, `xdbrivl.adf`, `xdbcutpn.adf`.
- Contract/function leaves: `cutman.fnc`, `trainer.fnc`, `fights.fnc`.
- Gameplay/AI labels: `stamina`, `dec damage taken from clean punch`, `inc all attack damage`, `ai/drones/drone0`, `ai/mods/p%d/attack power`, `ai/mods/p%d/energy and health`, `DRONE_COUNTER_PUNCH`.
- UI/HUD/resource labels: `fnhud`, `hud`, `StartAPTRender`, `StopAPTRender`, `Punch Stats`, `Scorecards`.

## Function areas to rename first

1. Xrefs to `preload/db.viv` and nearby `xdb*.adf` strings: rename as database archive open / database member load candidates.
2. Xrefs to `contract/contracts.viv` and `*.fnc`: rename as career contract script loader candidates.
3. Xrefs to `tables.viv`: rename as table preload/resource table loader candidates.
4. Xrefs to `scripts.viv`, `bootpreloads.viv`, and `boxerpre.viv`: rename as preload/resource archive loader candidates.
5. Xrefs to `fnhud`, `StartAPTRender`, and `StopAPTRender`: rename as HUD/APT UI loader/render candidates.
6. Xrefs to damage/stamina/AI modifier strings: rename conservatively as combat modifier / AI modifier candidates until decompilation or watchpoints prove behavior.

## Using archive/database string references to locate loader functions

- Start from each string in the Ghidra String window and use Xrefs. If a string has no direct xref, define it as ASCII and re-run analysis.
- For an archive path string, identify the function that passes it to file/open/read or VFS routines. Then inspect callers to find the owning subsystem: boot preload, career screen, venue select, fight load, etc.
- For `xdb*.adf` strings, inspect surrounding data references: they may be entries in a table of archive members. Rename the table and the function that iterates it.
- For `*.fnc` strings, track call chains from `contracts.viv` to career menus or contract negotiation screens.
- Once a likely loader is found, use PPSSPP breakpoints/watchpoints on file path buffers or loaded table memory to connect static xrefs to runtime behavior.
