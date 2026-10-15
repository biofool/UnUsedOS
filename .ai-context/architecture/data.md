# Architecture — Data

> **Evidence note:** No data files exist on `main`. Below is **DECLARED** in
> `README.md`/`TechnicalMarketingReadMe.md` and **INFERRED** from `origin/Public`
> file listings (read-only). No **OBSERVED** data on `main`.

## Data formats (DECLARED + INFERRED)

| Format | Delimiter | Used for | Columns (INFERRED) |
|--------|-----------|----------|--------------------|
| CSV | `,` | package→file mappings | `path, package` |
| PSV | `\|` | file access/creation times | `path, creation_time, access_time` |
| TXT | n/a | SCS package file lists | one path per line |
| JSON | n/a | dictionaries (`Dictionaries/VS8.json`, `VSNull.json`) | UNKNOWN schema |
| XLSX | n/a | `input.xlsx`, `output.xlsx` | UNKNOWN |
| Log | n/a | `usage.log`, `all_package_files.log` | collected by shell scripts |

## Key data files (INFERRED from origin/Public listing)

- `files_packages.csv`, `files_info.csv` — inputs to `PackageUsageReport.py`.
- `allpackages.txt`, `protected_packages.txt` — package reference / allowlist.
- `all_package_files.csv`, `oldest_access_times.csv` — derived outputs.
- `vems-scs-full_*.txt` (on `origin/Public`) — SCS package file lists across
  versions 4.2.0 → 7.11.6 (Lucid/Precise/Xenial). The `main` README refers to
  these as `bloated-scs-full_*.txt` — see `decisions/conflicts.yaml`.

## Data lifecycle (UNKNOWN)

No evidence of retention policy, backup, or migration handling. Data files
appear to be committed alongside scripts on `origin/Public` (DECLARED
limitation: "Large number of bloated-scs-full_*.txt data files increases repo
size"). No database is used.

## Data ownership

All data is file-based and co-located with scripts. No external data store.
(DECLARED/INFERRED.)
