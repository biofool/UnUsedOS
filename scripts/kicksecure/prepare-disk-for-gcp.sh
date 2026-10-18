#!/usr/bin/env bash
# Prepare Kicksecure qcow2 for GCP: guest agent, SSH, disk sizing hints.
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

QCOW2="$(cat "$WORK_DIR/qcow2.path")"
PREPARED="$WORK_DIR/kicksecure-gcp.qcow2"

if [ ! -f "$QCOW2" ]; then
  echo "Run download-kvm-image.sh first"
  exit 1
fi

cp -f "$QCOW2" "$PREPARED"

if command -v virt-customize >/dev/null 2>&1; then
  echo "Customizing disk with virt-customize (google-guest-agent + SSH)"
  virt-customize -a "$PREPARED" \
    --run-command 'export DEBIAN_FRONTEND=noninteractive; apt-get update -qq || true' \
    --run-command 'export DEBIAN_FRONTEND=noninteractive; apt-get install -y -qq google-guest-agent google-compute-engine-oslogin || apt-get install -y -qq cloud-init || true' \
    --run-command 'systemctl enable ssh 2>/dev/null || systemctl enable sshd 2>/dev/null || true' \
    --run-command 'growpart /dev/sda 1 2>/dev/null || true; resize2fs /dev/sda1 2>/dev/null || true'
else
  echo "WARNING: virt-customize not found (install libguestfs-tools)."
  echo "Boot the qcow2 locally once and install google-guest-agent + enable SSH manually."
  echo "See docs/KICKSECURE-GCP-IMAGE.md"
fi

if ! command -v qemu-img >/dev/null 2>&1; then
  echo "ERROR: qemu-img required for raw conversion"
  exit 1
fi

RAW="$WORK_DIR/kicksecure-gcp.raw"
echo "Converting to raw for GCP import"
qemu-img convert -p -f qcow2 -O raw "$PREPARED" "$RAW"

echo "$RAW" > "$WORK_DIR/raw.path"
echo "Prepared raw disk: $RAW ($(du -h "$RAW" | cut -f1))"
