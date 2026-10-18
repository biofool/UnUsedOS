# Host File Access Time Collection

`scripts/collect-on-host.sh` collects file metadata and package mappings on any Debian/Ubuntu host for later analysis with UnusedOS.

## Quick Start

```bash
# On the target host, clone the repo and run:
git clone https://github.com/vigilent/Security.git
cd Security/UnusedOS

# Collect data for the current host
bash scripts/collect-on-host.sh -o ./exports

# Or specify a custom output directory
bash scripts/collect-on-host.sh -o /var/log/unusedos-export/$(hostname)
```

## What It Collects

Three CSV files are generated:

| File | Purpose | Format |
|------|---------|--------|
| `files_info.csv` | Every regular file and symlink on the scanned disks | `path\|creation_time\|access_time` |
| `files_packages.csv` | File-to-package mappings, including files a package created but did not ship | `path,package` |
| `all_package_files.csv` | Paths shipped by installed packages, including directories | `path\|package` |

`creation_time` is the file modification time. Times are Unix epoch timestamps in whole seconds. Intermediate caches are stored in `<output>/cache` and reused until you pass `--refresh`.

## Usage

```bash
./scripts/collect-on-host.sh [OPTIONS]

Options:
  -o, --output-dir DIR    Output directory (default: current directory)
  --root PATH             Limit the scan to this tree (repeatable). Default: local disk mounts
  --refresh               Rebuild cached package and file lists
  -v, --verbose           Print progress messages
  -d, --debug             Enable bash debug output
  -h, --help              Show help and exit
```

## Examples

### Collect to standard location
```bash
bash scripts/collect-on-host.sh -o /var/log/unusedos-export/$(hostname) -v
```

### Rescan after package or file changes
```bash
bash scripts/collect-on-host.sh -o /var/log/unusedos-export/$(hostname) --refresh -v
```

### Limit the scan to one tree
```bash
bash scripts/collect-on-host.sh -o ./exports --root /usr --root /var -v
```

### Debug a collection
```bash
bash scripts/collect-on-host.sh -o ./test-export -d
```

### Collect and immediately analyze
```bash
OUTPUT_DIR="/tmp/myhost-$(date +%s)"
bash scripts/collect-on-host.sh -o "$OUTPUT_DIR" -v
.venv/bin/python -m unusedos analyze \
  --input-dir "$OUTPUT_DIR" \
  --host "$(hostname)" \
  --output-dir ./reports
```

## How It Works

1. **Cache the package list** — Records installed package names from `dpkg-query`, then the paths each package ships (`/var/lib/dpkg/info/*.list`).
2. **Cache the file list** — `find` lists every regular file and symlink, including files that are not in a package's file list. Eight `xargs` workers then run `stat` in batches of 1024 and record whole-second modification and access times.
3. **Match each file to a package** — Looks up each cached filesystem path in the cached package lists. A file that is not shipped is still attributed when the nearest parent directory is listed by exactly one package, and that directory is not a shared system directory such as `/usr`, `/home`, or `/var/log`. That is how logs, state, and other files created by a package are tied back to it. A nested file does not make its parent directories belong to that package. The shared-directory stop list is `scripts/collect-generic-dirs.txt`.

A later run reuses `<output>/cache` and does not walk the disk or query dpkg again. Pass `--refresh` after installing, removing, or upgrading packages, or when new files should be included.

## Performance Notes

- **Time**: usually a few minutes. `find` discovers paths, and 8 parallel `stat` workers read timestamps.
- **I/O**: one `find` over each local disk, batched `stat` calls, plus a read of the dpkg file lists
- **Memory**: sorting the cached lists, typically a few hundred MB
- **Disk**: output CSVs plus the cache directory

Limit a run with `--root` when you do not need every disk. Pass `--refresh` only when the package set or the filesystem has changed.

## Transferring to Analysis Host

After collection, transfer the CSVs to your analysis machine:

```bash
# On collection host, create archive
cd /var/log/unusedos-export
tar czf myhost-$(date +%Y%m%d).tar.gz myhost/

# Transfer to analysis host
scp myhost-*.tar.gz analysis-host:/data/unusedos-exports/
```

## Analyzing Collected Data

### Single-host analysis
```bash
.venv/bin/python -m unusedos analyze \
  --input-dir /path/to/export/myhost \
  --host myhost \
  --output-dir ./reports
```

### Fleet-wide analysis
```bash
# Import multiple hosts' data
bash scripts/import_logs.sh /data/unusedos-exports /tmp/fleet-data

# Generate fleet summary
.venv/bin/python -m unusedos analyze-fleet \
  --root-dir /tmp/fleet-data \
  --output-dir ./reports
```

## Troubleshooting

### Permission denied errors
The script requires filesystem access to run `stat` on all files. Some files may be inaccessible to unprivileged users.

```bash
# Run with sudo for complete coverage
sudo bash scripts/collect-on-host.sh -o ./exports -v
```

### Out of memory on large systems
If the script runs out of memory during sorting, reduce the problem size:

```bash
# Collect only files modified in the last 30 days
find / -mtime -30 2>/dev/null | while read f; do
  dpkg -S "$f" 2>/dev/null | cut -d: -f1 | while read pkg; do
    stat -c "$f|%Y|%X|$pkg"
  done
done > partial_files.csv
```

### Filesystem with relatime
Most modern filesystems use `relatime` (relative atime), which means:
- Access times are only updated if > 24 hours since last change
- Recent accesses may not be recorded
- The data gives a conservative estimate of "truly unused" files

Check your filesystem:
```bash
.venv/bin/python -m unusedos check-atime
```

## Safe removal list

After a collection, list unused packages whose removal stays inside the unused set:

```bash
.venv/bin/python -m unusedos safe-remove --input-dir ./exports/myhost --unused-before 2025-10-02
```

`safe-remove.txt` is one package name per line and can be edited. `safe-remove-details.tsv` names the other unused packages apt would remove with each entry. The command confirms the list with `apt-get -s remove` only.

## Architecture Notes

See `docs/ATIME-RELIABILITY.md` for discussion of atime tracking reliability across filesystems and kernel versions.

For integration with automated collectors (e.g., VEMSStatsCollector), see `docs/VEMSStatsCollector-INTEGRATION.md`.
