#!/bin/bash
# Full UnusedOS VM test on imported Kicksecure GCP image.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Debug/Verbose flags ---
DEBUG=false
VERBOSE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--debug) DEBUG=true; shift ;;
        -v|--verbose) VERBOSE=true; shift ;;
        *) break ;;
    esac
done

if $DEBUG; then
    set -x
    PS4='+ ${BASH_SOURCE}:${LINENO}: '
fi

log_verbose() { $VERBOSE && echo "[VERBOSE] $*" >&2 || true; }
log_debug() { $DEBUG && echo "[DEBUG] $*" >&2 || true; }

UNUSEDOS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TF_DIR="$UNUSEDOS_ROOT/terraform-test-kicksecure"
KEEP_VM=false
SSH_USER="${SSH_USER:-user}"

while [ $# -gt 0 ]; do
  case "$1" in
    --keep) KEEP_VM=true; shift ;;
    -h|--help)
      echo "Usage: $0 [--keep]"
      echo "  Requires Kicksecure image imported (scripts/kicksecure/build-and-import.sh)"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "==> Local terraform layout tests"
cd "$UNUSEDOS_ROOT"
if [ -d .venv ]; then
  .venv/bin/python -m pytest tests/test_terraform_kicksecure.py -q
else
  python3 -m pytest tests/test_terraform_kicksecure.py -q
fi

echo "==> Confirm Kicksecure GCP image exists"
cd "$TF_DIR"
if [ ! -f terraform.tfvars ]; then
  cp terraform.tfvars.example terraform.tfvars
fi
PROJECT="$(grep -E '^project_id' terraform.tfvars | sed -E 's/.*"([^"]+)".*/\1/')"
IMAGE="$(grep -E '^boot_disk_image_name' terraform.tfvars | sed -E 's/.*"([^"]+)".*/\1/')"
if ! gcloud compute images describe "$IMAGE" --project="$PROJECT" >/dev/null 2>&1; then
  echo "ERROR: GCP image $IMAGE not found in $PROJECT"
  echo "Run: cp scripts/kicksecure/config.env.example scripts/kicksecure/config.env"
  echo "     bash scripts/kicksecure/build-and-import.sh"
  exit 1
fi

echo "==> Upload deployment bundle to GCS"
bash "$SCRIPT_DIR/upload-to-gcs.sh"

echo "==> Terraform init/apply"
terraform init -input=false
terraform apply -auto-approve -input=false

VM_NAME="$(terraform output -json instance_names | python3 -c 'import json,sys; print(json.load(sys.stdin)[0])')"
ZONE="$(terraform output -json instance_zones | python3 -c 'import json,sys; print(json.load(sys.stdin)[0])')"
SSH_USER="$(terraform output -raw ssh_user 2>/dev/null || echo user)"
export SSH_USER

echo "==> Waiting for startup (up to 20 minutes)"
for i in $(seq 1 120); do
  if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --project="$PROJECT" --user="$SSH_USER" \
    --tunnel-through-iap --command "test -f /var/log/unusedos-test-complete" 2>/dev/null; then
    echo "Startup complete after $((i * 10))s"
    break
  fi
  sleep 10
  if [ "$i" -eq 120 ]; then
    echo "Timed out waiting for startup marker"
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --project="$PROJECT" --user="$SSH_USER" \
      --tunnel-through-iap --command "tail -50 /var/log/unusedos-startup.log" || true
    exit 1
  fi
done

echo "==> Verify deploy on Kicksecure VM"
bash "$TF_DIR/verify.sh" "$VM_NAME" "$ZONE" "$PROJECT"

if [ "$KEEP_VM" = false ]; then
  echo "==> Terraform destroy"
  terraform destroy -auto-approve -input=false
else
  echo "VM kept (--keep). SSH as $SSH_USER:"
  terraform output ssh_commands
fi

echo "UnusedOS Kicksecure VM test succeeded"
