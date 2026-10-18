from pathlib import Path

from unusedos.analyze import analyze_directory, analyze_fleet, check_atime_reliability
from unusedos.config import Settings


def test_analyze_directory_ranks_packages(host_fixture: Path):
    settings = Settings(anonymize=False, protected_packages=["coreutils"])
    result = analyze_directory(host_fixture, settings=settings, host_id="test-host")
    packages = list(result.package_rankings["package"])
    assert packages == ["beta", "alpha"]
    assert all(result.package_rankings["review_only"])


def test_analyze_directory_excludes_protected_packages(host_fixture: Path):
    settings = Settings(anonymize=False, protected_packages=["alpha"])
    result = analyze_directory(host_fixture, settings=settings, host_id="test-host")
    assert "alpha" not in set(result.package_rankings["package"])


def test_analyze_fleet(host_fixture: Path, fleet_fixture: Path):
    settings = Settings(anonymize=False, protected_packages=[])
    fleet = analyze_fleet(fleet_fixture, settings=settings)
    assert set(fleet["host"]) == {"test-host", "host-b"}


def test_check_atime_reliability(mounts_fixture: Path):
    warnings = check_atime_reliability(mounts_fixture)
    assert any("noatime" in warning for warning in warnings)
    assert any("relatime" in warning for warning in warnings)
