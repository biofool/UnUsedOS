#!/bin/bash
# VM startup: sync UnusedOS bundle from GCS, collect sample usage, run analysis.
set -euo pipefail

BUCKET_NAME="${bucket_name}"
GCS_PREFIX="${gcs_deployments_prefix}"
COLLECT_PATHS="${collect_paths}"
INSTALL_ROOT="/opt/security"
UNUSEDOS_DIR="$INSTALL_ROOT/UnusedOS"
LOG_FILE="/var/log/unusedos-startup.log"
HOST="$(hostname -s)"
EXPORT_DIR="/var/log/unusedos-export/$HOST"
MARKER="/var/log/unusedos-test-complete"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] [$HOST] $1" | tee -a "$LOG_FILE"
}

log "UnusedOS VM deploy test starting"

# Compressed swap: zram lz4 at ~100% RAM (e2-small OOM insurance).
# Idempotent + warn-and-continue; any failure must not abort the test run.
if swapon --show=NAME --noheadings 2>/dev/null | grep -q zram; then
  log "zram swap already active"
elif modprobe zram 2>>"$LOG_FILE" && [ -d /sys/block/zram0 ]; then
  echo lz4 > /sys/block/zram0/comp_algorithm 2>>"$LOG_FILE" || log "WARN: zram comp_algorithm write failed"
  echo "$(awk '/MemTotal/{print $2}' /proc/meminfo)K" > /sys/block/zram0/disksize 2>>"$LOG_FILE" || log "WARN: zram disksize write failed"
  if mkswap /dev/zram0 >>"$LOG_FILE" 2>&1 && swapon -p 10 /dev/zram0 >>"$LOG_FILE" 2>&1; then
    log "zram swap enabled (lz4, ~100% RAM, priority 10)"
  else
    log "WARN: zram swap activation failed; continuing without it"
  fi
else
  log "WARN: zram module unavailable; continuing without compressed swap"
fi

apt-get update -qq
apt-get install -y -qq python3-venv python3-pip findutils rsync

mkdir -p "$INSTALL_ROOT" "$EXPORT_DIR"
gsutil -m rsync -r "gs://$${BUCKET_NAME}/$${GCS_PREFIX}/" "$INSTALL_ROOT/" >>"$LOG_FILE" 2>&1

if [ ! -d "$UNUSEDOS_DIR" ]; then
  log "ERROR: UnusedOS bundle not found at $UNUSEDOS_DIR"
  exit 1
fi

cd "$UNUSEDOS_DIR"
python3 -m venv .venv
.venv/bin/pip install -q -r requirements-dev.txt

log "Running UnusedOS test suite"
if .venv/bin/python -m pytest -q > /var/log/unusedos-pytest.log 2>&1; then
  touch /var/log/unusedos-tests-passed
  log "pytest passed ($(tail -1 /var/log/unusedos-pytest.log))"
else
  log "ERROR: pytest failed"
  tail -30 /var/log/unusedos-pytest.log >>"$LOG_FILE"
  exit 1
fi

log "Running usage-detection harness"
if .venv/bin/python -m unusedos.harness --root /var/log/unusedos-harness-demo \
  > /var/log/unusedos-harness.log 2>&1; then
  touch /var/log/unusedos-harness-passed
  log "harness passed"
else
  log "ERROR: harness failed"
  tail -30 /var/log/unusedos-harness.log >>"$LOG_FILE"
  exit 1
fi

log "Building package inventory"
bash packages_exploder.sh
mv all_package_files.txt "$EXPORT_DIR/$${HOST}-all_package_files.log"

log "Collecting file usage from: $COLLECT_PATHS"
: > "$EXPORT_DIR/$${HOST}-usage.log"
IFS=':' read -r -a paths <<< "$COLLECT_PATHS"
for path in "$${paths[@]}"; do
  if [ -d "$path" ]; then
    nice find "$path" -xdev -type f -printf '%p|%T@|%A@\n' >> "$EXPORT_DIR/$${HOST}-usage.log" 2>>"$LOG_FILE" || true
  fi
done

log "Running UnusedOS analysis"
.venv/bin/python -m unusedos analyze \
  --input-dir "$EXPORT_DIR" \
  --host "$HOST" \
  --output-dir "$EXPORT_DIR/reports"

touch "$MARKER"
log "UnusedOS VM deploy test complete"
