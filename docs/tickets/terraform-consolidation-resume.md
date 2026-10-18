# Ticket: Terraform consolidation — resume status

**Status:** In progress (UnusedOS committed; dev-terraform missing; downstream migrations pending)  
**Created:** 2026-05-22  
**Owner:** Kevin  
**Related:** `~/projects/dev-terraform/`, `UnusedOS/terraform-test/`

## Goal

Multiple Terraform copies on the dev machine (`scraper-intl`, `Security`, worktrees, `scaper-prod`) duplicate the same GCP test-VM pattern. Consolidate shared VM/verify/bootstrap code into one library so each environment only defines app-specific startup and checks.

## Completed

### Shared library (`~/projects/dev-terraform/`)

| Path | Purpose |
|------|---------|
| `modules/gcp_test_vm/` | Ubuntu GCP VM + startup-script metadata |
| `modules/gcp_test_outputs/` | SSH/verify outputs + optional `verify_all.sh` |
| `scripts/verify-lib.sh` | Shared `gcp_check()` for verify scripts |
| `scripts/install-gcloud-cli.sh` | Shared gcloud/gsutil install (injected via Terraform `file()`) |
| `README.md`, `MIGRATION.md` | Usage and per-environment migration steps |

### First consumer: `Security/UnusedOS/terraform-test/`

- Migrated to shared `gcp_test_vm` + `gcp_test_outputs` modules
- Startup injects `install-gcloud-cli.sh` before app template (avoids GCS bootstrap chicken-and-egg)
- `verify.sh` sources shared `verify-lib.sh`
- Layout tests: `UnusedOS/tests/test_terraform_vm.py` (7 passing)
- Scripts: `UnusedOS/scripts/upload-to-gcs.sh`, `run_vm_build_deploy_test.sh`

### VM build/deploy test (2026-05-22)

Full end-to-end run **passed**:

- GCS upload → `terraform apply` → startup (~8 min) → 5/5 SSH verify checks → `terraform destroy`
- Zone: `us-central1-a`, machine: `e2-small`, bucket prefix: `deployments/unusedos-test/latest`

### Bugs fixed during retry

1. **`install-gcloud-cli.sh` early `exit 0`** — When `gsutil` was already on the GCP Ubuntu image, the concatenated startup script exited before UnusedOS ran. Fixed: skip install with `:` instead of `exit 0`.
2. **`run_vm_build_deploy_test.sh` project parsing** — Broken regex left `project_id` empty; SSH polling failed silently and looked like a timeout/network issue. Fixed: read `project_id` from `terraform.tfvars` via `grep`/`sed`.

## Committed (Security repo)

All UnusedOS terraform work was committed in `fe9cf8f` and `d42e2dd`:

- `UnusedOS/.gitignore` — excludes `terraform.tfvars`, `*.tfstate*`, `.terraform/`
- `UnusedOS/scripts/run_vm_build_deploy_test.sh`
- `UnusedOS/scripts/upload-to-gcs.sh`
- `UnusedOS/terraform-test/` (main.tf, variables.tf, verify.sh, startup-unusedos.sh.tpl, terraform.tfvars.example)
- `UnusedOS/tests/test_terraform_vm.py`
- `UnusedOS/docs/tickets/terraform-consolidation-resume.md` (this file)

Verified: `terraform.tfvars`, `*.tfstate*`, `.terraform/` are gitignored and not tracked.

### `dev-terraform` repo hygiene

- Lives outside Security at `~/projects/dev-terraform/`
- **Not present on this machine** as of 2026-08-22 — the directory does not exist
- `terraform-test/main.tf` references it via `pathexpand("~/projects/dev-terraform")`
- Needs to be re-created or restored before downstream migrations can proceed
- Decide: standalone repo vs symlink vs submodule

### Downstream migrations (see `MIGRATION.md`)

| Project | Environment | Status |
|---------|-------------|--------|
| Security/UnusedOS | `terraform-test/` | **Done** (committed) |
| WorldStudioFinder | `terraform-test/environments/test-refactor/` | Candidate — has duplicate `google_compute_instance` + `verify_all` pattern |
| WorldStudioFinder | `terraform-test/environments/*` (8 other envs) | Not started |
| WorldStudioFinder | `terraform/`, `terraform-repair/`, `terraform-validate/` | Not started |
| scraper-intl | `terraform-test/`, `terraform/` | Not started (repo not on this machine) |
| scaper-prod | `terraform-test/`, `terraform-hobby/` | Not started |

Scraper environments retain env-specific resources (Secrets Manager, etc.) — only VM/verify boilerplate moves to shared modules.

## Startup script injection — prefer Terraform `file()` over GCS bootstrap

The UnusedOS `terraform-test/main.tf` already implements the preferred pattern:

```hcl
startup_script = join("\n\n", [
  file("${local.dev_terraform}/scripts/install-gcloud-cli.sh"),
  templatefile("${path.module}/startup-unusedos.sh.tpl", { ... }),
])
```

This injects the shared gcloud-install script directly into the VM metadata at
`terraform apply` time, avoiding the GCS bootstrap chicken-and-egg problem
(the VM needs gcloud/gsutil to download from GCS, but gcloud isn't installed yet).

**Convention for all migrated environments:** use `file()` injection for shared
scripts. Do not copy install scripts to GCS and fetch them at boot — that
creates a circular dependency when the VM doesn't yet have `gsutil`.

The original `MIGRATION.md` lived in `~/projects/dev-terraform/` which is not
present on this machine. The guidance above supersedes the GCS bootstrap
approach documented there.

## Next steps

1. [x] Commit Security UnusedOS terraform + scripts + tests + this ticket
2. [ ] Restore or re-create `~/projects/dev-terraform/` shared library (modules, scripts, docs)
3. [ ] Initialize `dev-terraform` as git repo (or document install path convention)
4. [ ] Migrate `WorldStudioFinder/terraform-test/environments/test-refactor/` as second consumer
5. [x] Document `file()` startup injection preference (above)

## How to re-run the VM test

```bash
cd ~/projects/Security/UnusedOS
bash scripts/run_vm_build_deploy_test.sh
# Keep VM: bash scripts/run_vm_build_deploy_test.sh --keep
```

## Acceptance criteria (remaining)

- [ ] Shared library versioned and reachable from all dev stacks — **blocked**: `dev-terraform/` not present on machine
- [ ] At least two consumers migrated (UnusedOS + one scraper env) — UnusedOS done; WorldStudioFinder `test-refactor` identified as second consumer
- [ ] No duplicate `google_compute_instance` / verify boilerplate in migrated dirs
- [x] Documented convention in sub-project README (see `UnusedOS/README.md` shared library section)
