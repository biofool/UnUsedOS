#!/usr/bin/env bash
# Run multi-container UnusedOS test suite and write a cross-container fleet report.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

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

ARCHIVE_ROOT="${1:-$ROOT/reports/container-suite}"
REPORT_DIR="${2:-$ARCHIVE_ROOT/fleet-report}"

cd "$ROOT"
if [ -d .venv ]; then
  PY=.venv/bin/python
else
  PY=python3
fi

echo "==> Container fleet suite (archive: $ARCHIVE_ROOT)"
# Run tests only if pytest is installed (it's a dev dep, not in requirements.txt).
if $PY -m pytest --version >/dev/null 2>&1; then
  $PY -m pytest tests/test_archive_report.py -q
else
  echo "SKIP: pytest not installed (dev dep) — install with: pip install -r requirements-dev.txt"
fi

echo "==> Generate container archives and fleet summary"
$PY -m unusedos.container_suite --archive-root "$ARCHIVE_ROOT" --report-dir "$REPORT_DIR"

echo "==> Re-summarize from archive (search + aggregate)"
$PY -m unusedos summarize --archive-root "$ARCHIVE_ROOT" --output-dir "${REPORT_DIR}/rescan"

echo "Fleet report: ${REPORT_DIR}/fleet_summary.md"
echo "Rescan report: ${REPORT_DIR}/rescan/fleet_summary.md"
