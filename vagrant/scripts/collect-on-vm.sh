#!/usr/bin/env bash
# Collect package inventory + usage on a Debian VM and run UnusedOS analyze.
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

HOST="$(hostname -s)"
UNUSEDOS=/opt/unusedos
EXPORT="/vagrant/archives/${HOST}"
COLLECT_PATHS="${COLLECT_PATHS:-/usr/bin:/usr/lib}"

mkdir -p "$EXPORT"
cd "$UNUSEDOS"

bash packages_exploder.sh
mv all_package_files.txt "${EXPORT}/${HOST}-all_package_files.log"

: > "${EXPORT}/${HOST}-usage.log"
IFS=':' read -r -a paths <<< "$COLLECT_PATHS"
for path in "${paths[@]}"; do
  if [ -d "$path" ]; then
    nice find "$path" -xdev -type f -printf '%p|%T@|%A@\n' >> "${EXPORT}/${HOST}-usage.log" 2>/dev/null || true
  fi
done

.venv/bin/python -m unusedos analyze \
  --input-dir "$EXPORT" \
  --host "$HOST" \
  --output-dir "${EXPORT}/reports"

touch "${EXPORT}/.collect-complete"
echo "Collected UnusedOS artifacts for ${HOST} in ${EXPORT}"
