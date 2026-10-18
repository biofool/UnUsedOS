"""Tests for archive discovery and fleet reporting."""

from __future__ import annotations

from pathlib import Path

import pytest

from unusedos.archive import discover_hosts, discover_reports
from unusedos.config import Settings
from unusedos.container_suite import run_container_suite
from unusedos.fleet_report import build_fleet_summary, write_fleet_report


def test_discover_hosts_finds_nested_archives(tmp_path: Path) -> None:
    archive = tmp_path / "log-archives"
    host_a = archive / "2024" / "container-a"
    host_b = archive / "2024" / "container-b"
    host_a.mkdir(parents=True)
    host_b.mkdir(parents=True)
    (host_a / "container-a-usage.log").write_text("/bin/a|1|2\n", encoding="utf-8")
    (host_a / "container-a-all_package_files.log").write_text("/bin/a|pkg-a\n", encoding="utf-8")
    (host_b / "container-b-usage.log").write_text("/bin/b|1|3\n", encoding="utf-8")
    (host_b / "container-b-all_package_files.log").write_text("/bin/b|pkg-b\n", encoding="utf-8")

    hosts = discover_hosts(archive)
    assert {host.host_id for host in hosts} == {"container-a", "container-b"}
    assert all(host.has_raw_logs for host in hosts)


def test_discover_reports_finds_rankings_csv(tmp_path: Path) -> None:
    archive = tmp_path / "archives"
    reports = archive / "host-x" / "reports"
    reports.mkdir(parents=True)
    (reports / "package_rankings.csv").write_text("package|access_time|review_only\npkg|1|True\n", encoding="utf-8")

    found = discover_reports(archive)
    assert len(found) == 1
    hosts = discover_hosts(archive)
    assert len(hosts) == 1
    assert hosts[0].host_id == "host-x"
    assert hosts[0].has_rankings


def test_summarize_archive_from_existing_reports(tmp_path: Path, host_fixture: Path) -> None:
    archive = tmp_path / "fleet"
    dest = host_fixture
    import shutil

    shutil.copytree(dest, archive / "test-host")
    reports = archive / "test-host" / "reports"
    reports.mkdir()
    (reports / "package_rankings.csv").write_text(
        "package|access_time|review_only\nbeta|1500.0|True\nalpha|2000.0|True\n",
        encoding="utf-8",
    )

    settings = Settings(anonymize=False, protected_packages=[], stale_age_days=90)
    summary = build_fleet_summary(archive, settings=settings)
    assert summary.host_rankings["host"].nunique() == 1
    assert "beta" in set(summary.package_summary["package"])


def test_write_fleet_report_outputs(tmp_path: Path) -> None:
    result = run_container_suite(tmp_path / "archive", tmp_path / "out")
    assert (tmp_path / "out" / "fleet_summary.md").is_file()
    assert (tmp_path / "out" / "fleet_package_summary.csv").is_file()
    assert result.summary.host_rankings["host"].nunique() == 3
    stale = result.summary.package_summary[result.summary.package_summary["stale_host_count"] > 0]
    assert len(stale) >= 2


def test_container_suite_marks_used_package_fresh_across_hosts(tmp_path: Path) -> None:
    result = run_container_suite(tmp_path / "archive", tmp_path / "out")
    for host_id, used in (
        ("container-web", "alpha-cli"),
        ("container-api", "beta-lib"),
        ("container-worker", "shared-utils"),
    ):
        host_rows = result.summary.host_rankings[result.summary.host_rankings["host"] == host_id]
        used_row = host_rows[host_rows["package"] == used]
        assert not bool(used_row["stale"].iloc[0])
