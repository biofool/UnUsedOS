#!/usr/bin/env bash
# Verify remote packer-runner VM completed Kicksecure image import.
# Usage: bash verify.sh [vm-name] [zone] [project] [expected-image-name]


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

VM="${1:-packer-kicksecure-runner-0}"
ZONE="${2:-us-central1-a}"
PROJECT="${3:-project-135adecf-38fc-4e43-ae4}"
IMAGE="${4:-kicksecure-cli-18-1-4-2}"
SSH_USER="${SSH_USER:-admin}"

export SSH_USER
DEV_TERRAFORM="${DEV_TERRAFORM:-$HOME/projects/dev-terraform}"
# shellcheck source=/dev/null
source "${DEV_TERRAFORM}/scripts/verify-lib.sh"

PASS=0
FAIL=0

run_check() {
  if gcp_check "$VM" "$ZONE" "$PROJECT" "$1" "$2" "$3"; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "=== Packer runner verification: $VM ==="
echo ""

run_check "packer completion marker" \
  "test -f /var/log/packer-kicksecure-complete && echo complete" \
  "complete"

run_check "packer log mentions complete" \
  "grep -q 'Packer kicksecure import complete' /var/log/packer-runner.log 2>/dev/null && echo ok" \
  "ok"

if gcloud compute images describe "$IMAGE" --project="$PROJECT" >/dev/null 2>&1; then
  echo "  PASS  GCP image $IMAGE exists"
  PASS=$((PASS + 1))
else
  echo "  FAIL  GCP image $IMAGE missing"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
