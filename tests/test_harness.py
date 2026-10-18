"""Tests for the synthetic usage-detection harness."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

from unusedos.config import Settings
from unusedos.harness import PackageSpec, UsageDetectionHarness, default_demo_packages


@pytest.fixture
def harness_root(tmp_path: Path) -> Path:
    return tmp_path / "harness"


def test_backdate_then_run_package_produces_expected_ranking(harness_root: Path) -> None:
    harness = UsageDetectionHarness(
        harness_root / "sandbox",
        host_id="test-host",
        export_dir=harness_root / "export",
    )
    stale = 1_000.0
    fresh = 9_000_000.0
    result = harness.run_scenario(
        default_demo_packages(),
        used_package="alpha-cli",
        stale_access_time=stale,
        fresh_access_time=fresh,
        settings=Settings(anonymize=False, protected_packages=[]),
        prefer_find=False,
    )

    rankings = result.analysis.package_rankings
    packages = list(rankings["package"])
    assert packages == ["beta-lib", "alpha-cli"]

    alpha_atime = float(rankings.loc[rankings["package"] == "alpha-cli", "access_time"].iloc[0])
    beta_atime = float(rankings.loc[rankings["package"] == "beta-lib", "access_time"].iloc[0])
    assert alpha_atime == fresh
    assert beta_atime == stale


def test_without_run_package_all_packages_stay_stale(harness_root: Path) -> None:
    harness = UsageDetectionHarness(
        harness_root / "sandbox",
        host_id="test-host",
        export_dir=harness_root / "export",
    )
    harness.install_packages(default_demo_packages())
    harness.backdate_all(access_time=500.0)
    harness.write_package_inventory()
    harness.collect_usage_log(prefer_find=False)

    result = harness.analyze(settings=Settings(anonymize=False, protected_packages=[]))
    access_times = set(result.package_rankings["access_time"].astype(float))
    assert access_times == {500.0}


def test_run_package_updates_only_target_files(harness_root: Path) -> None:
    packages = [
        PackageSpec(name="pkg-a", files={"bin/a": "a"}),
        PackageSpec(name="pkg-b", files={"bin/b": "b"}),
    ]
    harness = UsageDetectionHarness(
        harness_root / "sandbox",
        host_id="test-host",
        export_dir=harness_root / "export",
    )
    harness.install_packages(packages)
    harness.backdate_all(access_time=100.0)
    harness.run_package("pkg-a", access_time=777.0)

    for path in harness.files_for_package("pkg-a"):
        assert path.stat().st_atime == 777.0
    for path in harness.files_for_package("pkg-b"):
        assert path.stat().st_atime == 100.0


def test_executable_package_is_run(harness_root: Path) -> None:
    harness = UsageDetectionHarness(
        harness_root / "sandbox",
        host_id="test-host",
        export_dir=harness_root / "export",
    )
    packages = [
        PackageSpec(
            name="runner",
            files={
                "var/runner/input.txt": "hello harness",
                "usr/bin/runner": '#!/bin/sh\ncat "$(dirname "$0")/../../var/runner/input.txt"\n',
            },
            executable="usr/bin/runner",
        ),
    ]
    harness.install_packages(packages)
    runner = harness.files_for_package("runner")
    assert len(runner) == 2
    harness.backdate_all(access_time=50.0)
    harness.run_package("runner", access_time=time.time())

    for path in runner:
        assert path.stat().st_atime > 50.0


@pytest.mark.skipif(shutil.which("find") is None, reason="find not available")
def test_find_collection_matches_stat(harness_root: Path) -> None:
    harness = UsageDetectionHarness(
        harness_root / "sandbox",
        host_id="test-host",
        export_dir=harness_root / "export",
    )
    harness.install_packages(default_demo_packages())
    harness.backdate_all(access_time=1234.0)
    harness.run_package("alpha-cli", access_time=5678.0)

    stat_log = harness_root / "export-stat"
    find_log = harness_root / "export-find"
    harness.export_dir = stat_log
    harness.collect_usage_log(prefer_find=False)
    harness.export_dir = find_log
    harness.collect_usage_log(prefer_find=True)

    stat_rows = (stat_log / "test-host-usage.log").read_text(encoding="utf-8").strip().splitlines()
    find_rows = (find_log / "test-host-usage.log").read_text(encoding="utf-8").strip().splitlines()
    assert len(stat_rows) == len(find_rows)

    def by_path(rows: list[str]) -> dict[str, tuple[float, float]]:
        out: dict[str, tuple[float, float]] = {}
        for row in rows:
            path, mtime, atime = row.split("|")
            out[path] = (float(mtime), float(atime))
        return out

    stat_map = by_path(stat_rows)
    find_map = by_path(find_rows)
    assert set(stat_map) == set(find_map)
    for path in stat_map:
        assert stat_map[path][1] == pytest.approx(find_map[path][1], rel=0, abs=1.0)


def test_usage_log_format_is_analyzable(harness_root: Path) -> None:
    harness = UsageDetectionHarness(
        harness_root / "sandbox",
        host_id="test-host",
        export_dir=harness_root / "export",
    )
    result = harness.run_scenario(
        default_demo_packages(),
        used_package="alpha-cli",
        settings=Settings(anonymize=False, protected_packages=[]),
        prefer_find=False,
    )
    usage_path = result.export_dir / "test-host-usage.log"
    package_path = result.export_dir / "test-host-all_package_files.log"
    assert usage_path.is_file()
    assert package_path.is_file()
    assert result.analysis.package_rankings.shape[0] == 2
