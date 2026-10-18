#!/usr/bin/env bash
# Download and extract Kicksecure KVM CLI qcow2 from kicksecure.com.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

if [ -f "$SCRIPT_DIR/config.env" ]; then
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/config.env"
else
  echo "Copy config.env.example to config.env first"
  exit 1
fi

mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

ARCHIVE="$(basename "$KICKSECURE_URL")"
if [ ! -f "$ARCHIVE" ]; then
  echo "Downloading $KICKSECURE_URL"
  curl -fL --tlsv1.3 --retry 3 -o "$ARCHIVE" "$KICKSECURE_URL"
else
  echo "Using cached archive $ARCHIVE"
fi

echo "Extracting (use tar, not unxz — per Kicksecure docs)"
tar -xvf "$ARCHIVE"

QCOW2="$(find "$WORK_DIR" -maxdepth 1 -name 'Kicksecure*.qcow2' | head -1)"
if [ -z "$QCOW2" ]; then
  echo "ERROR: no Kicksecure*.qcow2 found after extract"
  exit 1
fi

echo "Extracted disk: $QCOW2"
echo "$QCOW2" > "$WORK_DIR/qcow2.path"
