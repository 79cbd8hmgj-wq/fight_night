#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

sha256sum -c bundle.sha256
bash -n tools/ppsspp-debugger-bundle/run-headless-debugger.sh
bash -n tools/ppsspp-debugger-bundle/run-sdl-debugger.sh
bash -n tools/ppsspp-debugger-bundle/wsdbg.sh

export LD_LIBRARY_PATH="$ROOT/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
./PPSSPPHeadless --version >/dev/null 2>&1 || true
./wsdbg --help >/dev/null

echo "PPSSPP debugger bundle verification passed."
