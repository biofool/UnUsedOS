"""Synthetic filesystem harness for usage-detection tests.

Builds a mini directory tree with a fake package inventory, backdates file
timestamps, simulates running a package (read/execute + fresh atime), collects
usage in the same pipe format as production ``find``, and runs UnusedOS analysis.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from unusedos.analyze import AnalysisResult, analyze_directory
from unusedos.config import Settings


@dataclass(frozen=True)
class PackageSpec:
    """Files to create for one logical package."""

    name: str
    files: dict[str, str] = field(default_factory=dict)
    executable: str | None = None

    def iter_paths(self) -> list[str]:
        paths = sorted(self.files)
        if self.executable and self.executable not in self.files:
            paths.append(self.executable)
        return paths


@dataclass
class HarnessResult:
    root: Path
    export_dir: Path
    host_id: str
    analysis: AnalysisResult
    used_package: str
    unused_packages: list[str]


class UsageDetectionHarness:
    """Backdate a synthetic tree, run one package, collect usage, analyze."""

    def __init__(
        self,
        root: Path,
        *,
        host_id: str = "harness-host",
        export_dir: Path | None = None,
    ) -> None:
        self.root = root.resolve()
        self.host_id = host_id
        self.export_dir = (export_dir or root / "export").resolve()
        self._inventory: dict[Path, str] = {}

    def install_packages(self, packages: list[PackageSpec]) -> None:
        """Create package files under ``root`` and record path|package inventory."""
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True)
        self._inventory.clear()

        for spec in packages:
            for rel_path, content in spec.files.items():
                path = self._write_file(
                    rel_path,
                    content,
                    executable=(spec.executable is not None and rel_path == spec.executable),
                )
                self._inventory[path] = spec.name
            if spec.executable and spec.executable not in spec.files:
                path = self._write_file(spec.executable, "", executable=True)
                self._inventory[path] = spec.name

    def _write_file(self, rel_path: str, content: str, *, executable: bool) -> Path:
        rel = rel_path.lstrip("/")
        path = (self.root / rel).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"package path escapes sandbox root: {rel_path!r}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if executable:
            path.chmod(0o755)
        return path

    def all_files(self) -> list[Path]:
        return sorted(self._inventory)

    def files_for_package(self, package_name: str) -> list[Path]:
        return [path for path, pkg in self._inventory.items() if pkg == package_name]

    def backdate_all(
        self,
        *,
        access_time: float,
        modification_time: float | None = None,
    ) -> None:
        """Set stale atime/mtime on every sandbox file."""
        mtime = modification_time if modification_time is not None else access_time
        for path in self.all_files():
            os.utime(path, (access_time, mtime))

    def run_package(
        self,
        package_name: str,
        *,
        access_time: float | None = None,
    ) -> None:
        """Simulate package use: execute or read files, then refresh atime."""
        paths = self.files_for_package(package_name)
        if not paths:
            raise ValueError(f"Unknown package: {package_name}")

        fresh_atime = access_time if access_time is not None else time.time()
        for path in paths:
            if os.access(path, os.X_OK):
                subprocess.run(
                    ["/bin/sh", str(path)],
                    cwd=str(self.root),
                    check=False,
                    capture_output=True,
                    text=True,
                )
            else:
                path.read_bytes()
            os.utime(path, (fresh_atime, path.stat().st_mtime))

    def write_package_inventory(self) -> Path:
        """Write ``<host>-all_package_files.log``."""
        self.export_dir.mkdir(parents=True, exist_ok=True)
        out = self.export_dir / f"{self.host_id}-all_package_files.log"
        lines = [f"{path}|{pkg}" for path, pkg in sorted(self._inventory.items())]
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out

    def collect_usage_log(self, *, prefer_find: bool = True) -> Path:
        """Collect ``path|mtime|atime`` rows like production ``find -printf``."""
        self.export_dir.mkdir(parents=True, exist_ok=True)
        out = self.export_dir / f"{self.host_id}-usage.log"
        rows = self._collect_with_find() if prefer_find and shutil.which("find") else self._collect_with_stat()
        out.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
        return out

    def _collect_with_find(self) -> list[str]:
        cmd = [
            "find",
            str(self.root),
            "-xdev",
            "-type",
            "f",
            "-printf",
            "%p|%T@|%A@\\n",
        ]
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return [line for line in proc.stdout.splitlines() if line.strip()]

    def _collect_with_stat(self) -> list[str]:
        rows: list[str] = []
        for path in self.all_files():
            st = path.stat()
            rows.append(f"{path}|{st.st_mtime}|{st.st_atime}")
        return rows

    def analyze(self, settings: Settings | None = None) -> AnalysisResult:
        return analyze_directory(self.export_dir, settings=settings, host_id=self.host_id)

    def run_scenario(
        self,
        packages: list[PackageSpec],
        *,
        used_package: str,
        stale_access_time: float = 1_000.0,
        fresh_access_time: float | None = None,
        settings: Settings | None = None,
        prefer_find: bool = True,
    ) -> HarnessResult:
        """Install tree, backdate, run one package, collect, analyze."""
        settings = settings or Settings(anonymize=False, protected_packages=[])
        self.install_packages(packages)
        self.backdate_all(access_time=stale_access_time)
        self.run_package(used_package, access_time=fresh_access_time)
        self.write_package_inventory()
        self.collect_usage_log(prefer_find=prefer_find)
        analysis = self.analyze(settings=settings)
        unused = [spec.name for spec in packages if spec.name != used_package]
        return HarnessResult(
            root=self.root,
            export_dir=self.export_dir,
            host_id=self.host_id,
            analysis=analysis,
            used_package=used_package,
            unused_packages=unused,
        )


def default_demo_packages() -> list[PackageSpec]:
    """Two-package scenario: ``alpha-cli`` is executed; ``beta-lib`` stays stale."""
    return [
        PackageSpec(
            name="alpha-cli",
            files={
                "usr/lib/alpha/data.txt": "alpha payload",
                "usr/bin/alpha-cli": '#!/bin/sh\ncat "$(dirname "$0")/../lib/alpha/data.txt"\n',
            },
            executable="usr/bin/alpha-cli",
        ),
        PackageSpec(
            name="beta-lib",
            files={
                "usr/lib/beta/data.txt": "beta payload",
                "usr/lib/beta/extra.txt": "more beta",
            },
        ),
    ]


def build_demo_harness(tmp_root: Path) -> UsageDetectionHarness:
    return UsageDetectionHarness(
        tmp_root / "sandbox",
        host_id="harness-host",
        export_dir=tmp_root / "export",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run UnusedOS usage-detection harness scenario.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("reports/harness-demo"),
        help="Working directory for sandbox + export artifacts",
    )
    parser.add_argument("--used-package", default="alpha-cli", help="Package to simulate running")
    parser.add_argument(
        "--stale-atime",
        type=float,
        default=1_000.0,
        help="Epoch seconds applied before simulated package use",
    )
    parser.add_argument(
        "--fresh-atime",
        type=float,
        default=None,
        help="Epoch seconds for used package (default: now)",
    )
    parser.add_argument("--no-find", action="store_true", help="Collect usage via stat() instead of find")
    args = parser.parse_args(argv)

    args.root.mkdir(parents=True, exist_ok=True)
    harness = UsageDetectionHarness(
        args.root / "sandbox",
        host_id="harness-host",
        export_dir=args.root / "export",
    )
    result = harness.run_scenario(
        default_demo_packages(),
        used_package=args.used_package,
        stale_access_time=args.stale_atime,
        fresh_access_time=args.fresh_atime,
        prefer_find=not args.no_find,
    )

    rankings = result.analysis.package_rankings
    print(f"Export dir: {result.export_dir}")
    print(f"Used package: {result.used_package}")
    print("Package rankings (oldest access first):")
    for _, row in rankings.iterrows():
        print(f"  {row['package']}: access_time={row['access_time']}")

    used_rank = int(rankings.index[rankings["package"] == result.used_package][0])
    unused_rank = int(rankings.index[rankings["package"] == result.unused_packages[0]][0])
    if used_rank <= unused_rank:
        print("FAIL: used package should rank after stale packages", file=sys.stderr)
        return 1

    print("Harness scenario passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
