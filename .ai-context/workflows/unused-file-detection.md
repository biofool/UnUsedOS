# Workflow — Unused File / Package Detection

> **Evidence:** DECLARED in `README.md`; INFERRED from `origin/Public` (read-only).
> Not OBSERVED on `main`.

## Entry Point
Manual invocation on a target Linux host:
`bash FileUsageReport.sh /path/to/analyze` then offline `python PackageUsageReport.py`.

## Execution Path
```
FileUsageReport.sh  (sudo find / -xdev ! -atime -28 ... )
    ↓  writes /var/log/vems/{NoRead,Read}28Days_<host>.log  (PSV: path|datetime)
convert logs to CSV/PSV inputs  (ConCSV2PSV.sh / csv2psv.py)
    ↓  files_packages.csv (path,package) + files_info.csv (path,creation_time,access_time)
PackageUsageReport.py / ModifiedPackageUsageReportWithValidation.py
    ↓  pandas.merge on 'path'  →  groupby('package').min('access_time')  →  sort
ranked unused-package list  (print)
    ↓  human review / notebooks (UnusedFilesAndPackages.ipynb, WhatsUnused.ipynb)
removal decision
```

## Evidence
- `FileUsageReport.sh`: `find / -xdev ! -atime -28 -type f -printf '%p|%AY-%Am-%Ad,%AH:%M:%AS\n'` (INFERRED, origin/Public).
- `PackageUsageReport.py`: `pd.merge(files_packages, files_info, on='path')` then `groupby('package')['access_time'].min()` (INFERRED).
- `ModifiedPackageUsageReportWithValidation.py`: `argparse -D/--directories`, 5% error threshold, 90-day filter (INFERRED).
- `access_times.read_csv_filter_convert`: line-by-line delimited reader (INFERRED).

## Failure Paths
- **atime disabled (`noatime`):** access times are meaningless → false "unused" results. DECLARED limitation.
- **Malformed rows:** `read_csv_filter_convert` drops rows not matching column count; non-numeric trailing cols counted as `non_convertible_count`. Validation script skips a file if error rate > 5%.
- **Missing input files:** hardcoded paths (e.g. `insights-rand-1`) → FileNotFoundError. No graceful handling evidenced.
- **No retry/timeout:** batch scripts; no retry logic.

## Change Guidance
Review together before modifying: `FileUsageReport.sh` (output format), the
CSV/PSV converters, and the consuming Python scripts (column/delimiter
conventions). A change to the `-printf` format breaks all downstream parsers.
