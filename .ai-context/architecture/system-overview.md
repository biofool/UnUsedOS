# Architecture — System Overview

> **Evidence note:** On `main`, only `README.md` and `TechnicalMarketingReadMe.md`
> exist. System context below is **DECLARED** in those files, with
> **INFERRED** detail from the `origin/Public` branch (read-only). No
> **OBSERVED** runtime behavior exists on `main`.

## System Context

UnUsedOS targets system/security engineers maintaining SCS (Supercomputing
System) appliance OS images on Ubuntu (Lucid/Precise/Xenial). The system
ingests filesystem access timestamps and package-to-file mappings, analyzes
them with pandas to find unused files/packages, and produces installable
security patches that strip bloat.

### Users / external systems (DECLARED)

| Actor | Role |
|-------|------|
| System engineer | Runs collection + analysis on SCS appliances |
| Security engineer | Uses reports to harden images; applies patches |
| DevOps / platform owner | Deploys StatsCollector on VMs for longitudinal data |
| Target Linux hosts | Provide `atime` data via `find`/`stat`; receive patches via `dpkg`/`ssh` |
| `dpkg` / apt | Source of package-to-file mappings and security `.deb` packages |

### Trust boundary

Collection scripts run **as root** on target hosts (`sudo find /`, `sudo dpkg`).
Patch installation scripts `ssh` into remote hosts and run `sudo dpkg -i`.
(INFERRED from `origin/Public`.) No authentication/authorization layer exists
in the toolkit itself — it relies on OS-level sudo and SSH access.

## Deployable Units (DECLARED / INFERRED)

There is no packaged/deployed service. The "units" are standalone scripts and
notebooks run manually:

| Unit | Type | Entry point |
|------|------|-------------|
| File usage collector | Bash script | `FileUsageReport.sh` |
| Package usage analyzers | Python scripts | `PackageUsageReport.py`, `ModifiedPackageUsageReport*.py` |
| Main analysis | Python script | `UnusedFilesAndPackages.py` |
| Interactive exploration | Jupyter notebooks | `UnusedFilesAndPackages*.ipynb`, `WhatsUnused.ipynb` |
| Security patch builder | Bash script | `CreateSecurityPatch/CreateSecurityPatchBundle.sh` |
| Patch installer | Bash script | `CreateSecurityPatch/SecurityPatchInstaller.sh` |
| VM stats collector | Bash/zsh scripts | `StatsCollector/installVMCollector.sh`, `VEMSStatsCollector*.sh` |
| Access validation | Bash/PowerShell | `AccessValidate/*.sh`, `*.ps1` |

## High-level data flow (DECLARED)

```
target Linux host
   │  find -atime  (FileUsageReport.sh)
   ▼
CSV/PSV access-time + package-mapping files
   │  pandas merge on 'path'  (PackageUsageReport.py etc.)
   ▼
packages sorted by oldest file access time
   │  (human review / notebooks)
   ▼
unused-package list
   │  unattended-upgrades + dpkg  (CreateSecurityPatch/)
   ▼
installable security patch → remote host via ssh/dpkg
```

## Diagram vs inventory

The flow above is a DECLARED summary. The authoritative structured inventory
is the Deployable Units table and the component files under
`components/`. If they disagree, the inventory wins.
