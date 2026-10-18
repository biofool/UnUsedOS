#!/usr/bin/env bash
# Upload Packer Kicksecure bundle to GCS for the remote packer-runner VM.
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

UNUSEDOS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

BUCKET_NAME="${BUCKET_NAME:-scraper-intl-deployments-239573}"
PREFIX="${GCS_PREFIX:-deployments/packer-kicksecure/latest}"

echo "Staging packer bundle in $STAGE"
mkdir -p "$STAGE/packer/kicksecure-gcp/scripts"
rsync -a \
  --exclude '.packer' --exclude 'manifest.json' \
  "$UNUSEDOS_ROOT/packer/kicksecure-gcp/" "$STAGE/packer/kicksecure-gcp/"

if [ ! -f "$UNUSEDOS_ROOT/packer/kicksecure-gcp/variables.auto.pkrvars.hcl" ]; then
  cp "$UNUSEDOS_ROOT/packer/kicksecure-gcp/variables.auto.pkrvars.hcl.example" \
    "$STAGE/packer/kicksecure-gcp/variables.auto.pkrvars.hcl"
else
  cp "$UNUSEDOS_ROOT/packer/kicksecure-gcp/variables.auto.pkrvars.hcl" \
    "$STAGE/packer/kicksecure-gcp/variables.auto.pkrvars.hcl"
fi

echo "Uploading to gs://${BUCKET_NAME}/${PREFIX}/"
gsutil -m rsync -r "$STAGE/" "gs://${BUCKET_NAME}/${PREFIX}/"
echo "Upload complete"
