# PPSSPP Debugger Bundle

This directory is copied into the portable Linux x86_64 PPSSPP research artifact.
It provides the same handoff model used by the Nintendo DS debugger bundle:

- one pinned emulator build;
- local-only remote debugger startup;
- a self-contained standard-library WebSocket client;
- explicit ISO and save-state hashing;
- isolated `memstick/` and runtime logs;
- no ROM, save, or extracted copyrighted game data in Git or CI.

## Required local inputs

The bundle intentionally ships without game data. Runtime work requires:

1. The exact `ULUS10066-v1.00` Fight Night Round 3 image.
2. A `.ppst` save state produced by the exact PPSSPP revision recorded in
   `ppsspp-resolved-revision.txt`.
3. Preferably the battery savedata directory used when the state was created.

PPSSPP save states are version-sensitive. A state from another build is evidence only
if the bundled emulator loads it cleanly and the game image hash also matches.

## Usage

```bash
./install-state.sh /path/to/state.ppst
./launch-debug.sh /path/to/FightNightRound3.iso --state /path/to/state.ppst
./ppsspp_ws.py health
./ppsspp_ws.py event game.status
```

The default debugger endpoint is:

```text
ws://127.0.0.1:56244/debugger
```

`launch-debug.sh` writes a dedicated `memstick/PSP/SYSTEM/ppsspp.ini`, launches
`PPSSPPSDL` under the current display or `xvfb-run`, and falls back to
`PPSSPPHeadless` only when requested. It refuses missing inputs, records SHA-256
manifests, and waits for the remote debugger health check.

The state installer preserves the original state filename under:

```text
memstick/PSP/PPSSPP_STATE/
```

It does not guess a slot name or silently claim that a state loaded. State loading must
be confirmed through the exact build's supported UI or WebSocket command before any
runtime evidence is promoted.

## Evidence policy

Raw states, memory dumps, screenshots, and debugger transcripts remain local. Commit
only normalized evidence containing hashes, addresses, selected values, controls,
conclusions, confidence, and the exact emulator/source revision.
