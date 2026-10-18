#!/usr/bin/env bash
# Provision a Debian VM for UnusedOS fleet testing.
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

VM_NAME="${1:?vm name}"
USE_PACKAGES="${2:?packages to install and exercise}"
USE_CMD="${3:?command that reads the used package}"

export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y -qq python3-venv python3-pip findutils rsync $USE_PACKAGES tree
# tree is installed on every VM but not exercised (baseline unused package).

if [ ! -d /opt/unusedos/.venv ]; then
  python3 -m venv /opt/unusedos/.venv
fi
/opt/unusedos/.venv/bin/pip install -q -r /opt/unusedos/requirements.txt

# Exercise the declared package so its files get fresh atime.
bash -lc "$USE_CMD" >/dev/null 2>&1 || true
for pkg in $USE_PACKAGES; do
  dpkg-query -L "$pkg" 2>/dev/null | while IFS= read -r path; do
    [ -f "$path" ] || continue
    case "$path" in
      /usr/bin/*|/usr/lib/*) cat "$path" >/dev/null 2>&1 || true ;;
    esac
  done
done

touch "/var/log/unusedos-${VM_NAME}-provisioned"
echo "Provisioned ${VM_NAME}: used packages=${USE_PACKAGES}"
