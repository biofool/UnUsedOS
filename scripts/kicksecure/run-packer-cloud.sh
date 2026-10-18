#!/usr/bin/env bash
# Run only when already SSH'd into the packer-runner VM. Prefer run-packer-on-gce.sh from laptop.
set -euo pipefail

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

echo "Use from your laptop (no local Packer required):"
echo "  bash scripts/kicksecure/run-packer-on-gce.sh"
exit 1
