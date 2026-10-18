#!/usr/bin/env bash
# Run Kicksecure Packer import entirely in GCP (no local Packer).
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

UNUSEDOS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TF_DIR="$UNUSEDOS_ROOT/terraform-packer-runner"
KEEP_VM=false

while [ $# -gt 0 ]; do
  case "$1" in
    --keep) KEEP_VM=true; shift ;;
    -h|--help)
      echo "Usage: $0 [--keep]"
      echo "  Upload packer bundle, create packer-runner VM on GCP, wait for Kicksecure image import"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "==> Upload packer bundle to GCS"
bash "$SCRIPT_DIR/upload-packer-bundle.sh"

echo "==> Terraform init/apply (packer-runner VM)"
cd "$TF_DIR"
if [ ! -f terraform.tfvars ]; then
  cp terraform.tfvars.example terraform.tfvars
fi
terraform init -input=false
terraform apply -auto-approve -input=false

VM_NAME="$(terraform output -json instance_names | python3 -c 'import json,sys; print(json.load(sys.stdin)[0])')"
ZONE="$(terraform output -json instance_zones | python3 -c 'import json,sys; print(json.load(sys.stdin)[0])')"
PROJECT="$(grep -E '^project_id' terraform.tfvars | sed -E 's/.*"([^"]+)".*/\1/')"
IMAGE_NAME="$(grep -E '^kicksecure_image_name' terraform.tfvars | sed -E 's/.*"([^"]+)".*/\1/')"
SSH_USER="$(grep -E '^ssh_user' terraform.tfvars | sed -E 's/.*"([^"]+)".*/\1/' || echo admin)"
export SSH_USER

if gcloud compute images describe "$IMAGE_NAME" --project="$PROJECT" >/dev/null 2>&1; then
  echo "Kicksecure image $IMAGE_NAME already exists; skipping wait"
else
  echo "==> Waiting for packer-runner (up to 45 minutes)"
  for i in $(seq 1 270); do
    if gcloud compute ssh "$VM_NAME" --zone="$ZONE" --project="$PROJECT" --user="$SSH_USER" \
      --tunnel-through-iap --command "test -f /var/log/packer-kicksecure-complete" 2>/dev/null; then
      echo "Packer complete after $((i * 10))s"
      break
    fi
    if gcloud compute images describe "$IMAGE_NAME" --project="$PROJECT" >/dev/null 2>&1; then
      echo "Image $IMAGE_NAME appeared after $((i * 10))s"
      break
    fi
    sleep 10
    if [ "$i" -eq 270 ]; then
      echo "Timed out waiting for packer-runner"
      gcloud compute ssh "$VM_NAME" --zone="$ZONE" --project="$PROJECT" --user="$SSH_USER" \
        --tunnel-through-iap --command "tail -60 /var/log/packer-runner.log" || true
      exit 1
    fi
  done
fi

echo "==> Verify packer-runner"
bash "$TF_DIR/verify.sh" "$VM_NAME" "$ZONE" "$PROJECT" "$IMAGE_NAME"

if [ "$KEEP_VM" = false ]; then
  echo "==> Terraform destroy (packer-runner VM only)"
  terraform destroy -auto-approve -input=false
else
  echo "Runner VM kept (--keep)"
fi

echo ""
echo "Kicksecure image ready: projects/${PROJECT}/global/images/${IMAGE_NAME}"
