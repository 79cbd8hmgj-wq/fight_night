# PPSSPP Debugger Bundle

## Purpose

The debugger bundle supplies the live PSP runtime dependency that the existing capture harness intentionally leaves environment-gated. It is separate from any Fight Night Round 3 ISO, battery save, PPSSPP save state, RAM dump, screenshot, or extracted game asset.

The bundle is built from an immutable PPSSPP revision and contains:

```text
PPSSPPHeadless
PPSSPPSDL
wsdbg
assets/
lib/
tools/ppsspp-debugger-bundle/
PPSSPP-WebSocket-Debugger.md
PPSSPP-LICENSE.txt
ppsspp-resolved-revision.txt
bundle.sha256
```

## Why both emulator front ends are included

`PPSSPPHeadless` is the deterministic automation target. With `--debugger=PORT`, PPSSPP starts the remote WebSocket debugger and the headless frontend halts the emulated CPU before execution. This permits breakpoints to be installed before the game runs.

`PPSSPPSDL` is the visual fallback. It boots the same ISO normally while exposing the same remote debugger. It is used to navigate menus, create a profile or battery save, identify a reproducible scenario, and inspect presentation when a headless input trace has not yet been authored.

Both binaries are built from the same exact source revision.

## Debugger transport

PPSSPP exposes a JSON WebSocket debugger at:

```text
ws://127.0.0.1:PORT/debugger
```

The required WebSocket subprotocol is:

```text
debugger.ppsspp.org
```

The official `wsdbg` client is bundled. The interface supports the operations needed by the reverse-engineering plan, including:

- CPU pause, resume, status, registers, and stepping;
- execution breakpoints;
- read, write, and read/write memory breakpoints;
- memory reads, writes, searches, and disassembly;
- loaded HLE module enumeration and backtraces;
- deterministic button and analog input injection;
- screenshots, GPU buffers, and replay controls where supported.

## Launching

Headless, paused before game execution:

```bash
tools/ppsspp-debugger-bundle/run-headless-debugger.sh /path/to/game.iso 20000
```

Visual SDL session:

```bash
tools/ppsspp-debugger-bundle/run-sdl-debugger.sh /path/to/game.iso 20000
```

Connect interactively:

```bash
tools/ppsspp-debugger-bundle/wsdbg.sh 20000
```

Send a one-shot command:

```bash
tools/ppsspp-debugger-bundle/wsdbg.sh 20000 game.status
```

The launchers place PPSSPP's runtime configuration and memory-stick files under the bundle-local `runtime/` directory unless `PPSSPP_RUNTIME_DIR` is set explicitly.

## Save and state boundary

A PSP state is not required to build or validate the debugger bundle.

A clean ISO boot is sufficient for:

- validating the WebSocket transport;
- proving module load addresses;
- installing early breakpoints;
- tracing initialization and title-screen behavior;
- creating a new profile through the SDL frontend.

A battery save becomes useful when repeated research needs unlocked modes or career data. It is more portable across PPSSPP builds than a save state.

A PPSSPP save state is optional acceleration only. It must be produced by the exact bundled PPSSPP revision, hashed, kept local, and never treated as authoritative without a clean-boot control.

## Copyright boundary

The workflow never accepts, downloads, reads, or uploads a game image or save. The published artifact contains PPSSPP binaries, upstream assets, debugger documentation, wrapper scripts, dependency diagnostics, and hashes only.
