#!/usr/bin/env bash
set -euo pipefail

quiet=0
if [[ ${1:-} == "--quiet" ]]; then
  quiet=1
elif [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--quiet]" >&2
  exit 2
fi

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
runtime="$root/runtime"

stop_pid_file() {
  local label=$1
  local file=$2
  [[ -f "$file" ]] || return 0
  local pid
  pid=$(cat "$file")
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    for _attempt in $(seq 1 20); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.1
    done
    kill -9 "$pid" 2>/dev/null || true
    [[ $quiet -eq 1 ]] || echo "Stopped $label PID $pid"
  fi
  rm -f -- "$file"
}

stop_pid_file PPSSPP "$runtime/ppsspp.pid"
stop_pid_file Xvfb "$runtime/xvfb.pid"
