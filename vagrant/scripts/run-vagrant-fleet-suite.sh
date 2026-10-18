#!/usr/bin/env bash
# Bring up Debian Vagrant VMs, collect logs from each, summarize fleet-wide unused packages.
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

VAGRANT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
UNUSEDOS_ROOT="$(cd "$VAGRANT_DIR/.." && pwd)"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-$VAGRANT_DIR/archives}"
REPORT_DIR="${REPORT_DIR:-$ARCHIVE_ROOT/fleet-report}"
VMS=(container-web container-api container-worker)
DESTROY=false
SKIP_UP=false

usage() {
  echo "Usage: $0 [--destroy] [--skip-up]"
  echo "  --destroy   vagrant destroy after report"
  echo "  --skip-up   assume VMs are already running"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --destroy) DESTROY=true; shift ;;
    --skip-up) SKIP_UP=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

if ! command -v vagrant >/dev/null 2>&1; then
  echo "ERROR: vagrant not installed (https://developer.hashicorp.com/vagrant/install)"
  exit 1
fi

cd "$VAGRANT_DIR"
mkdir -p "$ARCHIVE_ROOT"

if [ "$SKIP_UP" = false ]; then
  echo "==> vagrant up"
  vagrant up
else
  echo "==> skipping vagrant up (--skip-up)"
fi

echo "==> Rsync UnusedOS source to VMs"
vagrant rsync

echo "==> Collect on each Debian VM"
for vm in "${VMS[@]}"; do
  echo "--- $vm"
  vagrant ssh "$vm" -c "sudo bash /opt/unusedos/vagrant/scripts/collect-on-vm.sh"
done

if [ -d "$UNUSEDOS_ROOT/.venv" ]; then
  PY="$UNUSEDOS_ROOT/.venv/bin/python"
else
  PY=python3
fi

echo "==> Fleet summarize from $ARCHIVE_ROOT"
cd "$UNUSEDOS_ROOT"
# Run tests only if pytest is installed (it's a dev dep, not in requirements.txt).
if $PY -m pytest --version >/dev/null 2>&1; then
  $PY -m pytest tests/test_vagrant_layout.py -q
else
  echo "SKIP: pytest not installed (dev dep) — install with: pip install -r requirements-dev.txt"
fi
$PY -m unusedos summarize --archive-root "$ARCHIVE_ROOT" --output-dir "$REPORT_DIR"

echo ""
echo "Archive:  $ARCHIVE_ROOT"
echo "Report:   $REPORT_DIR/fleet_summary.md"
echo "Hosts:    ${VMS[*]}"

if [ "$DESTROY" = true ]; then
  echo "==> vagrant destroy"
  cd "$VAGRANT_DIR"
  vagrant destroy -f
fi
