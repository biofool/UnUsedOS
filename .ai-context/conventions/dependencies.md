# Conventions — Dependencies

> **Evidence:** DECLARED in `README.md`; INFERRED from `origin/Public`. No
> `requirements.txt`/`setup.py`/`pyproject.toml` on `main`.

## Python dependencies (DECLARED)
- `pandas` — DECLARED in README setup (`pip install pandas`).
- `matplotlib` — INFERRED (`import matplotlib.pyplot as plt` in `UnusedFilesAndPackages.py`).
- `jupyter` — DECLARED (notebook usage).

## System dependencies (DECLARED)
- `find`, `stat`, `dpkg`, `shar`, `csvkit` — DECLARED in README prerequisites.
- `rsync`, `ssh`, `unattended-upgrades`, `vmstat`, `systemd` — INFERRED from scripts.

## Dependency rules (INFERRED, weak)
- No formal layering. Scripts are standalone; the only observed code dependency
  is `UnusedFilesAndPackages.py` → `access_times` (import).
- No prohibited-direction rules evidenced. **unknown** whether any are intended.
- No shared library beyond `access_times.py`.

## No dependency manifest
There is no pinned dependency file on `main`. Dependency versions are
**UNKNOWN**. Do not assume reproducibility.
