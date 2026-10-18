"""Convert legacy comma-separated exports to pipe-separated review artifacts."""

from __future__ import annotations

import logging
from pathlib import Path

from unusedos.anonymize import Anonymizer
from unusedos.config import Settings

logger = logging.getLogger("unusedos.import")


def convert_usage_csv(input_file: Path, output_file: Path, anonymizer: Anonymizer) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with input_file.open("r", encoding="utf-8") as source, output_file.open("w", encoding="utf-8") as dest:
        dest.write("path|creation_time|access_time\n")
        for line in source:
            text = line.strip()
            if not text or text.startswith("path"):
                continue
            parts = text.rsplit(",", 2)
            if len(parts) != 3:
                logger.error("Unparseable usage row: %s", text)
                continue
            path = anonymizer.anonymize_path(parts[0]) or parts[0]
            dest.write(f"{path}|{parts[1]}|{parts[2]}\n")


def convert_packages_csv(input_file: Path, output_file: Path, anonymizer: Anonymizer) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with input_file.open("r", encoding="utf-8") as source, output_file.open("w", encoding="utf-8") as dest:
        dest.write("path|package\n")
        for line in source:
            text = line.strip()
            if not text or text.startswith("path"):
                continue
            path, package = text.split(",", 1)
            path = anonymizer.anonymize_path(path) or path
            dest.write(f"{path}|{package}\n")


def import_host_directory(source_dir: Path, dest_dir: Path, settings: Settings | None = None) -> None:
    settings = settings or Settings.from_env()
    anonymizer = Anonymizer(
        enabled=settings.anonymize,
        host_replacement=settings.anonymize_host,
        path_replacement=settings.anonymize_replacement,
        segments=tuple(settings.anonymize_segments),
    )

    usage_src = source_dir / "files_info.csv"
    packages_src = source_dir / "files_packages.csv"
    if not usage_src.is_file() or not packages_src.is_file():
        raise FileNotFoundError(f"Expected files_info.csv and files_packages.csv in {source_dir}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    convert_usage_csv(usage_src, dest_dir / "files_info.csv", anonymizer)
    convert_packages_csv(packages_src, dest_dir / "files_packages.csv", anonymizer)
