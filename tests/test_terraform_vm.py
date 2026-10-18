"""Terraform VM build/deploy layout tests for UnusedOS."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TF_ROOT = REPO_ROOT / "terraform-test"


def test_terraform_core_files_exist() -> None:
    for name in (
        "main.tf",
        "variables.tf",
        "startup-unusedos.sh.tpl",
        "verify.sh",
        "terraform.tfvars.example",
    ):
        assert (TF_ROOT / name).is_file(), f"missing {name}"


def test_main_tf_uses_shared_dev_terraform_module() -> None:
    text = (TF_ROOT / "main.tf").read_text()
    assert "local.dev_terraform" in text
    assert "/modules/gcp_test_vm" in text
    assert "/modules/gcp_test_outputs" in text
    assert "google_compute_instance" not in text


def test_startup_runs_tests_harness_collect_and_analyze() -> None:
    text = (TF_ROOT / "startup-unusedos.sh.tpl").read_text()
    assert "requirements-dev.txt" in text
    assert "python -m pytest" in text
    assert "python -m unusedos.harness" in text
    assert "packages_exploder.sh" in text
    assert "python -m unusedos analyze" in text
    assert "unusedos-test-complete" in text


def test_main_tf_injects_shared_gcloud_install() -> None:
    text = (TF_ROOT / "main.tf").read_text()
    assert 'file("${local.dev_terraform}/scripts/install-gcloud-cli.sh")' in text


def test_verify_script_uses_shared_lib() -> None:
    text = (TF_ROOT / "verify.sh").read_text()
    assert "verify-lib.sh" in text
    assert "DEV_TERRAFORM" in text


def test_variables_default_gcs_prefix() -> None:
    text = (TF_ROOT / "variables.tf").read_text()
    assert "deployments/unusedos-test/latest" in text


def test_upload_script_exists() -> None:
    assert (REPO_ROOT / "scripts" / "upload-to-gcs.sh").is_file()
    assert (REPO_ROOT / "scripts" / "run_vm_build_deploy_test.sh").is_file()
