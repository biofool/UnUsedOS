# Component — Stats Collector

> **Evidence:** DECLARED in `README.md`; INFERRED from `origin/Public` (read-only).
> Not OBSERVED on `main`.

## Responsibility
Install longitudinal VM statistics collectors (vmstat logging) and gather
bloated-file usage statistics over time.

## Primary files (INFERRED from origin/Public)
- `StatsCollector/installVMCollector.sh` — creates `/usr/local/bin/vmstat_vs.sh` (`vmstat 10 | logger -t VEMS`), a systemd service `vmstat-vs.service` (`Restart=always`), enables + starts it.
- `StatsCollector/VEMSStatsCollector.zsh`, `VEMSStatsCollectorInc.sh`, `VEMSFileUsageStats.sh` — collection scripts (zsh/bash).
- `StatsCollector/installFireBirdLogger.sh` — installs a FireBird logger.
- `StatsCollector/Vagrantfile` — VM provisioning.
- `StatsCollector/VMStatsDisplay/` — `vmstat_dashboard.py`, `ExtractVEMSStats.py`, sample logs/plots, `test_vmstat_disp.sh`.

## Public interfaces
None. Installs a systemd service on the target VM.

## Dependencies
- **runtime:** `vmstat`, `logger`, `systemd`, `sudo`.
- **data:** logs via syslog tag `VEMS`; extracted stats in `VMStatsDisplay/`.
- **infra:** Vagrant for VM provisioning.

## Consumers
- `VMStatsDisplay/` scripts consume the collected logs for dashboards.
- Analysis scripts consume longitudinal data to identify removal candidates.

## State / data ownership
Installs a persistent systemd service (`vmstat-vs.service`) on the target VM.
Owns collected log/extracted-stat files.

## Operationally-sensitive behavior
- Creates and enables a systemd service (persists across reboots).
- Runs `vmstat 10` indefinitely (continuous resource use).

## Change-impact
See [../change-impact/relationships.yaml](../change-impact/relationships.yaml)
entry `stats-collector`. Before modifying: confirm the systemd service name
matches across install + display scripts; check the `VEMS` syslog tag contract.
