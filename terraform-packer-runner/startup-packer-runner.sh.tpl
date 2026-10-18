#!/bin/bash
# Remote packer-runner VM: install Packer, sync bundle from GCS, run kicksecure import build.
set -euo pipefail

BUCKET_NAME="${bucket_name}"
GCS_PREFIX="${gcs_packer_prefix}"
INSTALL_ROOT="/opt/packer-run"
PACKER_DIR="$INSTALL_ROOT/packer/kicksecure-gcp"
LOG_FILE="/var/log/packer-runner.log"
MARKER="/var/log/packer-kicksecure-complete"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $1" | tee -a "$LOG_FILE"
}

log "Packer runner starting"

# Compressed swap: zswap (zstd/zsmalloc) in front of disk swap.
# 16GB runner — cheap insurance; runtime sysctls guarded by file existence.
if [ -d /sys/module/zswap/parameters ]; then
  [ -f /sys/module/zswap/parameters/enabled ] && \
    echo 1 > /sys/module/zswap/parameters/enabled 2>>"$LOG_FILE" || log "WARN: zswap enable failed"
  [ -f /sys/module/zswap/parameters/compressor ] && \
    echo zstd > /sys/module/zswap/parameters/compressor 2>>"$LOG_FILE" || log "WARN: zswap compressor write failed"
  [ -f /sys/module/zswap/parameters/zpool ] && \
    echo zsmalloc > /sys/module/zswap/parameters/zpool 2>>"$LOG_FILE" || log "WARN: zswap zpool write failed"
  log "zswap configured (zstd compressor, zsmalloc zpool)"
else
  log "WARN: zswap not available in this kernel; continuing"
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl gnupg software-properties-common apt-transport-https ca-certificates

if ! command -v packer >/dev/null 2>&1; then
  log "Installing HashiCorp Packer"
  install -m 0755 -d /usr/share/keyrings
  curl -fsSL https://apt.releases.hashicorp.com/gpg \
    | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(. /etc/os-release && echo "$VERSION_CODENAME") main" \
    > /etc/apt/sources.list.d/hashicorp.list
  apt-get update -qq
  apt-get install -y -qq packer
fi

if command -v gsutil >/dev/null 2>&1; then
  :
else
  log "Installing Google Cloud CLI"
  install -m 0755 -d /usr/share/keyrings
  curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    > /etc/apt/sources.list.d/google-cloud-sdk.list
  apt-get update -qq
  apt-get install -y -qq google-cloud-cli
fi

mkdir -p "$INSTALL_ROOT"
gsutil -m rsync -r "gs://$${BUCKET_NAME}/$${GCS_PREFIX}/" "$INSTALL_ROOT/" >>"$LOG_FILE" 2>&1

if [ ! -d "$PACKER_DIR" ]; then
  log "ERROR: packer bundle missing at $PACKER_DIR"
  exit 1
fi

cd "$PACKER_DIR"
log "Running packer init"
packer init . >>"$LOG_FILE" 2>&1

log "Running packer build (creates inner converter VM on GCP)"
packer build -var-file=variables.auto.pkrvars.hcl . >>"$LOG_FILE" 2>&1

touch "$MARKER"
log "Packer kicksecure import complete"
