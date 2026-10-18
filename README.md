# UnusedOS

## Executive summary

<!-- exec-summary: begin -->
Finds files and software packages that are rarely used on Linux servers. Helps security teams shrink attack surface by prioritizing updates, patches, or removal of neglected components. The project now ships as a Python package for single-server and fleet-wide review, with runbooks, anonymization options, and automated GCP deploy testing.
<!-- exec-summary: end -->

## Overview

UnusedOS merges file access data with package inventories to rank packages by how long their files have gone untouched. Output is **review-only** — it recommends candidates for patch or removal; it does not uninstall packages.

| Layer | Location |
|-------|----------|
| Python package | `unusedos/` — `analyze`, `analyze-fleet`, `import`, `check-atime` |
| Host collection | `scripts/collect-on-host.sh`, `packages_exploder.sh`, container fleet suite |
| Fleet reporting | `python -m unusedos summarize --archive-root <logs>` |
| Runbooks | `docs/runbooks/` |
| Architecture notes | `docs/ATIME-RELIABILITY.md`, `docs/VEMSStatsCollector-INTEGRATION.md` |
| Terraform VM test | `terraform-test/` (shared modules in `~/projects/dev-terraform`) |

Copy `.env.example` to `.env` to configure anonymization and paths. See `docs/runbooks/single-server-analysis.md` for the end-to-end workflow.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Validate ext4 atime settings on this host
.venv/bin/python -m unusedos check-atime

# Analyze collected logs under /var/log/unusedos-export/<host>/
.venv/bin/python -m unusedos analyze \
  --input-dir /path/to/export \
  --host myhost \
  --output-dir ./reports
```

Packages unused for a year that can be removed together without also removing a package that has been used:

```bash
.venv/bin/python -m unusedos safe-remove --input-dir ./exports/myhost --unused-before 2025-10-02
```

That writes an editable `safe-remove.txt` (one package per line) and `safe-remove-details.tsv` (other unused packages apt would remove with each name). It checks the list with `apt-get -s remove` and does not uninstall anything.

Fleet-wide ranking after importing per-host exports:

```bash
.venv/bin/python -m unusedos analyze-fleet --root-dir ./fleet-data --output-dir ./reports
```

## Tests

```bash
pip install -r requirements-dev.txt
./run_tests.sh
```

Unit tests cover config, analysis, anonymization, CLI behavior, and the usage-detection harness. Layout tests in `tests/test_terraform_vm.py` assert the GCP test stack uses shared `dev-terraform` modules.

### Usage-detection harness

Synthetic end-to-end test: backdate files in a sandbox tree, run one package, collect usage, and verify rankings.

```bash
./scripts/run_usage_harness.sh
# custom workdir: ./scripts/run_usage_harness.sh --root reports/my-harness --used-package alpha-cli
```

Programmatic API: `unusedos.harness.UsageDetectionHarness` (see `tests/test_harness.py`).

### Container fleet suite and archive reporting

Simulates multiple containers, writes per-host log archives and reports, then summarizes unused packages fleet-wide:

```bash
./scripts/run_container_fleet_suite.sh
# or summarize an existing log archive folder:
.venv/bin/python -m unusedos summarize --archive-root /path/to/log-archives --output-dir reports/fleet-summary
```

The summarizer recursively searches for `*-usage.log` / `*-all_package_files.log` pairs and nested `package_rankings.csv` files, then writes `fleet_summary.md`, `fleet_package_summary.csv`, and `fleet_host_summary.csv`.

### Debian VMs (Vagrant)

Run the fleet suite on three Debian Bookworm VMs:

```bash
bash vagrant/scripts/run-vagrant-fleet-suite.sh
```

See `vagrant/README.md` for provider setup and VM roles.

## GCP VM build and deploy test

Provisions a throwaway Ubuntu VM, syncs the UnusedOS bundle from GCS, installs dev dependencies, runs the full pytest suite and usage-detection harness, then collects real package/usage data, runs analysis, verifies over SSH, and destroys the VM.

```bash
cp terraform-test/terraform.tfvars.example terraform-test/terraform.tfvars
# edit terraform.tfvars if needed

