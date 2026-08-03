#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 /absolute/path/to/game.iso [port]" >&2
  exit 2
fi

ISO="$1"
PORT="${2:-20000}"

if [[ ! -f "$ISO" ]]; then
  echo "ISO not found: $ISO" >&2
  exit 2
fi
if [[ ! "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
  echo "invalid debugger port: $PORT" >&2
  exit 2
fi

RUNTIME_DIR="${PPSSPP_RUNTIME_DIR:-$ROOT/runtime}"
mkdir -p "$RUNTIME_DIR/home" "$RUNTIME_DIR/config" "$RUNTIME_DIR/data"

export HOME="$RUNTIME_DIR/home"
export XDG_CONFIG_HOME="$RUNTIME_DIR/config"
export XDG_DATA_HOME="$RUNTIME_DIR/data"
export LD_LIBRARY_PATH="$ROOT/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

exec "$ROOT/PPSSPPSDL" --debugger="$PORT" "$ISO"
