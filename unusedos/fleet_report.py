"""Summarize unused packages across containers from log archives and reports."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from unusedos.analyze import analyze_directory
from unusedos.archive import HostArtifacts, discover_hosts
from unusedos.config import Settings
from unusedos.io import build_anonymizer, write_pipe_csv


@dataclass
class FleetSummary:
    archive_root: Path
    hosts: list[HostArtifacts]
    host_rankings: pd.DataFrame
    package_summary: pd.DataFrame
    host_summary: pd.DataFrame
    stale_cutoff_epoch: float


def _load_rankings_for_host(host: HostArtifacts, settings: Settings) -> pd.DataFrame:
    anonymizer = build_anonymizer(settings)
    if host.has_rankings and host.rankings_csv is not None:
        frame = pd.read_csv(host.rankings_csv, sep="|")
        if "host" not in frame.columns:
            frame.insert(0, "host", host.host_id)
        return frame

    if not host.has_raw_logs:
        raise FileNotFoundError(f"No analyzable data for host {host.host_id} in {host.directory}")

    result = analyze_directory(host.directory, settings=settings, host_id=host.host_id, anonymizer=anonymizer)
    ranked = result.package_rankings.copy()
    ranked.insert(0, "host", host.host_id)
    return ranked


def _stale_cutoff(settings: Settings) -> float:
    return time.time() - (settings.stale_age_days * 86400)


def build_fleet_summary(archive_root: str | Path, settings: Settings | None = None) -> FleetSummary:
    settings = settings or Settings.from_env()
    archive_root = Path(archive_root)
    hosts = discover_hosts(archive_root)
    if not hosts:
        raise FileNotFoundError(f"No host archives or reports found under {archive_root}")

    frames: list[pd.DataFrame] = []
    for host in hosts:
        try:
            frames.append(_load_rankings_for_host(host, settings))
        except FileNotFoundError:
            continue

    if not frames:
        raise FileNotFoundError(f"No rankings could be built from {archive_root}")

    host_rankings = pd.concat(frames, ignore_index=True)
    cutoff = _stale_cutoff(settings)
    host_rankings = host_rankings.copy()
    host_rankings["access_time"] = pd.to_numeric(host_rankings["access_time"], errors="coerce")
    host_rankings["stale"] = host_rankings["access_time"] < cutoff

    package_summary = (
        host_rankings.groupby("package", as_index=False)
        .agg(
            host_count=("host", "nunique"),
            hosts=("host", lambda values: ",".join(sorted(set(values)))),
            oldest_access_time=("access_time", "min"),
            newest_access_time=("access_time", "max"),
            stale_host_count=("stale", "sum"),
        )
        .sort_values(["stale_host_count", "oldest_access_time"], ascending=[False, True])
        .reset_index(drop=True)
    )
    package_summary["stale_on_all_hosts"] = package_summary["stale_host_count"] == package_summary["host_count"]

    host_summary = (
        host_rankings.groupby("host", as_index=False)
        .agg(
            package_count=("package", "count"),
            stale_package_count=("stale", "sum"),
            oldest_access_time=("access_time", "min"),
        )
        .sort_values("stale_package_count", ascending=False)
        .reset_index(drop=True)
    )

    return FleetSummary(
        archive_root=archive_root,
        hosts=hosts,
        host_rankings=host_rankings,
        package_summary=package_summary,
        host_summary=host_summary,
        stale_cutoff_epoch=cutoff,
    )


def render_markdown(summary: FleetSummary, settings: Settings | None = None) -> str:
    settings = settings or Settings.from_env()
    stale_packages = summary.package_summary[summary.package_summary["stale_host_count"] > 0]
    fleet_wide = summary.package_summary[summary.package_summary["stale_on_all_hosts"]]

    lines = [
        "# UnusedOS fleet summary",
        "",
        f"Archive: `{summary.archive_root}`",
        f"Hosts analyzed: {summary.host_rankings['host'].nunique()}",
        f"Stale threshold: {settings.stale_age_days} days (access_time < {summary.stale_cutoff_epoch:.0f})",
        "",
        "## Host overview",
        "",
        "| Host | Packages | Stale packages | Oldest access (epoch) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for _, row in summary.host_summary.iterrows():
        lines.append(
            f"| {row['host']} | {int(row['package_count'])} | {int(row['stale_package_count'])} | {row['oldest_access_time']:.0f} |"
        )

    lines.extend(
        [
            "",
            "## Packages stale on every host",
            "",
        ]
    )
    if fleet_wide.empty:
        lines.append("_None_")
    else:
        lines.append("| Package | Hosts | Oldest access (epoch) |")
        lines.append("| --- | ---: | ---: |")
        for _, row in fleet_wide.iterrows():
            lines.append(f"| {row['package']} | {int(row['host_count'])} | {row['oldest_access_time']:.0f} |")

    lines.extend(["", "## Top cross-container stale packages", ""])
    if stale_packages.empty:
        lines.append("_None_")
    else:
        lines.append("| Package | Stale hosts | Total hosts | Oldest access (epoch) |")
        lines.append("| --- | ---: | ---: | ---: |")
        for _, row in stale_packages.head(25).iterrows():
            lines.append(
                f"| {row['package']} | {int(row['stale_host_count'])} | {int(row['host_count'])} | {row['oldest_access_time']:.0f} |"
            )

    lines.append("")
    return "\n".join(lines)


def write_fleet_report(
    archive_root: str | Path,
    output_dir: str | Path,
    settings: Settings | None = None,
) -> FleetSummary:
    settings = settings or Settings.from_env()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = build_fleet_summary(archive_root, settings=settings)
    anonymizer = build_anonymizer(settings)

    write_pipe_csv(
        summary.host_rankings,
        output_dir / "fleet_host_rankings.csv",
        list(summary.host_rankings.columns),
        anonymizer=anonymizer,
    )
    write_pipe_csv(
        summary.package_summary,
        output_dir / "fleet_package_summary.csv",
        list(summary.package_summary.columns),
        anonymizer=anonymizer,
    )
    write_pipe_csv(
        summary.host_summary,
        output_dir / "fleet_host_summary.csv",
        list(summary.host_summary.columns),
        anonymizer=anonymizer,
    )
    (output_dir / "fleet_summary.md").write_text(render_markdown(summary, settings), encoding="utf-8")
    return summary
