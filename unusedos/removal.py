"""Plan package removals that stay inside the unused set.

A package is safe to remove when every package apt would also remove is itself
unused. The planned set is safe together: dropping one of an OR-dependency
keeps a used package installed when removing both would not.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_APT_GRAPH_SCRIPT = """
import json
import sys
import apt

cache = apt.Cache()
out = {}
for pkg in cache:
    if not pkg.is_installed or pkg.installed is None:
        continue
    groups = []
    for dtype in ("Depends", "PreDepends"):
        for dep in pkg.installed.get_dependencies(dtype):
            sats = []
            for base in dep.or_dependencies:
                for ver in base.installed_target_versions:
                    sats.append(ver.package.name)
            if sats:
                groups.append(sorted(set(sats)))
    out[pkg.name] = groups
json.dump(out, sys.stdout)
"""


@dataclass
class PackageGraph:
    """Installed Depends and PreDepends, reduced to packages that satisfy them now."""

    requirements: dict[str, tuple[frozenset[str], ...]]
    reverse: dict[str, tuple[str, ...]] = field(init=False)

    def __post_init__(self) -> None:
        rev: dict[str, set[str]] = defaultdict(set)
        for name, groups in self.requirements.items():
            for group in groups:
                for satisfier in group:
                    rev[satisfier].add(name)
        self.reverse = {name: tuple(dependents) for name, dependents in rev.items()}


@dataclass
class UnusedPackages:
    unused: set[str]
    used: set[str]
    skipped_lines: int


@dataclass
class SafeRemoval:
    packages: list[str]
    also_removed: dict[str, tuple[str, ...]]
    joint: frozenset[str]


def graph_from_groups(groups: dict[str, list[list[str]]]) -> PackageGraph:
    requirements = {
        name: tuple(frozenset(group) for group in dep_groups if group)
        for name, dep_groups in groups.items()
    }
    return PackageGraph(requirements)


def removal_closure(graph: PackageGraph, seeds: set[str]) -> set[str]:
    """Packages apt must remove so every remaining hard dependency stays satisfiable."""
    removing: set[str] = set()
    queue: list[str] = []
    for seed in seeds:
        if seed in graph.requirements and seed not in removing:
            removing.add(seed)
            queue.append(seed)
    while queue:
        gone = queue.pop()
        for dependent in graph.reverse.get(gone, ()):
            if dependent in removing:
                continue
            for group in graph.requirements[dependent]:
                if group <= removing:
                    removing.add(dependent)
                    queue.append(dependent)
                    break
    return removing


def select_safe_removals(graph: PackageGraph, unused: set[str]) -> SafeRemoval:
    """Largest removable set whose combined closure stays inside ``unused``.

    Candidates are considered smallest-closure first so an OR-dependency keeps
    one alternative installed when removing both would pull in a used package.
    """
    solos: dict[str, set[str]] = {}
    for name in sorted(unused):
        if name not in graph.requirements:
            continue
        closure = removal_closure(graph, {name})
        if closure <= unused:
            solos[name] = closure

    chosen: list[str] = []
    chosen_set: set[str] = set()
    for name in sorted(solos, key=lambda item: (len(solos[item]), item)):
        trial = removal_closure(graph, chosen_set | {name})
        if trial <= unused:
            chosen.append(name)
            chosen_set.add(name)

    joint = removal_closure(graph, chosen_set) if chosen_set else set()
    ordered = sorted(chosen)
    also_removed = {
        name: tuple(sorted(solos[name] - {name}))
        for name in ordered
    }
    return SafeRemoval(packages=ordered, also_removed=also_removed, joint=frozenset(joint))


def unused_before_timestamp(day: str) -> int:
    """UTC midnight at the start of ``YYYY-MM-DD``."""
    parsed = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def default_unused_before(today: datetime | None = None) -> str:
    moment = today or datetime.now(timezone.utc)
    cutoff = (moment - timedelta(days=365)).date()
    return cutoff.isoformat()


def load_unused_packages(input_dir: Path, cutoff: int) -> UnusedPackages:
    """Packages whose newest collected file access is strictly before ``cutoff``."""
    input_dir = Path(input_dir)
    atime_path = input_dir / "cache" / "filesystem_files.tsv"
    packages_path = input_dir / "files_packages.csv"
    if not atime_path.is_file() or not packages_path.is_file():
        raise FileNotFoundError(
            f"Expected {atime_path} and {packages_path} from scripts/collect-on-host.sh"
        )

    atime_by_path: dict[str, int] = {}
    skipped = 0
    for line_no, line in enumerate(atime_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        parts = line.split("\t")
        if len(parts) < 3:
            skipped += 1
            logger.warning("Skipping short filesystem row %s in %s", line_no, atime_path)
            continue
        try:
            atime_by_path[parts[0]] = int(parts[2])
        except ValueError:
            skipped += 1
            logger.warning("Skipping non-integer atime on %s line %s", atime_path, line_no)

    max_atime: dict[str, int] = {}
    for line_no, line in enumerate(packages_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if "," not in line:
            skipped += 1
            logger.warning("Skipping files_packages row %s with no package column", line_no)
            continue
        path, package = line.rsplit(",", 1)
        atime = atime_by_path.get(path)
        if atime is None:
            continue
        short = package.split(":", 1)[0]
        previous = max_atime.get(short)
        if previous is None or atime > previous:
            max_atime[short] = atime

    unused = {name for name, atime in max_atime.items() if atime < cutoff}
    used = set(max_atime) - unused
    return UnusedPackages(unused=unused, used=used, skipped_lines=skipped)


def load_apt_graph() -> PackageGraph:
    """Read the installed Depends and PreDepends graph.

    The project virtualenv often lacks python-apt. Fall back to the system
    interpreter, which provides the ``apt`` module on Debian and Ubuntu.
    """
    try:
        import apt  # type: ignore[import-untyped]
    except ImportError:
        apt = None
    if apt is not None:
        return graph_from_groups(_groups_from_cache(apt))

    system_python = Path("/usr/bin/python3")
    if not system_python.is_file():
        raise RuntimeError(
            "python-apt is not installed in this interpreter and /usr/bin/python3 is missing. "
            "Install the python3-apt package to plan removals."
        )
    completed = subprocess.run(
        [str(system_python), "-c", _APT_GRAPH_SCRIPT],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit {completed.returncode}"
        raise RuntimeError(f"Could not read the apt dependency graph: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The apt dependency graph was not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("The apt dependency graph JSON was not an object.")
    return graph_from_groups(payload)


def _groups_from_cache(apt_module: object) -> dict[str, list[list[str]]]:
    cache = apt_module.Cache()  # type: ignore[attr-defined]
    groups: dict[str, list[list[str]]] = {}
    for pkg in cache:
        if not pkg.is_installed or pkg.installed is None:
            continue
        dep_groups: list[list[str]] = []
        for dtype in ("Depends", "PreDepends"):
            for dep in pkg.installed.get_dependencies(dtype):
                sats = sorted({
                    ver.package.name
                    for base in dep.or_dependencies
                    for ver in base.installed_target_versions
                })
                if sats:
                    dep_groups.append(sats)
        groups[pkg.name] = dep_groups
    return groups


def write_safe_remove_files(output_dir: Path, result: SafeRemoval, unused_before: str) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    names_path = output_dir / "safe-remove.txt"
    details_path = output_dir / "safe-remove-details.tsv"
    header = (
        f"# Packages that can be removed together without also removing a package\n"
        f"# used on or after {unused_before}.\n"
        f"# One package name per line. Blank lines and lines starting with # are ignored.\n"
        f"# Edit this file to drop packages. It does not uninstall anything.\n"
    )
    names_path.write_text(header + "\n".join(result.packages) + ("\n" if result.packages else ""), encoding="utf-8")
    detail_lines = ["package\talso_removed"]
    for name in result.packages:
        detail_lines.append(f"{name}\t{' '.join(result.also_removed[name])}")
    details_path.write_text("\n".join(detail_lines) + "\n", encoding="utf-8")
    return names_path, details_path


def read_safe_remove_list(path: Path) -> list[str]:
    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        names.append(stripped.split(":", 1)[0])
    return names


def parse_apt_removed(output: str) -> list[str]:
    """Package names from an ``apt-get -s remove`` plan."""
    removed: list[str] = []
    capturing = False
    for line in output.splitlines():
        if line.startswith("The following packages will be REMOVED:"):
            capturing = True
            continue
        if not capturing:
            continue
        if not line.startswith(" "):
            break
        removed.extend(token.split(":", 1)[0] for token in line.split())
    return removed


def unexpected_removals(removed: list[str], unused: set[str]) -> list[str]:
    return sorted({name for name in removed if name not in unused})


def simulate_apt_remove(packages: list[str]) -> str:
    """Dry-run only. ``-s`` is fixed so this cannot uninstall packages."""
    if not packages:
        return ""
    completed = subprocess.run(
        ["apt-get", "-s", "-o", "Debug::NoLocking=true", "remove", "--", *packages],
        check=False,
        capture_output=True,
        text=True,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        raise RuntimeError(f"apt-get -s remove failed: {detail}")
    if "The following packages will be REMOVED:" not in completed.stdout and packages:
        raise RuntimeError("apt-get -s remove succeeded but did not list packages to remove.")
    return output
