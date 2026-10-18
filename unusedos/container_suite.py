"""Multi-container test suite: simulate hosts, analyze, archive, and summarize."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from unusedos.analyze import analyze_directory
from unusedos.config import Settings
from unusedos.fleet_report import FleetSummary, write_fleet_report
from unusedos.harness import PackageSpec, UsageDetectionHarness
from unusedos.io import build_anonymizer, write_pipe_csv


@dataclass(frozen=True)
class ContainerScenario:
    host_id: str
    used_package: str
    stale_access_time: float
    fresh_access_time: float
    packages: tuple[PackageSpec, ...]


def _default_packages() -> tuple[PackageSpec, ...]:
    return (
        PackageSpec(
            name="alpha-cli",
            files={
                "usr/lib/alpha/data.txt": "alpha",
                "usr/bin/alpha-cli": '#!/bin/sh\necho alpha\n',
            },
            executable="usr/bin/alpha-cli",
        ),
        PackageSpec(
            name="beta-lib",
            files={"usr/lib/beta/data.txt": "beta"},
        ),
        PackageSpec(
            name="shared-utils",
            files={"usr/lib/shared/util.txt": "shared"},
        ),
    )


def _timestamps() -> tuple[float, float]:
    now = time.time()
    return now - (120 * 86400), now


def _scenario(
    host_id: str,
    used_package: str,
    packages: tuple[PackageSpec, ...] | None = None,
) -> ContainerScenario:
    stale_at, fresh_at = _timestamps()
    return ContainerScenario(
        host_id=host_id,
        used_package=used_package,
        stale_access_time=stale_at,
        fresh_access_time=fresh_at,
        packages=packages or _default_packages(),
    )


CONTAINER_SCENARIOS: tuple[ContainerScenario, ...] = (
    _scenario("container-web", "alpha-cli"),
    _scenario("container-api", "beta-lib"),
    _scenario("container-worker", "shared-utils"),
)


@dataclass
class ContainerSuiteResult:
    archive_root: Path
    report_dir: Path
    summary: FleetSummary
    scenarios: tuple[ContainerScenario, ...]


def run_container_scenario(
    scenario: ContainerScenario,
    archive_root: Path,
    settings: Settings | None = None,
) -> Path:
    settings = settings or Settings(anonymize=False, protected_packages=[], stale_age_days=90)
    host_dir = archive_root / scenario.host_id
    harness = UsageDetectionHarness(
        host_dir / "sandbox",
        host_id=scenario.host_id,
        export_dir=host_dir,
    )
    harness.run_scenario(
        list(scenario.packages),
        used_package=scenario.used_package,
        stale_access_time=scenario.stale_access_time,
        fresh_access_time=scenario.fresh_access_time,
        settings=settings,
        prefer_find=False,
    )

    anonymizer = build_anonymizer(settings)
    analysis = analyze_directory(host_dir, settings=settings, host_id=scenario.host_id, anonymizer=anonymizer)
    reports_dir = host_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_pipe_csv(
        analysis.package_rankings,
        reports_dir / "package_rankings.csv",
        list(analysis.package_rankings.columns),
        anonymizer=anonymizer,
    )
    return host_dir


def run_container_suite(
    archive_root: str | Path,
    report_dir: str | Path | None = None,
    scenarios: tuple[ContainerScenario, ...] | None = None,
    settings: Settings | None = None,
) -> ContainerSuiteResult:
    settings = settings or Settings(anonymize=False, protected_packages=[], stale_age_days=90)
    archive_root = Path(archive_root)
    archive_root.mkdir(parents=True, exist_ok=True)
    report_dir = Path(report_dir or archive_root / "fleet-report")

    active = scenarios or CONTAINER_SCENARIOS
    for scenario in active:
        run_container_scenario(scenario, archive_root, settings=settings)

    summary = write_fleet_report(archive_root, report_dir, settings=settings)
    return ContainerSuiteResult(
        archive_root=archive_root,
        report_dir=report_dir,
        summary=summary,
        scenarios=active,
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run UnusedOS multi-container test suite")
    parser.add_argument("--archive-root", default="reports/container-suite")
    parser.add_argument("--report-dir", help="Defaults to <archive-root>/fleet-report")
    args = parser.parse_args()

    result = run_container_suite(args.archive_root, args.report_dir)
    stale = result.summary.package_summary[result.summary.package_summary["stale_host_count"] > 0]
    print(f"Archive: {result.archive_root}")
    print(f"Report: {result.report_dir}")
    print(f"Hosts: {result.summary.host_rankings['host'].nunique()}")
    print(f"Cross-container stale packages: {len(stale)}")
    print(f"Summary: {result.report_dir / 'fleet_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
