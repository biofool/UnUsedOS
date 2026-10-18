from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def host_fixture(tmp_path: Path) -> Path:
    host_dir = tmp_path / "test-host"
    host_dir.mkdir()
    (host_dir / "test-host-all_package_files.log").write_text(
        "/usr/bin/app|alpha\n/var/lib/data|beta\n",
        encoding="utf-8",
    )
    (host_dir / "test-host-usage.log").write_text(
        "/usr/bin/app|1000.0|2000.0\n/var/lib/data|1000.0|1500.0\n/opt/local/bin|1000.0|1800.0\n",
        encoding="utf-8",
    )
    return host_dir


@pytest.fixture
def fleet_fixture(tmp_path: Path, host_fixture: Path) -> Path:
    fleet_root = tmp_path / "fleet"
    fleet_root.mkdir()
    host_b = fleet_root / "host-b"
    host_b.mkdir()
    (host_b / "host-b-all_package_files.log").write_text("/bin/tool|gamma\n", encoding="utf-8")
    (host_b / "host-b-usage.log").write_text("/bin/tool|1000.0|3000.0\n", encoding="utf-8")

    import shutil

    shutil.copytree(host_fixture, fleet_root / "test-host")
    return fleet_root


@pytest.fixture
def legacy_csv_fixture(tmp_path: Path) -> Path:
    source = tmp_path / "legacy"
    source.mkdir()
    (source / "files_info.csv").write_text(
        "path,creation_time,access_time\n/customer/vigilent/secret,1000,2000\n",
        encoding="utf-8",
    )
    (source / "files_packages.csv").write_text(
        "path,package\n/customer/vigilent/secret,alpha\n",
        encoding="utf-8",
    )
    return source


@pytest.fixture
def mounts_fixture(tmp_path: Path) -> Path:
    mounts = tmp_path / "mounts"
    mounts.write_text(
        "/dev/sda1 / ext4 rw,relatime 0 0\n/dev/sdb1 /data ext4 rw,noatime 0 0\n",
        encoding="utf-8",
    )
    return mounts
