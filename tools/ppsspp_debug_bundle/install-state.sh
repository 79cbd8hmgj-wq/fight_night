#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 STATE.ppst" >&2
  exit 2
}

[[ $# -eq 1 ]] || usage
state_path=$1
[[ -f "$state_path" ]] || { echo "State file not found: $state_path" >&2; exit 1; }

case "$(basename "$state_path")" in
  *.ppst) ;;
  *) echo "State filename must end in .ppst" >&2; exit 1 ;;
esac

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
destination_dir="$root/memstick/PSP/PPSSPP_STATE"
mkdir -p "$destination_dir"
destination="$destination_dir/$(basename "$state_path")"

source_hash=$(sha256sum "$state_path" | awk '{print $1}')
cp -- "$state_path" "$destination"
destination_hash=$(sha256sum "$destination" | awk '{print $1}')
[[ "$source_hash" == "$destination_hash" ]] || {
  echo "State hash changed during installation" >&2
  rm -f -- "$destination"
  exit 1
}

printf '%s  %s\n' "$destination_hash" "$(basename "$destination")" \
  > "$destination_dir/state-manifest.sha256"
printf 'Installed state: %s\nSHA-256: %s\n' "$destination" "$destination_hash"
