"""Terraform layout tests for UnusedOS on Kicksecure GCP image."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TF_ROOT = REPO_ROOT / "terraform-test-kicksecure"
KICKSECURE_SCRIPTS = REPO_ROOT / "scripts" / "kicksecure"


def test_kicksecure_terraform_files_exist() -> None:
    for name in (
        "main.tf",
        "variables.tf",
        "startup-unusedos.sh.tpl",
        "verify.sh",
        "terraform.tfvars.example",
    ):
        assert (TF_ROOT / name).is_file(), f"missing {name}"


def test_main_tf_uses_custom_kicksecure_image() -> None:
    text = (TF_ROOT / "main.tf").read_text()
    assert "data.google_compute_image.kicksecure" in text
    assert "boot_disk_image       = data.google_compute_image.kicksecure.self_link" in text


def test_import_scripts_exist() -> None:
    for name in (
        "config.env.example",
        "download-kvm-image.sh",
        "prepare-disk-for-gcp.sh",
        "import-to-gcp.sh",
        "build-and-import.sh",
    ):
        assert (KICKSECURE_SCRIPTS / name).is_file(), f"missing {name}"


def test_verify_sets_ssh_user() -> None:
    text = (TF_ROOT / "verify.sh").read_text()
    assert 'SSH_USER="${SSH_USER:-user}"' in text


def test_packer_cloud_pipeline_exists() -> None:
    packer_root = REPO_ROOT / "packer" / "kicksecure-gcp"
    for name in (
        "versions.pkr.hcl",
        "variables.pkr.hcl",
        "kicksecure-gcp.pkr.hcl",
        "scripts/cloud-convert-import.sh",
    ):
        assert (packer_root / name).is_file(), f"missing {name}"
    assert (KICKSECURE_SCRIPTS / "run-packer-on-gce.sh").is_file()