bash scripts/run_vm_build_deploy_test.sh
# keep VM for debugging: bash scripts/run_vm_build_deploy_test.sh --keep
```

Shared VM, verify, and gcloud-install code lives in `~/projects/dev-terraform/`. Resume status and migration plan: `docs/tickets/terraform-consolidation-resume.md` ([GitHub #67](https://github.com/vigilent/Security/issues/67)).

### Shared Terraform library convention

The `terraform-test/` stack consumes shared modules from `~/projects/dev-terraform/`:

| Module | Purpose |
|--------|---------|
| `modules/gcp_test_vm/` | Ubuntu GCP VM + startup-script metadata |
| `modules/gcp_test_outputs/` | SSH/verify outputs + optional `verify_all.sh` |
| `scripts/verify-lib.sh` | Shared `gcp_check()` for verify scripts |
| `scripts/install-gcloud-cli.sh` | Shared gcloud/gsutil install (injected via Terraform `file()`) |

Each environment defines only app-specific startup templates and verify checks. Shared boilerplate (`google_compute_instance`, SSH output formatting, `verify_all.sh` generation) lives in the library modules.

**Startup injection:** prefer `file("${local.dev_terraform}/scripts/install-gcloud-cli.sh")` over GCS bootstrap copy. This avoids the chicken-and-egg problem where a VM needs `gsutil` to download from GCS but doesn't have it installed yet.

**Note:** `~/projects/dev-terraform/` is not present on this machine as of 2026-08-22. The `terraform-test/main.tf` references it via `pathexpand("~/projects/dev-terraform")`. The shared library needs to be restored or re-created before `terraform init` will succeed and before downstream migrations can proceed.

### Kicksecure GCP image (optional)

To test on [Kicksecure](https://www.kicksecure.com/) instead of Ubuntu:

```bash
cp packer/kicksecure-gcp/variables.auto.pkrvars.hcl.example packer/kicksecure-gcp/variables.auto.pkrvars.hcl
bash scripts/kicksecure/run-packer-on-gce.sh          # Packer runs on a GCP runner VM (no local Packer)
bash scripts/run_kicksecure_vm_build_deploy_test.sh
```

See `docs/KICKSECURE-GCP-IMAGE.md` for the full import workflow and Terraform variables (`boot_disk_image_name`, `ssh_user=user`).

## Legacy scripts

Older shell and Python entry points (`WhatsUnusedSurvey.py`, `UnusedPackageReport.py`, `collector2.sh`, etc.) remain for reference. Prefer `python -m unusedos` for new work.

---

# File Access and Modification Analysis (legacy)

## Overview

This program uses `find` to examine a directory tree or filesystem for the last time a file was accessed or changed. It also determines whether either of these events has happened since the file was created. This analysis is designed for Ubuntu versions 20 and later. It stores the last modification time and whether the file was accessed more than a threshold number of seconds after it was modified.

This application (`WhatsUnused.sh`) is in alpha; the installer is still in alpha test.

## Usage

To use this program, provide a path to the directory or filesystem you want to analyze.

```
Usage: $0 [OPTIONS]
  OPTIONS:
    -t, --threshold SECONDS
                     Set the time threshold in SECONDS (default: 600).
    -d, --directories DIRS
                     Specify a colon-separated list of directories to search.
                     (default: all mounted ext4 file systems).
    -u, --unused_window SECONDS
                     Set the time window in days during which a file must not
                     have been modified or read to be considered unused (default: 30).
    -m, --monitor
                     Run in monitor loops with sort -u & sleep minutes between loops.
                     no -m run once
                     -m=n>0 (monitor for N+1 iteration)
                     -m=0 infinite loop
    -s, --sleep
                     In monitor mode sleep N minutes between find runs.
    -D, --debug
                     Enable debug mode to output additional information.
                     Debug also shortens the sleep time to 6 seconds
    -h       Show this help message and exit.
```

## Find command output

The collector uses `find` to locate files that have not been accessed or modified within a time frame. Example line:

```
./collector2.sh,0,0,v1, ../.. /tmp,-xdev -type f ( -mtime +30 -o -atime +30 ) -printf
%p,%T@,%A@\n../../aws_security_incident_response.docx,1677433493.066,1677433519.457,ish+-:26.392
```

Outputs:

- `Unused.csv` — files neither modified nor accessed in the window
- `Unused.err` — errors from `find` (should be 0 for a privileged user)

## Timestamp management in ext4

See `docs/ATIME-RELIABILITY.md` for operational guidance. Kernel mount options that affect atime behavior include `relatime`, `norelatime`, `strictatime`, `nostrictatime`, `lazytime`, and `nolazytime`.

## Core objective (original project notes)

The primary goal was to identify which files and packages had files that are not needed most of the time.

**Data collection:** (1) a comprehensive list of files with paths, creation, and access times; (2) a mapping of files to packages.

**Processing:** merge on file paths with pandas, group by package, and take the oldest access time per package.

**Reporting:** packages sorted by oldest file access time to guide security review.

**Why it matters:** reduces attack surface and supports proactive maintenance. Alternatives considered (SELinux, auditd, eBPF, AppArmor) were rejected due to performance and engineering cost for full utilization coverage.

![image](https://github.com/vigilent/Security/assets/1031599/06ece6b1-f041-4dbc-92ef-8f9da6833e15)
