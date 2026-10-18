"""Terraform layout tests for remote Packer runner on GCP."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TF_ROOT = REPO_ROOT / "terraform-packer-runner"
PACKER_ROOT = REPO_ROOT / "packer" / "kicksecure-gcp"
SCRIPTS = REPO_ROOT / "scripts" / "kicksecure"


def test_packer_runner_terraform_files_exist() -> None:
    for name in (
        "main.tf",
        "variables.tf",
        "startup-packer-runner.sh.tpl",
        "verify.sh",
        "terraform.tfvars.example",
    ):
        assert (TF_ROOT / name).is_file(), f"missing {name}"


def test_startup_runs_packer_on_vm() -> None:
    text = (TF_ROOT / "startup-packer-runner.sh.tpl").read_text()
    assert "apt-get install" in text and "packer" in text
    assert "packer init" in text
    assert "packer build" in text
    assert "packer-kicksecure-complete" in text


def test_remote_orchestrator_scripts_exist() -> None:
    for name in ("run-packer-on-gce.sh", "upload-packer-bundle.sh", "build-and-import.sh"):
        assert (SCRIPTS / name).is_file(), f"missing {name}"


def test_packer_template_uses_gce_credentials() -> None:
    text = (PACKER_ROOT / "kicksecure-gcp.pkr.hcl").read_text()
    assert "use_google_compute_credentials = true" in text
    assert "skip_create_image = true" in text
