#!/usr/bin/env bash
# Runs on a temporary GCP builder VM (Packer googlecompute source).
# Download Kicksecure KVM qcow2, customize for GCP, convert, import as custom image.
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

: "${PROJECT_ID:?}"
: "${ZONE:?}"
: "${IMPORT_BUCKET:?}"
: "${IMPORT_PREFIX:?}"
: "${KICKSECURE_URL:?}"
: "${GCP_IMAGE_NAME:?}"
: "${IMPORT_OS:=debian-12}"

WORKDIR=/var/tmp/kicksecure-import
GCS_URI="gs://${IMPORT_BUCKET}/${IMPORT_PREFIX}/kicksecure-gcp.raw"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $*"
}

log "Kicksecure cloud conversion starting"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl qemu-utils libguestfs-tools ca-certificates gnupg

if ! command -v gcloud >/dev/null 2>&1; then
  log "Installing Google Cloud CLI"
  install -m 0755 -d /usr/share/keyrings
  curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    > /etc/apt/sources.list.d/google-cloud-sdk.list
  apt-get update -qq
  apt-get install -y -qq google-cloud-cli
fi

mkdir -p "$WORKDIR"
cd "$WORKDIR"

ARCHIVE="$(basename "$KICKSECURE_URL")"
if [ ! -f "$ARCHIVE" ]; then
  log "Downloading $KICKSECURE_URL"
  curl -fL --tlsv1.3 --retry 3 -o "$ARCHIVE" "$KICKSECURE_URL"
fi

log "Extracting archive (tar, not unxz)"
tar -xvf "$ARCHIVE"

QCOW2="$(find "$WORKDIR" -maxdepth 1 -name 'Kicksecure*.qcow2' | head -1)"
if [ -z "$QCOW2" ]; then
  log "ERROR: Kicksecure qcow2 not found after extract"
  exit 1
fi

PREPARED="$WORKDIR/kicksecure-gcp.qcow2"
cp -f "$QCOW2" "$PREPARED"

log "Customizing disk for GCP (google-guest-agent, SSH)"
if virt-customize -a "$PREPARED" \
  --run-command 'export DEBIAN_FRONTEND=noninteractive; apt-get update -qq || true' \
  --run-command 'export DEBIAN_FRONTEND=noninteractive; apt-get install -y -qq google-guest-agent google-compute-engine-oslogin 2>/dev/null || apt-get install -y -qq cloud-init || true' \
  --run-command 'systemctl enable ssh 2>/dev/null || systemctl enable sshd 2>/dev/null || true'; then
  log "virt-customize completed"
else
  log "WARNING: virt-customize failed; continuing with unmodified disk"
fi

RAW="$WORKDIR/kicksecure-gcp.raw"
log "Converting qcow2 to raw"
qemu-img convert -p -f qcow2 -O raw "$PREPARED" "$RAW"

if gcloud compute images describe "$GCP_IMAGE_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
  log "Image $GCP_IMAGE_NAME already exists; skipping import"
  exit 0
fi

log "Uploading raw disk to $GCS_URI"
gsutil -m cp "$RAW" "$GCS_URI"

log "Importing GCP image $GCP_IMAGE_NAME"
gcloud compute images import "$GCP_IMAGE_NAME" \
  --project="$PROJECT_ID" \
  --source-uri="$GCS_URI" \
  --os="$IMPORT_OS" \
  --zone="$ZONE" \
  --quiet

log "Kicksecure image ready: projects/${PROJECT_ID}/global/images/${GCP_IMAGE_NAME}"
