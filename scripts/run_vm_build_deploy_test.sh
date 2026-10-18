#!/bin/bash
# Full UnusedOS VM build and deploy test (GCP Terraform template from scraper-intl).
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
TF_DIR="$UNUSEDOS_ROOT/terraform-test"
KEEP_VM=false

while [ $# -gt 0 ]; do
  case "$1" in
    --keep) KEEP_VM=true; shift ;;
    -h|--help)
      echo "Usage: $0 [--keep]"
      echo "  Upload bundle, terraform apply, verify SSH checks, destroy VM (unless --keep)"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "==> Local terraform layout tests"
cd "$UNUSEDOS_ROOT"
if [ -d .venv ]; then
  .venv/bin/python -m pytest tests/test_terraform_vm.py -q
else
  python3 -m pytest tests/test_terraform_vm.py -q
fi

echo "==> Upload deployment bundle to GCS"
bash "$SCRIPT_DIR/upload-to-gcs.sh"

# Declare intent with CloudManagement (best-effort, issue #73).
# Returns an intent_id (or "none" if not configured) for reporting actuals later.
CM_INTENT_ID="$(cd "$UNUSEDOS_ROOT" && python3 -m unusedos.cloudmgmt_report declare --expected-hours 1 --expected-cost-usd 0.05 2>/dev/null || echo none)"
echo "CloudManagement intent: $CM_INTENT_ID"

echo "==> Terraform init/apply"
cd "$TF_DIR"
if [ ! -f terraform.tfvars ]; then
  cp terraform.tfvars.example terraform.tfvars
fi
terraform init -input=false
terraform apply -auto-approve -input=false

VM_NAME="$(terraform output -json instance_names | python3 -c 'import json,sys; print(json.load(sys.stdin)[0])')"
ZONE="$(terraform output -json instance_zones | python3 -c 'import json,sys; print(json.load(sys.stdin)[0])')"
PROJECT="$(grep -E '^project_id' terraform.tfvars | sed -E 's/.*"([^"]+)".*/\1/')"
if [ -z "$PROJECT" ]; then
  echo "Could not read project_id from terraform.tfvars"
  exit 1
fi

echo "==> Waiting for startup (up to 15 minutes)"
for i in $(seq 1 90); do
  if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --project="$PROJECT" \
    --tunnel-through-iap --command "test -f /var/log/unusedos-test-complete" 2>/dev/null; then
    echo "Startup complete after $((i * 10))s"
    break
  fi
  sleep 10
  if [ "$i" -eq 90 ]; then
    echo "Timed out waiting for startup marker"
    gcloud compute ssh "$VM_NAME" --zone="$ZONE" --project="$PROJECT" \
      --tunnel-through-iap --command "tail -50 /var/log/unusedos-startup.log" || true
    exit 1
  fi
done

echo "==> Verify deploy on VM"
bash "$TF_DIR/verify.sh" "$VM_NAME" "$ZONE" "$PROJECT"

if [ "$KEEP_VM" = false ]; then
  echo "==> Terraform destroy"
  terraform destroy -auto-approve -input=false
else
  echo "VM kept (--keep). SSH:"
  terraform output ssh_commands
fi

# Report actuals to CloudManagement (best-effort, issue #73).
cd "$UNUSEDOS_ROOT"
python3 -m unusedos.cloudmgmt_report actual --intent-id "$CM_INTENT_ID" --actual-hours 0.5 --actual-cost-usd 0.03 --status completed 2>/dev/null || true

echo "UnusedOS VM build and deploy test succeeded"
