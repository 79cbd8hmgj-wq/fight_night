#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: launch-debug.sh ISO --state STATE.ppst [--port PORT] [--headless]
       launch-debug.sh ISO --allow-no-state [--port PORT] [--headless]
EOF
  exit 2
}

[[ $# -ge 2 ]] || usage
iso_path=$1
shift
state_path=
port=56244
force_headless=0
allow_no_state=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --state)
      [[ $# -ge 2 ]] || usage
      state_path=$2
      shift 2
      ;;
    --port)
      [[ $# -ge 2 ]] || usage
      port=$2
      shift 2
      ;;
    --headless)
      force_headless=1
      shift
      ;;
    --allow-no-state)
      allow_no_state=1
      shift
      ;;
    *) usage ;;
  esac
done

[[ -f "$iso_path" ]] || { echo "ISO not found: $iso_path" >&2; exit 1; }
[[ "$port" =~ ^[0-9]+$ ]] && (( port >= 1 && port <= 65535 )) || {
  echo "Invalid debugger port: $port" >&2
  exit 1
}
if [[ -z "$state_path" && $allow_no_state -ne 1 ]]; then
  echo "A compatible PSP .ppst state is required. Use --allow-no-state only for bundle diagnostics." >&2
  exit 1
fi
if [[ -n "$state_path" && ! -f "$state_path" ]]; then
  echo "State file not found: $state_path" >&2
  exit 1
fi

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
runtime="$root/runtime"
memstick="$root/memstick"
mkdir -p "$runtime" "$memstick/PSP/SYSTEM" "$memstick/PSP/PPSSPP_STATE"

# The template enables RemoteDebuggerOnStartup and RemoteDebuggerLocal.
cp -- "$root/ppsspp-debug.ini" "$memstick/PSP/SYSTEM/ppsspp.ini"
grep -q '^RemoteDebuggerOnStartup = True$' "$memstick/PSP/SYSTEM/ppsspp.ini"
grep -q '^RemoteDebuggerLocal = True$' "$memstick/PSP/SYSTEM/ppsspp.ini"

for checksum in PPSSPPSDL.sha256 PPSSPPHeadless.sha256; do
  [[ -f "$root/$checksum" ]] || { echo "Missing checksum: $checksum" >&2; exit 1; }
  (cd "$root" && sha256sum -c "$checksum")
done

sha256sum "$iso_path" > "$runtime/iso.sha256"
if [[ -n "$state_path" ]]; then
  "$root/install-state.sh" "$state_path" | tee "$runtime/state-install.log"
fi

"$root/stop-debug.sh" --quiet || true

export LD_LIBRARY_PATH="$root/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export HOME="$root/home"
export XDG_CONFIG_HOME="$root/home/.config"
mkdir -p "$HOME" "$XDG_CONFIG_HOME"

ppsspp_binary="$root/PPSSPPSDL"
xvfb_pid=
if [[ $force_headless -eq 1 ]]; then
  ppsspp_binary="$root/PPSSPPHeadless"
elif [[ -z "${DISPLAY:-}" ]]; then
  if [[ -x "$root/bin/Xvfb" ]]; then
    display_number=99
    "$root/bin/Xvfb" ":$display_number" -screen 0 1280x720x24 -nolisten tcp \
      >"$runtime/xvfb.stdout.log" 2>"$runtime/xvfb.stderr.log" &
    xvfb_pid=$!
    printf '%s\n' "$xvfb_pid" > "$runtime/xvfb.pid"
    export DISPLAY=":$display_number"
    sleep 1
  else
    ppsspp_binary="$root/PPSSPPHeadless"
  fi
fi

(
  cd "$root"
  "$ppsspp_binary" "$iso_path" \
    >"$runtime/ppsspp.stdout.log" 2>"$runtime/ppsspp.stderr.log"
) &
ppsspp_pid=$!
printf '%s\n' "$ppsspp_pid" > "$runtime/ppsspp.pid"
printf '%s\n' "$ppsspp_binary" > "$runtime/ppsspp-binary.txt"

cleanup_on_failure() {
  "$root/stop-debug.sh" --quiet || true
}
trap cleanup_on_failure ERR

for _attempt in $(seq 1 40); do
  if ! kill -0 "$ppsspp_pid" 2>/dev/null; then
    echo "PPSSPP exited before the debugger became available" >&2
    tail -n 80 "$runtime/ppsspp.stderr.log" >&2 || true
    exit 1
  fi
  if "$root/ppsspp_ws.py" --port "$port" --timeout 1 --wait 1 health \
    >"$runtime/debugger-health.jsonl" 2>"$runtime/debugger-health.stderr"; then
    printf 'PPSSPP PID: %s\nDebugger: ws://127.0.0.1:%s/debugger\n' "$ppsspp_pid" "$port"
    printf 'ISO manifest: %s\n' "$runtime/iso.sha256"
    if [[ -n "$state_path" ]]; then
      printf 'State manifest: %s\n' "$memstick/PSP/PPSSPP_STATE/state-manifest.sha256"
    fi
    trap - ERR
    exit 0
  fi
  sleep 0.5
done

echo "PPSSPP remote debugger did not become healthy on port $port" >&2
exit 1
