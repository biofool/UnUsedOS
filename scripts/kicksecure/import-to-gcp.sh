#!/usr/bin/env bash
# Upload prepared Kicksecure disk to GCS and import as a GCP compute image.
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

RAW="$(cat "$WORK_DIR/raw.path")"
if [ ! -f "$RAW" ]; then
  echo "Run prepare-disk-for-gcp.sh first"
  exit 1
fi

GCS_URI="gs://${IMPORT_BUCKET}/${IMPORT_PREFIX}/kicksecure-gcp.raw"
echo "Uploading $RAW to $GCS_URI (this may take several minutes)"
gsutil -m cp "$RAW" "$GCS_URI"

if gcloud compute images describe "$GCP_IMAGE_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
  echo "Image $GCP_IMAGE_NAME already exists in $PROJECT_ID"
  echo "Delete it first to re-import: gcloud compute images delete $GCP_IMAGE_NAME --project=$PROJECT_ID"
  exit 1
fi

echo "Importing GCP image $GCP_IMAGE_NAME"
gcloud compute images import "$GCP_IMAGE_NAME" \
  --project="$PROJECT_ID" \
  --source-uri="$GCS_URI" \
  --os="$IMPORT_OS" \
  --zone="$ZONE"

echo ""
echo "Import complete. Use in Terraform:"
echo "  boot_disk_image = \"projects/${PROJECT_ID}/global/images/${GCP_IMAGE_NAME}\""
