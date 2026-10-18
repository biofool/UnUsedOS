#!/bin/bash
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

output_file="all_package_files.txt"
> "$output_file"

for package in $(dpkg --get-selections | grep -v deinstall | cut -f1); do
    for file_path in $(dpkg -L "$package"); do
        if [ -f "$file_path" ]; then
            echo "$file_path|$package" >> "$output_file"
        fi
    done
done

echo "Output written to $output_file"
