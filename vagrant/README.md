# UnusedOS fleet suite on Debian (Vagrant)

Run the UnusedOS fleet test suite against **real Debian Bookworm VMs** instead of local synthetic containers.

## Prerequisites

- [Vagrant](https://developer.hashicorp.com/vagrant/install)
- [VirtualBox](https://www.virtualbox.org/) or libvirt/KVM
- ~3 GB RAM free (three `e2`-sized VMs at 1 GB each)

## Quick start

```bash
cd UnusedOS/vagrant
vagrant up
bash scripts/run-vagrant-fleet-suite.sh
```

Or one command from UnusedOS root:

```bash
bash vagrant/scripts/run-vagrant-fleet-suite.sh
```

## What it does

| VM | Role | Package exercised |
|----|------|-------------------|
| `container-web` | web tier | `curl` |
| `container-api` | API tier | `jq` |
| `container-worker` | worker tier | `dnsutils` (`dig`) |

Each VM also installs `tree` without using it (shared unused baseline).

Per VM:

1. `packages_exploder.sh` — dpkg inventory
2. `find` on `/usr/bin` and `/usr/lib` — usage log
3. `python -m unusedos analyze` — per-host report

Artifacts land in `vagrant/archives/<hostname>/` (synced folder). The host runs:

```bash
python -m unusedos summarize --archive-root vagrant/archives --output-dir vagrant/archives/fleet-report
```

## Outputs

- `archives/<host>/*-usage.log`
- `archives/<host>/*-all_package_files.log`
- `archives/<host>/reports/package_rankings.csv`
- `archives/fleet-report/fleet_summary.md`
- `archives/fleet-report/fleet_package_summary.csv`

## Options

```bash
bash scripts/run-vagrant-fleet-suite.sh --skip-up    # VMs already running
bash scripts/run-vagrant-fleet-suite.sh --destroy  # tear down after report
```

## Troubleshooting

- **Synced folder stale:** `vagrant rsync` before re-collecting.
- **libvirt instead of VirtualBox:** install `vagrant-libvirt`, then `vagrant up --provider=libvirt`.
- **Provision failed:** `vagrant provision container-web`
