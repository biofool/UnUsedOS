# Conventions — Configuration

> **Evidence:** INFERRED from `origin/Public`. No config files on `main`.

## Configuration-loading patterns (INFERRED, weak)
- No centralized config module. Configuration is **hardcoded** in scripts:
  - `UnusedFilesAndPackages.py`: `input_dir = "insights-rand-1"`, suffix constants.
  - `FileUsageReport.sh`: output dir `/var/log/vems/`, 28-day window.
  - `ModifiedPackageUsageReportWithValidation.py`: 5% error threshold, 90-day filter.
- One external config file: `CreateSecurityPatch/upgrade.conf` → copied to
  `/etc/apt/apt.conf.d/50unattended-upgrades`.

## Environment variable handling (UNKNOWN)
- No evidence of env-var-driven configuration. **unknown**.

## Environment-specific behavior (UNKNOWN)
- No evidence of dev/staging/prod switching. Scripts appear environment-agnostic
  but assume SCS appliance targets. **unknown**.
