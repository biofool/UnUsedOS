#!/bin/bash
# Upload UnusedOS + VEMSStatsCollector bundle to GCS for terraform VM startup.
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

SECURITY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null | tail -n 1)}"
BUCKET_NAME="${BUCKET_NAME:-scraper-intl-deployments-239573}"
PREFIX="${GCS_PREFIX:-deployments/unusedos-test/latest}"

echo "Staging bundle in $STAGE"
mkdir -p "$STAGE/UnusedOS" "$STAGE/VEMSStatsCollector"

rsync -a \
  --exclude '.venv' --exclude '__pycache__' --exclude 'reports' --exclude 'data' \
  --exclude 'insights-rand-1' --exclude '*.csv' --exclude '.pytest_cache' \
  --exclude '.idea' \
  --exclude 'terraform-test/.terraform' --exclude 'terraform-test/*.tfstate*' \
  --exclude 'terraform-test/terraform.tfvars' --exclude 'terraform-test/.terraform.lock.hcl' \
  "$SECURITY_ROOT/UnusedOS/" "$STAGE/UnusedOS/"

rsync -a \
  "$SECURITY_ROOT/VEMSStatsCollector/VEMSFileUsageStats.sh" \
  "$SECURITY_ROOT/VEMSStatsCollector/VEMSStatsCollectorInc.sh" \
  "$STAGE/VEMSStatsCollector/"

echo "Uploading to gs://${BUCKET_NAME}/${PREFIX}/"
gsutil -m rsync -r "$STAGE/" "gs://${BUCKET_NAME}/${PREFIX}/"
echo "Upload complete (project=${PROJECT_ID})"
