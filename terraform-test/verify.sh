#!/usr/bin/env bash
# Verify UnusedOS terraform VM deploy test.
# Usage: bash verify.sh [vm-name] [zone] [project]


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

VM="${1:-unusedos-test-0}"
ZONE="${2:-us-central1-a}"
PROJECT="${3:-project-135adecf-38fc-4e43-ae4}"

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
echo "=== UnusedOS VM verification: $VM ==="
echo ""

run_check "startup completion marker" \
  "test -f /var/log/unusedos-test-complete && echo complete" \
  "complete"

run_check "package inventory artifact" \
  "ls /var/log/unusedos-export/${VM}/*-all_package_files.log 2>/dev/null | head -1" \
  "all_package_files.log"

run_check "usage artifact" \
  "ls /var/log/unusedos-export/${VM}/*-usage.log 2>/dev/null | head -1" \
  "usage.log"

run_check "analysis report" \
  "ls /var/log/unusedos-export/${VM}/reports/package_rankings.csv 2>/dev/null" \
  "package_rankings.csv"

run_check "pytest suite passed" \
  "test -f /var/log/unusedos-tests-passed && echo passed" \
  "passed"

run_check "usage harness passed" \
  "test -f /var/log/unusedos-harness-passed && echo passed" \
  "passed"

run_check "unusedos CLI available" \
  "cd /opt/security/UnusedOS && .venv/bin/python -m unusedos check-atime >/dev/null 2>&1 && echo ok" \
  "ok"

echo ""
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -eq 0 ]; then
  echo "All checks passed!"
  exit 0
fi
exit 1
