# Coding-Agent Quickstart — UnUsedOS

> **Staleness check:** Read `last_verified_revision` in
> [index.md](index.md) / [manifest.yaml](manifest.yaml). Compare to current
> `HEAD`. If files in an artifact's `source_paths` changed since, treat that
> artifact as suspect — use it for routing only, verify against source before
> load-bearing claims.

## System shape

UnUsedOS is a Linux system analysis toolkit that identifies unused files and
packages on SCS (Supercomputing System) appliances using filesystem access
timestamps (`atime`) and package-usage data, then produces security patches to
remove bloat. Mixed tooling: Bash (collection), Python 3 + pandas (analysis),
Jupyter (interactive exploration).

**WARNING:** The `main` branch is **documentation-only** (`README.md`,
`TechnicalMarketingReadMe.md`). The described implementation lives on
`origin/Public`. To edit code, check out `origin/Public` first. Editing `main`
means editing documentation only.

## Major entry points (DECLARED in README; INFERRED from origin/Public)

- `FileUsageReport.sh` — collect file access-time report for a directory tree.
- `PackageUsageReport.py` / `ModifiedPackageUsageReportWithValidation.py` — package usage reports.
- `UnusedFilesAndPackages.py` — main analysis script (pandas).
- `CreateSecurityPatch/CreateSecurityPatchBundle.sh` — build security patch bundle.
- `CreateSecurityPatch/SecurityPatchInstaller.sh` — install patch on a host.
- `StatsCollector/installVMCollector.sh` — install vmstat logging service.

## Major architectural boundaries

- Shell scripts = data collection on target Linux hosts (need root, `atime`).
- Python scripts = offline pandas analysis of collected CSV/PSV data.
- Jupyter notebooks = interactive exploration of the same data.
- `CreateSecurityPatch/` = patch generation + installation (separate concern).
- `StatsCollector/` = longitudinal data collection on VMs.

## Important dependency rules

- Python analysis scripts depend on `pandas` (DECLARED) and `matplotlib`
  (INFERRED). No `requirements.txt` on `main`.
- Shell scripts depend on coreutils (`find`, `stat`), `dpkg`, `shar`, `rsync`,
  `ssh`, `unattended-upgrades` (DECLARED/INFERRED).
- No formal layering enforced; scripts are standalone (INFERRED).

## Repository coding patterns

See [conventions/coding-patterns.md](conventions/coding-patterns.md). Summary:
standalone scripts, CSV/PSV (`|`-delimited) data, hardcoded input paths,
`print`-based output. No package structure, no tests observed on `main`.

## Essential test/build commands

**UNKNOWN / none on `main`.** No package manifest, Makefile, or CI config
exists on `main`. See [testing/test-map.yaml](testing/test-map.yaml) — all
entries are UNKNOWN. If working on `origin/Public`, verify available commands
there before relying on this.

## Highest-risk areas

1. **Branch divergence** — `main` (docs) vs `origin/Public` (code). Editing
   `main` thinking code is present will fail. See
   [decisions/conflicts.yaml](decisions/conflicts.yaml).
2. **Security patch scripts** — `CreateSecurityPatch/*.sh` run `sudo apt`,
   `dpkg -i`, `ssh` to remote hosts, and contain commented-out credential
   creation (INFERRED from origin/Public). High blast radius if modified.
3. **`atime` dependency** — analysis correctness depends on `atime` being
   enabled (often disabled via `noatime`). DECLARED limitation.

## How to navigate .ai-context/

`index.md` → staleness check → identify domain → component/workflow →
change-impact map → conventions → test-map → source code.
