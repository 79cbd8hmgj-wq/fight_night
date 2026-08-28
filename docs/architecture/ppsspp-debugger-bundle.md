# PPSSPP Debugger Bundle

## Purpose

The debugger bundle supplies the live PSP runtime dependency for environment-gated reverse engineering. It is separate from every Fight Night Round 3 ISO, battery save, PPSSPP save state, RAM dump, screenshot, debugger transcript, and extracted game asset.

Two related bundle workflows exist in this repository:

1. the older manual PPSSPP research-bundle builder, which packages upstream PPSSPP tooling such as `wsdbg` and its wrapper scripts; and
2. the externally supplied, identity-locked bundle consumed by the Task 9E runtime adapter.

They must not be treated as interchangeable interfaces. Task 9E uses only the second contract described below.

## Task 9E verified bundle contract

`fnr3-re ppsspp-bundle verify BUNDLE` validates the external bundle before any Task 9E launch. The verifier requires these regular, non-symlinked files under the bundle root:

```text
PPSSPPHeadless
PPSSPPSDL
bin/Xvfb
launch-debug.sh
ppsspp_ws.py
ppsspp-debug.ini
ppsspp-resolved-revision.txt
```

For the Fight Night Round 3 runtime adapter, the locked PPSSPP revision is:

```text
fa50bb1976065c4f8b1b47af227d367fe9771555
```

The verifier also locks the SHA-256 identities of `PPSSPPSDL`, `PPSSPPHeadless`, and `bin/Xvfb`. A bundle with a different revision, binary hash, debugger configuration, missing required file, or symlinked required file is rejected before launch.

The default debugger endpoint is local-only on port `56244`.

## Debugger startup is configuration-driven

The verified Task 9E artifact does **not** depend on the older repository wrapper convention of launching PPSSPP with `--debugger=PORT`.

Instead, `ppsspp-debug.ini` must contain a `[General]` section with a debugger configuration equivalent to:

```ini
RemoteDebuggerOnStartup = true
RemoteDebuggerLocal = true
RemoteISOPort = 56244
```

The verifier reads these values and rejects a bundle if the debugger does not start automatically, is not local-only, or uses a different port from the locked profile.

PPSSPP exposes the JSON WebSocket debugger locally at the configured endpoint. The debugger protocol uses the subprotocol:

```text
debugger.ppsspp.org
```

## Task 9E launcher interface

Task 9E invokes only the verified bundle-local launcher. The supported form is:

```bash
./launch-debug.sh /path/to/game.iso --state /path/to/state.ppst --port 56244
```

The repository adapter constructs the same argument shape programmatically:

```text
[launch-debug.sh, ISO, --state, STATE.ppst, --port, PORT]
```

It does not fall back to a globally installed PPSSPP executable and does not substitute one of the older `run-headless-debugger.sh` or `run-sdl-debugger.sh` wrappers.

The launcher path is accepted only after the bundle revision, binary hashes, and debugger configuration have been verified.

## Repository debugger client

The bundle-local `ppsspp_ws.py` is retained as a diagnostic/reference tool. Task 9E does **not** import or execute it as the runtime adapter library.

The repository uses its own independently unit-tested standard-library WebSocket client, `PpssppDebuggerClient`, for the subset of debugger operations required by Task 9E. This keeps debugger framing, request/response correlation, event handling, breakpoint operations, register reads, bounded memory reads, and backtraces directly testable in the repository.

Raw debugger transcript bodies are not normalized into committed Task 9E evidence.

## Older manual research-bundle builder

The repository still contains the earlier manual builder and wrapper scripts for general PPSSPP research. That workflow packages both PPSSPP front ends plus upstream `wsdbg` and documents the WebSocket transport.

Its wrappers use the confirmed interface available to the PPSSPP revision they build, including forms such as:

```bash
tools/ppsspp-debugger-bundle/run-headless-debugger.sh /path/to/game.iso 20000
tools/ppsspp-debugger-bundle/run-sdl-debugger.sh /path/to/game.iso 20000
tools/ppsspp-debugger-bundle/wsdbg.sh 20000 game.status
```

Those wrappers remain useful for general research and diagnostics. They are not the authoritative launch path for the identity-locked Task 9E experiment.

## Save and state boundary

A PSP state is not required to build or validate the debugger bundle. A clean ISO boot can still be useful for transport checks, module-load research, early breakpoints, and interactive scenario preparation.

For **Task 9E evidence**, however, a `.ppst` state is required. The CLI requires `--state`, hashes the supplied state before capture, and uses the same state identity for both the successful-save and corrupted-copy controls.

A battery save supplies the explicit savedata slot under test. The corrupted control is prepared as a temporary deterministic copy; the source slot is inventoried and must remain unchanged.

Outside Task 9E, a save state is optional acceleration only. For Task 9E, the state is part of the experiment identity and cannot be omitted.

## Copyright and evidence boundary

The runtime adapter never downloads game or save material. ISO, `.ppst`, and savedata inputs remain external and local to the researcher.

Normalized Task 9E evidence may record only bounded, attributable facts such as hashes, sizes, typed addresses, selected registers, callback target, breakpoint observations, and the deterministic one-byte mutation description. Raw save bytes, broad RAM dumps, screenshots, audio/video, and raw debugger transcripts remain outside the repository.
