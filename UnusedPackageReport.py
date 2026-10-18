#!/usr/bin/env python3
import os

from unusedos.analyze import analyze_directory
from unusedos.config import Settings
from unusedos.io import build_anonymizer, write_pipe_csv


def main():
    input_dir = "insights-rand-1"
    settings = Settings.from_env()
    anonymizer = build_anonymizer(settings)
    result = analyze_directory(input_dir, settings=settings, host_id=input_dir, anonymizer=anonymizer)

    output_dir = os.path.join("reports", input_dir)
    write_pipe_csv(
        result.package_rankings,
        os.path.join(output_dir, "package_rankings.csv"),
        list(result.package_rankings.columns),
        anonymizer=anonymizer,
    )
    print(f"Review-only rankings written to {output_dir}/package_rankings.csv")
    print(result.package_rankings.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
