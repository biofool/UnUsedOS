# Architecture — Backend / Analysis Scripts

> **Evidence note:** No Python source exists on `main`. All below is
> **DECLARED** in `README.md` or **INFERRED** from `origin/Public` (read-only
> `git show`). No **OBSERVED** runtime behavior on `main`.

## Analysis scripts (INFERRED from origin/Public)

### `access_times.py` — shared access-time utilities
- `read_csv_filter_convert(file_path, column_names, numeric_tail, delimiter)`
  reads a delimited file line-by-line, keeps rows with the expected column
  count, coerces trailing numeric columns, returns `(DataFrame, non_convertible_count)`.
- `print_intervals(df, intervals)` buckets access times into day intervals.
- Module-level constant `KERNEL_VER = '/boot/vmlinuz-.*'` (regex for kernel files).
- **Consumers:** `UnusedFilesAndPackages.py` imports `access_times`.

### `UnusedFilesAndPackages.py` — main analysis
- Hardcoded `input_dir = "insights-rand-1"`, reads `all_package_files.log` and
  `usage.log` via `access_times.read_csv_filter_convert`.
- Normalizes access times to days, filters files accessed >45 days before the
  max as "unneeded".
- Uses `pandas`, `matplotlib.pyplot`.

### `PackageUsageReport.py` — basic package report
- Reads `files_packages.csv` (cols: path, package) and `files_info.csv`
  (`|`-delimited; cols: path, creation_time, access_time).
- Outer-merge on `path`, group by `package`, min `access_time`, sort ascending.

### `ModifiedPackageUsageReportWithValidation.py` — validated report
- Adds `argparse` (`-D/--directories`), a `read_validate_csv` with a **5% error
  threshold** (skips files exceeding it), and a 90-day staleness filter.
- Most robust of the package-report scripts.

### Other scripts (DECLARED)
- `ModifiedPackageUsageReport.py`, `WhatsUnusedSurvey.py`, `DescribeDataFrames.py`
  (prints DataFrame structure as JSON), `compare_package_dictionaries.py`,
  `buffer_unitizer.py`, `csv2psv.py`.

## Patterns observed (INFERRED)

- Scripts are standalone; no shared CLI framework beyond `argparse` in one script.
- Input paths are hardcoded (e.g. `input_dir = "insights-rand-1"`).
- Output is via `print()`; no structured logging.
- Data format: CSV (comma) for package mappings, PSV (`|`) for file info.
- No error classes; errors surface as pandas exceptions or skipped rows.

## No backend service

There is no HTTP API, server, daemon, or queue. All analysis is batch/offline.
(INFERRED; no server code found on `origin/Public`.)
