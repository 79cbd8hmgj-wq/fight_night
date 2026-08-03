#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

sha256sum -c bundle.sha256
bash -n tools/ppsspp-debugger-bundle/run-headless-debugger.sh
bash -n tools/ppsspp-debugger-bundle/run-sdl-debugger.sh
bash -n tools/ppsspp-debugger-bundle/wsdbg.sh

export LD_LIBRARY_PATH="$ROOT/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
./PPSSPPHeadless --version >/dev/null
./wsdbg --help >/dev/null

if ldd ./PPSSPPHeadless ./PPSSPPSDL ./wsdbg | grep -q 'not found'; then
  echo "A bundled executable has an unresolved shared-library dependency." >&2
  exit 1
fi

echo "PPSSPP debugger bundle verification passed."
