#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- Debug/Verbose flags ---
DEBUG=false
VERBOSE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--debug) DEBUG=true; shift ;;
        -v|--verbose) VERBOSE=true; shift ;;
        *) break ;;
    esac
done

if $DEBUG; then
    set -x
    PS4='+ ${BASH_SOURCE}:${LINENO}: '
fi

log_verbose() { $VERBOSE && echo "[VERBOSE] $*" >&2 || true; }
log_debug() { $DEBUG && echo "[DEBUG] $*" >&2 || true; }

SOURCE_ROOT="${1:-./import-source}"
DEST_ROOT="${2:-./data/fleet}"

if [ ! -d "$SOURCE_ROOT" ]; then
  echo "Source directory not found: $SOURCE_ROOT" >&2
  exit 1
fi

mkdir -p "$DEST_ROOT"
cd "$ROOT"

find "$SOURCE_ROOT" -type f -name 'files_info.csv' | while IFS= read -r usage_file; do
  host_dir="$(dirname "$usage_file")"
  if [ -f "$host_dir/files_packages.csv" ]; then
    host_name="$(basename "$host_dir")"
    echo "Importing $host_name"
    python3 -m unusedos import --source-dir "$host_dir" --dest-dir "$DEST_ROOT/$host_name"
  fi
done

echo "Import complete. Output in $DEST_ROOT"
