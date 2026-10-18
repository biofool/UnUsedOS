#!/usr/bin/env python3
"""Run UnusedOS tests."""

import subprocess
import sys


def main() -> int:
    return subprocess.call([sys.executable, "-m", "pytest", "-q", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
