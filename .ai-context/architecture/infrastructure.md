# Architecture — Infrastructure

> **Evidence note:** No infrastructure-as-code, CI/CD, Dockerfile, or deploy
> config exists on `main`. Below is **DECLARED** in `README.md` or **INFERRED**
> from `origin/Public` (read-only). No **OBSERVED** infra on `main`.

## Runtime requirements (DECLARED)

- **OS:** Linux (tested on Ubuntu Lucid/Precise/Xenial) on SCS appliances.
- **Python:** Python 3 with `pandas` (and `matplotlib`, `jupyter` — INFERRED).
- **System tools:** `find`, `stat`, `dpkg`, `shar`, `csvkit`, `rsync`, `ssh`,
  `unattended-upgrades`, `vmstat`, `systemd`.
- **Filesystem:** `atime` must be enabled (often disabled via `noatime`).

## Infrastructure components (INFERRED from origin/Public)

### StatsCollector VM provisioning
- `StatsCollector/Vagrantfile` — Vagrant-based VM provisioning (INFERRED; not
  inspected in detail).
- `installVMCollector.sh` — creates a systemd service `vmstat-vs.service` that
  runs `vmstat 10 | logger -t VEMS` and enables it at boot.
- `installFireBirdLogger.sh` — installs a FireBird logger (INFERRED).

### Security patch infrastructure
- `CreateSecurityPatch/upgrade.conf` — `unattended-upgrades` config copied to
  `/etc/apt/apt.conf.d/50unattended-upgrades`.
- Patch bundle is built on a "patch generator" host, then `rsync`'d to a
  destination host and installed via `ssh ... sudo dpkg -i`.

## CI/CD

**None.** DECLARED limitation: "No automated CI — analysis is run manually or
via notebooks." No `.github/`, `Makefile`, or CI config on `main`.

## Deployment topology (UNKNOWN)

No evidence of a defined deployment topology beyond manual script execution on
target hosts. Do not assume production readiness.
