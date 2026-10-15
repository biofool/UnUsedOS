# Workflow — Security Patch Creation & Installation

> **Evidence:** DECLARED in `README.md`; INFERRED from `origin/Public` (read-only).
> Not OBSERVED on `main`. **High-risk workflow.**

## Entry Point
Manual, on a patch-generator host:
`bash CreateSecurityPatch/CreateSecurityPatchBundle.sh`

## Execution Path
```
CreateSecurityPatchBundle.sh  (patch generator host, root)
    ↓  ensure unattended-upgrades installed + dpkg-reconfigure
    ↓  cp upgrade.conf → /etc/apt/apt.conf.d/50unattended-upgrades
    ↓  apt clean; verify no .deb in /var/cache/apt/archives
    ↓  apt-get -s --download-only upgrade  (count available upgrades)
    ↓  unattended-upgrade --download-only  (download .deb files)
    ↓  find /var/cache/apt/archives -name '*.deb'  →  /var/tmp/$$.patchlist
    ↓  mkdir /var/log/vems/patch_dir_<date>; cp .deb files there
    ↓  read destination_host from stdin
    ↓  rsync -av patch_dir  destination_host:patch_dir
    ↓  ssh destination_host 'sudo -S dpkg -i /var/log/vems/output_dir/*'
installed on remote host
```
`SecurityPatchInstaller.sh` is a local-install variant (`sudo dpkg -i /var/tmp/$$.patchlist`).

## Evidence
- `CreateSecurityPatchBundle.sh` and `SecurityPatchInstaller.sh` near-identical; both "V 0.5 Alpha" (INFERRED, origin/Public).
- `upgrade.conf` copied to apt config dir (INFERRED).
- `CreateSecurityPatch/README.md`: "does not need to get deployed to production ... lives solely on the patch generator" (DECLARED on origin/Public).

## Failure Paths
- **No upgrades available:** `exit 1` (script aborts).
- **.deb already in cache:** `exit 1` (refuses to proceed).
- **SSH failure:** `|| { echo 'SSH command failed' >&2; exit 1; }` (bundle script only).
- **No rollback:** once `dpkg -i` runs, no automated revert. UNKNOWN recovery.
- **No integrity check:** `.deb` files not verified (e.g. no `dpkg --verify` / checksum) beyond apt's own.
- **Temp file race:** `/var/tmp/$$.patchlist` is predictable; symlink-risk if hostile local users present.

## Change Guidance
Review `CreateSecurityPatchBundle.sh`, `SecurityPatchInstaller.sh`, and
`upgrade.conf` together (they share logic). Never uncomment the embedded
credential-creation block. Confirm the apt config schema for the target Ubuntu
release. This workflow is operationally destructive — test on a disposable VM.
