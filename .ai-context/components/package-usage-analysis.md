# Component — Package Usage Analysis

> **Evidence:** DECLARED in `README.md`; INFERRED from `origin/Public` (read-only).
> Not OBSERVED on `main`.

## Responsibility
Merge package→file mappings with file access-time data (pandas) to rank
packages by oldest file access time, identifying unused packages.

## Primary files (INFERRED from origin/Public)
- `PackageUsageReport.py` — basic: reads `files_packages.csv` + `files_info.csv` (PSV), outer-merge on `path`, groupby `package` min `access_time`, sort.
- `ModifiedPackageUsageReport.py` — modified variant.
- `ModifiedPackageUsageReportWithValidation.py` — adds `argparse` (`-D/--directories`), `read_validate_csv` with 5% error threshold, 90-day staleness filter.
- `WhatsUnusedSurvey.py` — survey script.
- `compare_package_dictionaries.py`, `buffer_unitizer.py` — helpers.

## Public interfaces
None formal. Scripts are run directly; `ModifiedPackageUsageReportWithValidation.py` accepts `-D/--directories`.

## Dependencies
- **code:** `pandas`, `argparse`, `datetime`.
- **data:** `files_packages.csv`, `files_info.csv`, `allpackages.txt`, `protected_packages.txt`.
- **runtime:** offline Python 3.

## Consumers
- Human reviewers / notebooks consume the ranked output.
- `CreateSecurityPatch/` consumes the unused-package decision (human-in-the-loop).

## State / data ownership
Reads derived CSVs; writes none persistently (output via `print`).

## Architectural boundaries
Offline analysis layer; depends on collection-layer outputs but does not run on target hosts.

## Security-sensitive behavior
Outputs package names ranked by non-use — used to decide removal. False
positives could cause removal of needed packages. The validation script's 5%
threshold mitigates data-quality issues. (INFERRED.)

## Change-impact
See [../change-impact/relationships.yaml](../change-impact/relationships.yaml)
entry `package-usage-analysis`. Before modifying: confirm CSV column
conventions (`path, package` / `path, creation_time, access_time`) and the
delimiter difference (CSV vs PSV) across producer/consumer scripts.
