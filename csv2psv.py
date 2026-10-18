#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from unusedos.config import Settings
from unusedos.import_tools import convert_usage_csv
from unusedos.io import build_anonymizer


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python csv2psv.py input_file output_file")
        return 1
    settings = Settings.from_env()
    convert_usage_csv(Path(sys.argv[1]), Path(sys.argv[2]), build_anonymizer(settings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
