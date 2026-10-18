"""Merge package and usage datasets and rank packages for review."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from unusedos.anonymize import Anonymizer
from unusedos.config import Settings
from unusedos.io import read_csv_filter_convert


@dataclass
class AnalysisResult:
    merged_df: pd.DataFrame
    package_rankings: pd.DataFrame
    non_packaged_dirs: pd.Series
    unreported_package_paths: pd.DataFrame
    atime_warnings: list[str]


def _resolve_input_paths(input_dir: Path, host_id: str | None) -> tuple[Path, Path]:
    host = host_id or input_dir.name
    packages = input_dir / f"{host}-all_package_files.log"
    usage = input_dir / f"{host}-usage.log"
    if packages.is_file() and usage.is_file():
        return packages, usage

    packages = input_dir / "files_packages.csv"
    usage = input_dir / "files_info.csv"
    if packages.is_file() and usage.is_file():
        return packages, usage

    raise FileNotFoundError(
        f"Expected artifact pair in {input_dir}: "
        f"<host>-all_package_files.log + <host>-usage.log or files_packages.csv + files_info.csv"
    )


def check_atime_reliability(mounts_path: Path | None = None) -> list[str]:
    warnings: list[str] = []
    mounts_path = mounts_path or Path("/proc/mounts")
    if not mounts_path.is_file():
        warnings.append("Cannot read mount table; atime reliability was not checked.")
        return warnings

    for line in mounts_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        mount_point, fs_type, options = parts[1], parts[2], parts[3]
        if fs_type != "ext4":
            continue
        opts = options.split(",")
        if "noatime" in opts:
            warnings.append(f"{mount_point}: mounted with noatime; access timestamps are not updated on read.")
        elif "strictatime" not in opts:
            warnings.append(
                f"{mount_point}: default/relatime behavior — atime updates are limited and may under-report reads."
            )
        if "lazytime" in opts:
            warnings.append(f"{mount_point}: lazytime delays atime persistence; offline scans may be stale.")
    return warnings


def analyze_directory(
    input_dir: str | Path,
    settings: Settings | None = None,
    host_id: str | None = None,
    anonymizer: Anonymizer | None = None,
) -> AnalysisResult:
    settings = settings or Settings.from_env()
    anonymizer = anonymizer or Anonymizer(enabled=settings.anonymize)
    input_dir = Path(input_dir)
    packages_input, usage_input = _resolve_input_paths(input_dir, host_id)

    packages_df, _ = read_csv_filter_convert(
        packages_input, ["path", "package"], 0, "|", anonymizer=anonymizer
    )
    usage_df, _ = read_csv_filter_convert(
        usage_input, ["path", "creation_time", "access_time"], 2, "|", anonymizer=anonymizer
    )

    usage_df = usage_df.dropna(subset=["access_time"]).copy()

    merged_df = pd.merge(packages_df, usage_df, on="path", how="outer", indicator=True)
    merged_df["directory"] = merged_df["path"].apply(
        lambda value: os.path.dirname(value) if pd.notnull(value) else value
    )
    merged_df.fillna({"package": "Unknown", "creation_time": pd.NA, "access_time": pd.NA}, inplace=True)

    packaged = merged_df[merged_df["_merge"] == "both"].copy()
    rankings = (
        packaged.groupby("package", as_index=False)["access_time"]
        .min()
        .sort_values("access_time")
        .reset_index(drop=True)
    )
    rankings["review_only"] = True
    rankings = rankings[~rankings["package"].isin(settings.protected_packages)]

    non_packaged = merged_df[merged_df["_merge"] == "right_only"]
    non_packaged_dirs = non_packaged.groupby("directory").size().sort_values(ascending=False)
    unreported = merged_df[merged_df["_merge"] == "left_only"][["path", "package"]]

    return AnalysisResult(
        merged_df=merged_df,
        package_rankings=rankings,
        non_packaged_dirs=non_packaged_dirs,
        unreported_package_paths=unreported,
        atime_warnings=check_atime_reliability(),
    )


def analyze_fleet(root_dir: str | Path, settings: Settings | None = None) -> pd.DataFrame:
    settings = settings or Settings.from_env()
    anonymizer = Anonymizer(
        enabled=settings.anonymize,
        host_replacement=settings.anonymize_host,
        path_replacement=settings.anonymize_replacement,
        segments=tuple(settings.anonymize_segments),
    )
    root_dir = Path(root_dir)
    frames: list[pd.DataFrame] = []

    for child in sorted(root_dir.iterdir()):
        if not child.is_dir():
            continue
        try:
            result = analyze_directory(child, settings=settings, anonymizer=anonymizer)
        except FileNotFoundError:
            continue
        ranked = result.package_rankings.copy()
        ranked.insert(0, "host", child.name)
        frames.append(ranked)

    if not frames:
        raise FileNotFoundError(f"No analyzable host directories found under {root_dir}")

    return pd.concat(frames, ignore_index=True)
