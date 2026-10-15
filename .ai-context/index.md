# UnUsedOS — Repository Context Index

> **Last verified revision:** `d2e849327a94a41153dede6b82854484413cce9a` (branch: `main`)
>
> **Staleness check:** Compare this revision to current `HEAD`. Context covering
> paths changed since this revision is suspect — verify against source before
> relying on it. See `.ai-context/manifest.yaml` for `source_paths` per artifact.

## Critical orientation (read first)

The `main` branch is **documentation-only**. It contains exactly two tracked
files: `README.md` and `TechnicalMarketingReadMe.md`. **No application code,
tests, configuration, or infrastructure exists on `main`.**

The README *describes* a full Linux system analysis toolkit (Python scripts,
shell scripts, Jupyter notebooks, data files). That implementation lives on the
`origin/Public` branch (282 files), which was inspected read-only for context
enrichment but is **not** the analyzed branch. Treat all component/workflow/
convention detail below as **DECLARED** (from README) or **INFERRED** (from
`origin/Public`), never as OBSERVED-on-`main` behavior.

See `.ai-context/decisions/conflicts.yaml` for the recorded contradiction
between the README's described project structure and `main`'s actual contents.

## Routing

| Need | Go to |
|------|-------|
| Minimum info before editing | [quickstart.md](quickstart.md) |
| System shape & deployable units | [architecture/system-overview.md](architecture/system-overview.md) |
| Backend / analysis scripts | [architecture/backend.md](architecture/backend.md) |
| Data files & formats | [architecture/data.md](architecture/data.md) |
| Infrastructure / system deps | [architecture/infrastructure.md](architecture/infrastructure.md) |
| Component responsibilities | [components/index.md](components/index.md) |
| End-to-end execution paths | [workflows/index.md](workflows/index.md) |
| If-I-change-X-what-else | [change-impact/relationships.yaml](change-impact/relationships.yaml) |
| Coding patterns & conventions | [conventions/coding-patterns.md](conventions/coding-patterns.md) |
| Dependency rules | [conventions/dependencies.md](conventions/dependencies.md) |
| Configuration patterns | [conventions/configuration.md](conventions/configuration.md) |
| Observability | [conventions/observability.md](conventions/observability.md) |
| What tests to run | [testing/test-map.yaml](testing/test-map.yaml) |
| Architecture decisions | [decisions/architecture-decisions.md](decisions/architecture-decisions.md) |
| Recorded contradictions | [decisions/conflicts.yaml](decisions/conflicts.yaml) |
| Technical debt & risks | [debt/register.yaml](debt/register.yaml) |
| Unresolved unknowns | [unknowns/register.yaml](unknowns/register.yaml) |
| What changed this refresh | [deltas/latest.yaml](deltas/latest.yaml) |
| Pass plan & coverage | [manifest.yaml](manifest.yaml) |

## Domains (DECLARED in README; INFERRED from origin/Public)

1. **File usage analysis** — `FileUsageReport.sh`, `access_times.py` collect
   filesystem `atime` to find never-accessed files.
2. **Package usage analysis** — `PackageUsageReport.py`,
   `ModifiedPackageUsageReport.py`, `ModifiedPackageUsageReportWithValidation.py`
   cross-reference packages with file access data.
3. **Interactive notebooks** — `UnusedFilesAndPackages*.ipynb`,
   `UnusedPackageReport.ipynb`, `WhatsUnused.ipynb` (pandas-based exploration).
4. **Security patch pipeline** — `CreateSecurityPatch/` builds installable
   patches from `unattended-upgrades`.
5. **Stats collection** — `StatsCollector/` installs VM collectors and gathers
   longitudinal file-usage statistics.
6. **Access validation** — `AccessValidate/` (zabbix/ESXi metric collection).

## Evidence legend

- **OBSERVED** — directly supported by files on `main`.
- **DECLARED** — stated by README/TechnicalMarketingReadMe.
- **INFERRED** — suggested by `origin/Public` branch contents (read-only).
- **UNKNOWN** — insufficient evidence.
