PPSSPP DEBUGGER BUNDLE
======================

This bundle contains an exact Linux x86_64 PPSSPP research build and the official wsdbg WebSocket debugger client.

It contains no Fight Night Round 3 ISO, PSP save, PPSSPP save state, RAM dump, screenshot, or extracted game asset.

Headless launch, paused before execution:
  tools/ppsspp-debugger-bundle/run-headless-debugger.sh /path/to/game.iso 20000

Visual SDL launch:
  tools/ppsspp-debugger-bundle/run-sdl-debugger.sh /path/to/game.iso 20000

Debugger client:
  tools/ppsspp-debugger-bundle/wsdbg.sh 20000

Bundle verification:
  tools/ppsspp-debugger-bundle/verify-bundle.sh

A PSP state is not required. A clean ISO can boot under the debugger. Battery saves and exact-build save states are optional scenario accelerators and must remain local.
