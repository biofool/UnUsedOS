# Component — Security Patch Pipeline

> **Evidence:** DECLARED in `README.md`; INFERRED from `origin/Public` (read-only).
> Not OBSERVED on `main`. **Highest-risk component.**

## Responsibility
Build an installable security patch bundle from `unattended-upgrades` `.deb`
files and install it on a remote host via SSH + `dpkg`.

## Primary files (INFERRED from origin/Public)
- `CreateSecurityPatch/CreateSecurityPatchBundle.sh` — on a patch-generator host: ensure `unattended-upgrades`, copy `upgrade.conf` to `/etc/apt/apt.conf.d/50unattended-upgrades`, `apt clean`, `unattended-upgrade --download-only`, copy `.deb`s to `/var/log/vems/patch_dir_<date>/`, `rsync` to a destination host, `ssh ... sudo dpkg -i`.
- `CreateSecurityPatch/SecurityPatchInstaller.sh` — similar flow but installs locally via `sudo dpkg -i /var/tmp/$$.patchlist`.
- `CreateSecurityPatch/upgrade.conf` — unattended-upgrades config.
- `CreateSecurityPatch/README.md` — "Version 0.5 Alpha", dev-environment only.

## Public interfaces
None. Scripts are run manually as root.

## Dependencies
- **runtime:** `unattended-upgrades`, `apt-get`, `dpkg`, `rsync`, `ssh`, `sudo`.
- **data:** `/var/cache/apt/archives/*.deb`, `/var/log/vems/`.
- **config:** `upgrade.conf` → `/etc/apt/apt.conf.d/50unattended-upgrades`.

## Consumers
Target SCS appliance hosts (receive & install the patch).

## Security-sensitive behavior (HIGH)
- Runs `sudo apt-get install`, `sudo dpkg-reconfigure`, `sudo dpkg -i`.
- `ssh "${destination_host}" 'sudo -S dpkg -i ...'` — remote root command execution.
- Contains a **commented-out** block creating a user `fc` with password
  `fcllc00` and `NOPASSWD` sudo (`sed -i 's/^%sudo.*/%sudo ALL=(ALL:ALL) NOPASSWD:ALL/' /etc/sudoers`). Though commented out, this is a credential/privilege-escalation pattern that must never be uncommented.
- Uses `/var/tmp/$$.patchlist` (predictable temp path; potential symlink race).
- Marked "Version 0.5 Alpha" and "does not need to get deployed to production".

## Operationally-sensitive behavior
- Modifies system apt config (`/etc/apt/apt.conf.d/`).
- Installs packages on remote hosts — no rollback path evidenced.
- No idempotency guarantees; no verification of installed package integrity beyond dpkg.

## Change-impact
See [../change-impact/relationships.yaml](../change-impact/relationships.yaml)
entry `security-patch-pipeline`. Before modifying: review both bundle and
installer scripts together; confirm `upgrade.conf` matches the apt config
schema for the target Ubuntu release; never enable the commented credential block.
