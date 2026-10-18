"""Layout tests for Vagrant Debian fleet suite."""

from __future__ import annotations

from pathlib import Path

VAGRANT_ROOT = Path(__file__).resolve().parent.parent / "vagrant"


def test_vagrant_files_exist() -> None:
    for name in ("Vagrantfile", "README.md", "scripts/provision-debian.sh", "scripts/collect-on-vm.sh", "scripts/run-vagrant-fleet-suite.sh"):
        assert (VAGRANT_ROOT / name).is_file(), f"missing {name}"


def test_vagrantfile_defines_three_debian_hosts() -> None:
    text = (VAGRANT_ROOT / "Vagrantfile").read_text()
    assert "debian/bookworm64" in text
    for host in ("container-web", "container-api", "container-worker"):
        assert host in text


def test_collect_script_writes_to_archives() -> None:
    text = (VAGRANT_ROOT / "scripts/collect-on-vm.sh").read_text()
    assert "/vagrant/archives" in text
    assert "unusedos analyze" in text
