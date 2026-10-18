"""CSV/PSV readers and writers with optional anonymization."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from unusedos.anonymize import Anonymizer
from unusedos.config import Settings


def read_csv_filter_convert(
    file_path: str | Path,
    column_names: list[str],
    numeric_tail: int,
    delimiter: str = "|",
    anonymizer: Anonymizer | None = None,
) -> tuple[pd.DataFrame, int]:
    file_path = Path(file_path)
    valid_rows: list[list[str | float]] = []
    non_convertible_count = 0

    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            columns = line.strip().split(delimiter)
            if len(columns) != len(column_names):
                continue
            if anonymizer is not None and anonymizer.enabled:
                columns[0] = anonymizer.anonymize_path(columns[0]) or columns[0]
            try:
                for item in range(1, numeric_tail + 1):
                    columns[-item] = float(columns[-item])
                valid_rows.append(columns)
            except ValueError:
                non_convertible_count += 1

    return pd.DataFrame(valid_rows, columns=column_names), non_convertible_count


def write_pipe_csv(
    df: pd.DataFrame,
    output_path: str | Path,
    columns: list[str],
    anonymizer: Anonymizer | None = None,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = df[columns].copy()
    if anonymizer is not None and anonymizer.enabled and "path" in frame.columns:
        frame["path"] = frame["path"].apply(anonymizer.anonymize_path)
    frame.to_csv(output_path, sep="|", index=False)


def build_anonymizer(settings: Settings) -> Anonymizer:
    return Anonymizer(
        enabled=settings.anonymize,
        host_replacement=settings.anonymize_host,
        path_replacement=settings.anonymize_replacement,
        segments=tuple(settings.anonymize_segments),
    )
