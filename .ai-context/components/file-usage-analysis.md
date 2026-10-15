# Component — File Usage Analysis

> **Evidence:** DECLARED in `README.md`; INFERRED from `origin/Public` (read-only).
> Not OBSERVED on `main`.

## Responsibility
Collect filesystem access timestamps (`atime`) across a directory tree and
emit delimited reports identifying files not accessed within a window.

## Primary files (INFERRED from origin/Public)
- `FileUsageReport.sh` — `sudo find / -xdev ! -atime -28 -type f -printf '%p|%AY-%Am-%Ad,%AH:%M:%AS\n'` → `NoRead28Days_<host>.log`; and `-atime -28` → `Read28Days_<host>.log`. Output dir: `/var/log/vems/`.
- `access_times.py` — `read_csv_filter_convert()`, `print_intervals()`.
- `ConCSV2PSV.sh`, `csv2psv.py` — CSV→PSV conversion helpers.
- `MakeShar.sh`, `packages_exploder.sh` — archive/explode helpers.

## Public interfaces
- `access_times.read_csv_filter_convert(file_path, column_names, numeric_tail, delimiter)` → `(DataFrame, non_convertible_count)`.

## Dependencies
- **code:** `pandas` (Python); coreutils `find`, `stat`, `tee` (Bash).
- **runtime:** root/sudo on target host; `atime` enabled on filesystem.
- **data:** writes to `/var/log/vems/*.log`.

## Consumers
- `UnusedFilesAndPackages.py` imports `access_times`.
- Package-usage scripts consume the emitted CSV/PSV files.

## State / data ownership
Owns the raw access-time log files under `/var/log/vems/`. No persistent state
beyond files.

## Architectural boundaries
Collection (Bash, root, on-host) is separated from analysis (Python, offline).

## Security-sensitive behavior
Runs `sudo find /` over the entire filesystem. Output logs contain full file
paths of every file on the system — sensitive if exfiltrated. (INFERRED.)

## Change-impact
See [../change-impact/relationships.yaml](../change-impact/relationships.yaml)
entry `file-usage-analysis`. Before modifying: check `access_times.py` API
callers and the log path convention used by downstream scripts.
