#!/bin/bash
# collect-on-host.sh - Collect file access times and package ownership.
#
# Phases, each cached under <output>/cache:
#   1. Installed package list, plus the path list shipped by each package
#   2. Every regular file and symlink on the selected filesystems.
#      find discovers paths; 8 xargs workers stat them in batches.
#   3. Match each filesystem path to a package
#
# Phase 3 is an index lookup, not a per-file dpkg -S. Files a package creates
# on disk but does not ship are attributed when the nearest parent directory
# is listed by exactly one package. Shared directories in
# collect-generic-dirs.txt stop that walk. A package does not own a directory
# merely because one of its files is nested there.

set -euo pipefail

export LC_ALL=C

OUTPUT_DIR="${PWD}"
VERBOSE=false
DEBUG=false
REFRESH=false
DPKG_INFO_DIR="/var/lib/dpkg/info"
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
GENERIC_DIRS_FILE="${SCRIPT_DIR}/collect-generic-dirs.txt"
ROOT_ARGS=()
CACHE_FORMAT=2
STAT_WORKERS=8
STAT_BATCH=1024

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2; }
log_verbose() { $VERBOSE && echo "[VERBOSE] $*" >&2 || true; }
log_debug() { $DEBUG && echo "[DEBUG] $*" >&2 || true; }

usage() {
    cat <<EOF
collect-on-host.sh - Collect file access time data for UnusedOS analysis

Usage: $0 [OPTIONS]

Options:
  -o, --output-dir DIR    Output directory (default: current directory)
  --root PATH             Filesystem tree to scan (repeatable). Default: local
                          disk mounts from /proc/mounts, or / if none are listed
  --refresh               Ignore cached package and file lists and collect again
  --dpkg-info DIR         Directory of dpkg *.list files (default: /var/lib/dpkg/info)
  --generic-dirs FILE     Shared directories that must not inherit package ownership
  -v, --verbose           Enable verbose output
  -d, --debug             Enable debug output
  -h, --help              Show this help message

Output files:
  files_info.csv          Every regular file and symlink (path|creation_time|access_time)
  files_packages.csv      File-to-package mappings (path,package)
  all_package_files.csv   Paths shipped by dpkg, including directories (path|package)

creation_time is the file modification time, in whole seconds. Caches live in
<output>/cache and are reused on the next run until --refresh.

Requirements:
  - dpkg-query (Debian/Ubuntu)
  - GNU find, xargs, and stat
  - sort, join, awk

Example:
  ./collect-on-host.sh -o ./exports/myhost -v
  ./collect-on-host.sh -o ./exports/myhost --refresh

EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        --root) ROOT_ARGS+=("$2"); shift 2 ;;
        --roots)
            IFS=':' read -r -a _extra <<< "$2"
            ROOT_ARGS+=("${_extra[@]}")
            shift 2
            ;;
        --refresh) REFRESH=true; shift ;;
        --dpkg-info) DPKG_INFO_DIR="$2"; shift 2 ;;
        --generic-dirs) GENERIC_DIRS_FILE="$2"; shift 2 ;;
        -v|--verbose) VERBOSE=true; shift ;;
        -d|--debug) DEBUG=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) log "Unknown option: $1"; exit 1 ;;
    esac
done

if $DEBUG; then
    set -x
    PS4='+ ${BASH_SOURCE}:${LINENO}: '
fi

abspath_dir() {
    local target="$1"
    if [[ ! -d "$target" ]]; then
        log "Not a directory: $target"
        exit 1
    fi
    (cd "$target" && pwd -P)
}

