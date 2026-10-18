#!/usr/bin/env python3
"""UnusedOS command-line interface."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from unusedos.analyze import analyze_directory, analyze_fleet, check_atime_reliability
from unusedos.config import Settings
from unusedos.fleet_report import write_fleet_report
from unusedos.import_tools import import_host_directory
from unusedos.io import build_anonymizer, write_pipe_csv
from unusedos.removal import (
    default_unused_before,
    load_apt_graph,
    load_unused_packages,
    parse_apt_removed,
    read_safe_remove_list,
    select_safe_removals,
    simulate_apt_remove,
    unexpected_removals,
    unused_before_timestamp,
    write_safe_remove_files,
)


def _cmd_check_atime(args: argparse.Namespace) -> int:
    mounts = Path(args.mounts) if args.mounts else None
    warnings = check_atime_reliability(mounts)
    if not warnings:
        print("No ext4 atime reliability warnings detected.")
        return 0
    print("ext4 atime reliability warnings:")
    for warning in warnings:
        print(f"  - {warning}")
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    anonymizer = build_anonymizer(settings)
    result = analyze_directory(args.input_dir, settings=settings, host_id=args.host, anonymizer=anonymizer)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_pipe_csv(
        result.package_rankings,
        output_dir / "package_rankings.csv",
        list(result.package_rankings.columns),
        anonymizer=anonymizer,
    )
    write_pipe_csv(
        result.unreported_package_paths,
        output_dir / "unreported_package_paths.csv",
        ["path", "package"],
        anonymizer=anonymizer,
    )

    print(f"Wrote review artifacts to {output_dir}")
    print(f"Ranked {len(result.package_rankings)} packages (protected packages excluded).")
    if result.atime_warnings:
        print("\nAtime warnings (see docs/ATIME-RELIABILITY.md):")
        for warning in result.atime_warnings:
            print(f"  - {warning}")
    return 0


def _cmd_analyze_fleet(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    anonymizer = build_anonymizer(settings)
    fleet = analyze_fleet(args.root_dir, settings=settings)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_pipe_csv(
        fleet,
        output_dir / "fleet_package_rankings.csv",
        list(fleet.columns),
        anonymizer=anonymizer,
    )
    print(f"Wrote fleet rankings for {fleet['host'].nunique()} hosts to {output_dir / 'fleet_package_rankings.csv'}")
    return 0


def _cmd_import(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    import_host_directory(Path(args.source_dir), Path(args.dest_dir), settings=settings)
    print(f"Imported and normalized artifacts into {args.dest_dir}")
    if settings.anonymize:
        print("Anonymization enabled via .env / environment.")
    return 0


def _cmd_summarize(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    summary = write_fleet_report(args.archive_root, args.output_dir, settings=settings)
    stale = summary.package_summary[summary.package_summary["stale_host_count"] > 0]
    print(f"Wrote fleet report to {args.output_dir}")
    print(f"Hosts: {summary.host_rankings['host'].nunique()}")
    print(f"Stale packages (any host): {len(stale)}")
    print(f"Markdown summary: {Path(args.output_dir) / 'fleet_summary.md'}")
    return 0


def _cmd_safe_remove(args: argparse.Namespace) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    unused_before = args.unused_before or default_unused_before()
    cutoff = unused_before_timestamp(unused_before)
    observed = load_unused_packages(Path(args.input_dir), cutoff)
    if observed.skipped_lines:
        print(f"Skipped {observed.skipped_lines} malformed collection rows.", file=sys.stderr)
    planned = select_safe_removals(load_apt_graph(), observed.unused)
    output_dir = Path(args.output_dir)
    if not args.no_simulate:
        simulation = simulate_apt_remove(planned.packages)
        removed = parse_apt_removed(simulation)
        unexpected = unexpected_removals(removed, observed.unused)
        if unexpected:
            print(
                "apt-get -s remove would also remove packages that have been used:",
                file=sys.stderr,
            )
            for name in unexpected:
                print(f"  {name}", file=sys.stderr)
            return 1
        for line in simulation.splitlines():
            if "essential" in line.lower() or line.startswith("0 upgraded,"):
                print(line)
        if removed and set(removed) != set(planned.packages):
            extra = sorted(set(removed) - set(planned.packages))
            missing = sorted(set(planned.packages) - set(removed))
            if extra or missing:
                print(
                    "apt-get -s remove plan differs from the dependency closure: "
                    f"extra={extra or 'none'} missing={missing or 'none'}"
                )
    names_path, details_path = write_safe_remove_files(output_dir, planned, unused_before)
    written = read_safe_remove_list(names_path)
    print(f"Unused packages (newest access before {unused_before}): {len(observed.unused)}")
    print(f"Safe to remove together: {len(written)}")
    print(f"Wrote {names_path}")
    print(f"Wrote {details_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UnusedOS analysis tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    atime_parser = subparsers.add_parser("check-atime", help="Check ext4 mount options affecting atime reliability")
    atime_parser.add_argument("--mounts", help="Path to mounts file (default: /proc/mounts when present)")
    atime_parser.set_defaults(func=_cmd_check_atime)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze one collected host dataset")
    analyze_parser.add_argument("--input-dir", required=True)
    analyze_parser.add_argument("--host")
    analyze_parser.add_argument("--output-dir", default="reports")
    analyze_parser.set_defaults(func=_cmd_analyze)

    fleet_parser = subparsers.add_parser("analyze-fleet", help="Analyze many host datasets under one root directory")
    fleet_parser.add_argument("--root-dir", required=True)
    fleet_parser.add_argument("--output-dir", default="reports/fleet")
    fleet_parser.set_defaults(func=_cmd_analyze_fleet)

    import_parser = subparsers.add_parser("import", help="Normalize legacy CSV exports into review-ready pipe files")
    import_parser.add_argument("--source-dir", required=True)
    import_parser.add_argument("--dest-dir", required=True)
    import_parser.set_defaults(func=_cmd_import)

    summarize_parser = subparsers.add_parser(
        "summarize",
        help="Search log archives and reports under a folder; summarize unused packages fleet-wide",
    )
    summarize_parser.add_argument(
        "--archive-root",
        required=True,
        help="Root folder containing per-host log archives and/or nested package_rankings.csv reports",
    )
    summarize_parser.add_argument("--output-dir", default="reports/fleet-summary")
    summarize_parser.set_defaults(func=_cmd_summarize)

    safe_parser = subparsers.add_parser(
        "safe-remove",
        help="List unused packages that can be removed without removing a used package",
    )
    safe_parser.add_argument("--input-dir", required=True, help="Host export from collect-on-host.sh")
    safe_parser.add_argument("--output-dir", help="Directory for safe-remove.txt (default: input dir)")
    safe_parser.add_argument(
        "--unused-before",
        help="UTC date (YYYY-MM-DD). Packages used on or after this date stay installed. Default: 365 days ago.",
    )
    safe_parser.add_argument(
        "--no-simulate",
        action="store_true",
        help="Skip apt-get -s remove. The list is still review-only.",
    )
    safe_parser.set_defaults(func=_cmd_safe_remove)

    args = parser.parse_args(argv)
    if args.command == "safe-remove" and not args.output_dir:
        args.output_dir = args.input_dir
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