require_tools() {
    local missing=()
    command -v dpkg-query >/dev/null 2>&1 || missing+=("dpkg-query")
    command -v find >/dev/null 2>&1 || missing+=("find")
    command -v xargs >/dev/null 2>&1 || missing+=("xargs")
    command -v stat >/dev/null 2>&1 || missing+=("stat")
    command -v sort >/dev/null 2>&1 || missing+=("sort")
    command -v join >/dev/null 2>&1 || missing+=("join")
    command -v awk >/dev/null 2>&1 || missing+=("awk")
    if ((${#missing[@]})); then
        log "Missing required tools: ${missing[*]}"
        exit 1
    fi
    if ! find / -maxdepth 0 -printf '%p' >/dev/null 2>&1; then
        log "GNU find with -printf is required"
        exit 1
    fi
    if ! stat --printf='%Y' / >/dev/null 2>&1; then
        log "GNU stat with --printf is required"
        exit 1
    fi
    if ! xargs --help 2>&1 | grep -q -- '--process-slot-var'; then
        log "GNU xargs with --process-slot-var is required"
        exit 1
    fi
    if [[ ! -f "$GENERIC_DIRS_FILE" ]]; then
        log "Shared-directory list not found: $GENERIC_DIRS_FILE"
        exit 1
    fi
}

discover_roots() {
    local raw fstype unesc
    local -a found=()
    if ((${#ROOT_ARGS[@]})); then
        printf '%s\n' "${ROOT_ARGS[@]}"
        return
    fi
    if [[ -r /proc/mounts ]]; then
        while read -r _ raw fstype _; do
            case "$fstype" in
                ext2|ext3|ext4|xfs|btrfs|zfs|jfs|f2fs|bcachefs) ;;
                *) continue ;;
            esac
            unesc=$(printf '%b' "$raw")
            [[ -n "$unesc" ]] && found+=("$unesc")
        done < /proc/mounts
    fi
    if ((${#found[@]} == 0)); then
        found=("/")
    fi
    printf '%s\n' "${found[@]}"
}

SCRATCH=()
track() { SCRATCH+=("$1"); }
cleanup() {
    if ((${#SCRATCH[@]})); then
        rm -rf "${SCRATCH[@]}"
    fi
}
trap cleanup EXIT

require_tools

mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR=$(abspath_dir "$OUTPUT_DIR")
DPKG_INFO_DIR=$(abspath_dir "$DPKG_INFO_DIR")
GENERIC_DIRS_FILE=$(cd "$(dirname "$GENERIC_DIRS_FILE")" && pwd -P)/$(basename "$GENERIC_DIRS_FILE")
if [[ ! -f "$GENERIC_DIRS_FILE" ]]; then
    log "Shared-directory list not found: $GENERIC_DIRS_FILE"
    exit 1
fi

CACHE="${OUTPUT_DIR}/cache"
mkdir -p "$CACHE"

if [[ ! -f "$CACHE/format" || "$(<"$CACHE/format")" != "$CACHE_FORMAT" ]]; then
    log "Rebuilding caches (format ${CACHE_FORMAT})"
    rm -f \
        "$CACHE/packages.list" \
        "$CACHE/packages.meta" \
        "$CACHE/package_paths.tsv" \
        "$CACHE/unique_owners.tsv" \
        "$CACHE/filesystem_files.tsv" \
        "$CACHE/filesystem.roots"
    echo "$CACHE_FORMAT" > "$CACHE/format"
fi

if $REFRESH; then
    log "Refreshing caches"
    rm -f \
        "$CACHE/packages.list" \
        "$CACHE/packages.meta" \
        "$CACHE/package_paths.tsv" \
        "$CACHE/unique_owners.tsv" \
        "$CACHE/filesystem_files.tsv" \
        "$CACHE/filesystem.roots"
fi

mapfile -t ROOTS < <(discover_roots)
CANON_ROOTS=()
for _root in "${ROOTS[@]}"; do
    [[ -n "$_root" ]] || continue
    CANON_ROOTS+=("$(abspath_dir "$_root")")
done
if ((${#CANON_ROOTS[@]} == 0)); then
    log "No filesystem roots to scan"
    exit 1
fi
mapfile -t ROOTS < <(printf '%s\n' "${CANON_ROOTS[@]}" | sort -u)

log "Starting file collection on $(hostname)"
log "Output directory: $OUTPUT_DIR"

build_package_list() {
    local tmp
    tmp=$(mktemp "$CACHE/packages.list.XXXXXX")
    track "$tmp"
    log "Step 1/3: Collecting installed package list..."
    dpkg-query -W -f '${db:Status-Status}\t${binary:Package}\n' \
        | awk -F '\t' '$1 == "installed" && $2 != "" { print $2 }' \
        | sort -u > "$tmp"
    if [[ ! -s "$tmp" ]]; then
        log "No installed packages reported by dpkg-query"
        exit 1
    fi
    mv -f "$tmp" "$CACHE/packages.list"
    rm -f "$CACHE/package_paths.tsv" "$CACHE/unique_owners.tsv"
    log "Cached $(wc -l < "$CACHE/packages.list") installed packages"
}

build_package_paths() {
    local listfiles tmp
    listfiles=$(mktemp "$CACHE/listfiles.XXXXXX")
    tmp=$(mktemp "$CACHE/package_paths.XXXXXX")
    track "$listfiles" "$tmp"
    log "Indexing paths shipped by each cached package..."
    find "$DPKG_INFO_DIR" -maxdepth 1 -type f -name '*.list' -printf '%p\n' > "$listfiles"
    awk -v packages="$CACHE/packages.list" -v listfiles="$listfiles" '
        BEGIN {
            while ((getline pkg < packages) > 0) {
                if (pkg != "") installed[pkg] = 1
            }
            close(packages)
            while ((getline listpath < listfiles) > 0) {
                pkg = listpath
                sub(/^.*\//, "", pkg)
                sub(/\.list$/, "", pkg)
                if (!(pkg in installed)) continue
                while ((getline line < listpath) > 0) {
                    if (line != "") print line "\t" pkg
                }
                close(listpath)
            }
            close(listfiles)
        }
    ' | sort -T "$CACHE" -t $'\t' -k1,1 -k2,2 -u > "$tmp"
    if [[ ! -s "$tmp" ]]; then
        log "Installed packages have no file lists in $DPKG_INFO_DIR"
        exit 1
    fi
    mv -f "$tmp" "$CACHE/package_paths.tsv"
    rm -f "$CACHE/unique_owners.tsv"
    log "Cached $(wc -l < "$CACHE/package_paths.tsv") packaged paths"
}

build_unique_owners() {
    local tmp
    tmp=$(mktemp "$CACHE/unique_owners.XXXXXX")
    track "$tmp"
    log_verbose "Building unique package-directory index..."
    # Own only paths a package lists itself. Parent directories of a nested
    # file stay with whichever package listed that directory.
    awk -F '\t' '
        BEGIN { OFS = "\t" }
        $1 == "" || $1 == "/" || $1 == "/." || $2 == "" { next }
        $1 != prev {
            if (n == 1) print prev, only
            prev = $1
            only = $2
            n = 1
            next
        }
        { n++ }
        END { if (n == 1 && prev != "") print prev, only }
    ' "$CACHE/package_paths.tsv" > "$tmp"
    mv -f "$tmp" "$CACHE/unique_owners.tsv"
    log_verbose "Cached $(wc -l < "$CACHE/unique_owners.tsv") uniquely owned paths"
}

build_filesystem_list() {
    local tmp err root prune find_rc xargs_rc sorted slotdir slot_file
    tmp=$(mktemp "$CACHE/filesystem.XXXXXX")
    err=$(mktemp "$CACHE/find-errors.XXXXXX")
    slotdir=$(mktemp -d "$CACHE/slots.XXXXXX")
    track "$tmp" "$err" "$slotdir"
    rm -f "$CACHE/find-errors.txt"
    : > "$tmp"
    : > "$err"
    STAT_SLOT_DIR=$slotdir
    export STAT_SLOT_DIR
    log "Step 2/3: Collecting filesystem file list (${STAT_WORKERS} workers)..."
    for root in "${ROOTS[@]}"; do
        log_verbose "Scanning $root"
        if [[ "$OUTPUT_DIR" == "$root"/* ]]; then
            prune=$OUTPUT_DIR
        else
            prune=$CACHE
        fi
        # find only discovers paths. Each xargs slot appends to its own file so
        # parallel stat output cannot interleave. Times are whole seconds.
        set +e
        set +o pipefail
        find "$root" -xdev \
            \( -path "$prune" -prune \) -o \
            \( -type f -o -type l \) -print0 2>>"$err" \
        | xargs -0 -r -P "$STAT_WORKERS" -n "$STAT_BATCH" --process-slot-var=SLOT \
            sh -c 'stat --printf="%n\t%Y\t%X\n" -- "$@" >> "$STAT_SLOT_DIR/$SLOT" 2>>"$STAT_SLOT_DIR/err-$SLOT" || true' _
        local pipe_status=("${PIPESTATUS[@]}")
        set -o pipefail
        set -e
        find_rc=${pipe_status[0]:-1}
        xargs_rc=${pipe_status[1]:-1}
        if (( find_rc > 1 )); then
            log "find failed on $root (exit $find_rc)"
            exit 1
        fi
        if (( xargs_rc != 0 )); then
            log "xargs stat failed on $root (exit $xargs_rc)"
            exit 1
        fi
    done
    for slot_file in "$slotdir"/*; do
        [[ -f "$slot_file" ]] || continue
        case "$(basename "$slot_file")" in
            err-*) cat "$slot_file" >> "$err" ;;
            *) cat "$slot_file" >> "$tmp" ;;
        esac
    done
    rm -rf "$slotdir"
    if [[ -s "$err" ]]; then
        local err_count
        err_count=$(wc -l < "$err")
        mv -f "$err" "$CACHE/find-errors.txt"
        log "Some paths could not be read (${err_count}). Re-run with sudo for full coverage. Details: $CACHE/find-errors.txt"
    fi
    sorted=$(mktemp "$CACHE/filesystem.sorted.XXXXXX")
    track "$sorted"
    sort -T "$CACHE" -t $'\t' -k1,1 -u "$tmp" > "$sorted"
    mv -f "$sorted" "$CACHE/filesystem_files.tsv"
    log "Cached $(wc -l < "$CACHE/filesystem_files.tsv") filesystem files"
}

meta_tmp=$(mktemp "$CACHE/packages.meta.XXXXXX")
track "$meta_tmp"
printf '%s\n' "$DPKG_INFO_DIR" > "$meta_tmp"
if [[ -s "$CACHE/packages.list" && -f "$CACHE/packages.meta" ]] && cmp -s "$CACHE/packages.meta" "$meta_tmp"; then
    log "Step 1/3: Using cached package list ($(wc -l < "$CACHE/packages.list") packages). Pass --refresh after package changes."
else
    build_package_list
    mv -f "$meta_tmp" "$CACHE/packages.meta"
fi

if [[ ! -s "$CACHE/package_paths.tsv" ]]; then
    build_package_paths
else
    log_verbose "Using cached packaged-path index ($(wc -l < "$CACHE/package_paths.tsv") paths)"
fi

roots_tmp=$(mktemp "$CACHE/filesystem.roots.XXXXXX")
track "$roots_tmp"
printf '%s\n' "${ROOTS[@]}" > "$roots_tmp"
if [[ -f "$CACHE/filesystem_files.tsv" && -f "$CACHE/filesystem.roots" ]] && cmp -s "$CACHE/filesystem.roots" "$roots_tmp"; then
    log "Step 2/3: Using cached filesystem file list ($(wc -l < "$CACHE/filesystem_files.tsv") files). Pass --refresh to rescan."
else
    build_filesystem_list
    mv -f "$roots_tmp" "$CACHE/filesystem.roots"
fi

if [[ ! -f "$CACHE/unique_owners.tsv" || "$CACHE/package_paths.tsv" -nt "$CACHE/unique_owners.tsv" ]]; then
    build_unique_owners
fi

log "Step 3/3: Matching each filesystem file to a package..."
exact_tmp=$(mktemp "$CACHE/exact.XXXXXX")
unmatched_tmp=$(mktemp "$CACHE/unmatched.XXXXXX")
inferred_tmp=$(mktemp "$CACHE/inferred.XXXXXX")
pairs_tmp=$(mktemp "$CACHE/pairs.XXXXXX")
track "$exact_tmp" "$unmatched_tmp" "$inferred_tmp" "$pairs_tmp"

join -t $'\t' -1 1 -2 1 "$CACHE/filesystem_files.tsv" "$CACHE/package_paths.tsv" > "$exact_tmp"
join -t $'\t' -v 1 -1 1 -2 1 "$CACHE/filesystem_files.tsv" "$CACHE/package_paths.tsv" > "$unmatched_tmp"

awk -F '\t' -v generic_file="$GENERIC_DIRS_FILE" -v owner_file="$CACHE/unique_owners.tsv" '
    BEGIN {
        OFS = "\t"
        while ((getline line < generic_file) > 0) {
            if (line == "" || line ~ /^[[:space:]]*#/) continue
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
            if (line != "") generic[line] = 1
        }
        close(generic_file)
        while ((getline line < owner_file) > 0) {
            split(line, fields, "\t")
            if (fields[1] != "" && fields[2] != "") owner[fields[1]] = fields[2]
        }
        close(owner_file)
    }
    {
        path = $1
        dir = path
        while (sub(/\/[^\/]+$/, "", dir)) {
            if (dir == "" || dir == "/") break
            if (dir in generic) break
            if (dir in owner) {
                print path, owner[dir]
                break
            }
        }
    }
' "$unmatched_tmp" > "$inferred_tmp"

{
    awk -F '\t' 'NF >= 4 && $1 != "" && $4 != "" { print $1 "\t" $4 }' "$exact_tmp"
    awk -F '\t' 'NF >= 2 && $1 != "" && $2 != "" { print $1 "\t" $2 }' "$inferred_tmp"
} | sort -T "$CACHE" -u -t $'\t' -k1,1 -k2,2 > "$pairs_tmp"

files_info_tmp=$(mktemp "$CACHE/files_info.XXXXXX")
files_packages_tmp=$(mktemp "$CACHE/files_packages.XXXXXX")
all_pkg_tmp=$(mktemp "$CACHE/all_package_files.XXXXXX")
track "$files_info_tmp" "$files_packages_tmp" "$all_pkg_tmp"

{
    echo "path|creation_time|access_time"
    awk -F '\t' 'NF >= 3 { print $1 "|" $2 "|" $3 }' "$CACHE/filesystem_files.tsv"
} > "$files_info_tmp"

{
    echo "path,package"
    awk -F '\t' '{ print $1 "," $2 }' "$pairs_tmp"
} > "$files_packages_tmp"

{
    echo "path|package"
    awk -F '\t' '{ print $1 "|" $2 }' "$CACHE/package_paths.tsv"
} > "$all_pkg_tmp"

mv -f "$files_info_tmp" "${OUTPUT_DIR}/files_info.csv"
mv -f "$files_packages_tmp" "${OUTPUT_DIR}/files_packages.csv"
mv -f "$all_pkg_tmp" "${OUTPUT_DIR}/all_package_files.csv"

EXACT_COUNT=$(wc -l < "$exact_tmp")
INFERRED_COUNT=$(wc -l < "$inferred_tmp")
INFO_LINES=$(wc -l < "${OUTPUT_DIR}/files_info.csv")
PACKAGES_LINES=$(wc -l < "${OUTPUT_DIR}/files_packages.csv")
ALL_FILES_LINES=$(wc -l < "${OUTPUT_DIR}/all_package_files.csv")

log "Matched ${EXACT_COUNT} shipped files and ${INFERRED_COUNT} files created outside the package lists"
log "Collection complete!"
log "Output files:"
log "  files_info.csv:          $(du -h "${OUTPUT_DIR}/files_info.csv" | cut -f1) ($((INFO_LINES - 1)) files)"
log "  files_packages.csv:      $(du -h "${OUTPUT_DIR}/files_packages.csv" | cut -f1) ($((PACKAGES_LINES - 1)) files)"
log "  all_package_files.csv:   $(du -h "${OUTPUT_DIR}/all_package_files.csv" | cut -f1) ($((ALL_FILES_LINES - 1)) files)"
log ""
log "Next steps:"
log "  1. Transfer files to analysis host"
log "  2. Run: python -m unusedos import --source-dir $OUTPUT_DIR --dest-dir <fleet-data-dir>"
log "  3. Run: python -m unusedos analyze --input-dir $OUTPUT_DIR --host \$(hostname) --output-dir ./reports"
