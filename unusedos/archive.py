"""Discover host log archives and analysis reports under a directory tree."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

USAGE_SUFFIX = "-usage.log"
PACKAGE_SUFFIX = "-all_package_files.log"
RANKINGS_NAME = "package_rankings.csv"
LEGACY_USAGE = "files_info.csv"
LEGACY_PACKAGES = "files_packages.csv"


@dataclass(frozen=True)
class HostArtifacts:
    """Collected logs and/or reports for one container or host."""

    host_id: str
    directory: Path
    usage_log: Path | None = None
    package_log: Path | None = None
    rankings_csv: Path | None = None

    @property
    def has_raw_logs(self) -> bool:
        return self.usage_log is not None and self.package_log is not None

    @property
    def has_rankings(self) -> bool:
        return self.rankings_csv is not None and self.rankings_csv.is_file()


def _host_id_from_log(path: Path, suffix: str) -> str | None:
    name = path.name
    if name.endswith(suffix):
        return name[: -len(suffix)]
    return None


def _find_rankings_in_tree(directory: Path) -> list[Path]:
    return sorted(directory.rglob(RANKINGS_NAME))


def _pair_logs_in_directory(directory: Path) -> list[HostArtifacts]:
    hosts: dict[str, HostArtifacts] = {}

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        host = _host_id_from_log(path, USAGE_SUFFIX)
        if host:
            entry = hosts.get(host) or HostArtifacts(host_id=host, directory=directory)
            hosts[host] = HostArtifacts(
                host_id=host,
                directory=directory,
                usage_log=path,
                package_log=entry.package_log,
                rankings_csv=entry.rankings_csv,
            )
            continue
        host = _host_id_from_log(path, PACKAGE_SUFFIX)
        if host:
            entry = hosts.get(host) or HostArtifacts(host_id=host, directory=directory)
            hosts[host] = HostArtifacts(
                host_id=host,
                directory=directory,
                usage_log=entry.usage_log,
                package_log=path,
                rankings_csv=entry.rankings_csv,
            )

    legacy_usage = directory / LEGACY_USAGE
    legacy_packages = directory / LEGACY_PACKAGES
    if legacy_usage.is_file() and legacy_packages.is_file():
        host = directory.name
        entry = hosts.get(host) or HostArtifacts(host_id=host, directory=directory)
        hosts[host] = HostArtifacts(
            host_id=host,
            directory=directory,
            usage_log=legacy_usage,
            package_log=legacy_packages,
            rankings_csv=entry.rankings_csv,
        )

    for rankings in _find_rankings_in_tree(directory):
        host_dir = rankings.parent.parent if rankings.parent.name == "reports" else rankings.parent
        host = host_dir.name
        entry = hosts.get(host) or HostArtifacts(host_id=host, directory=host_dir)
        hosts[host] = HostArtifacts(
            host_id=host,
            directory=host_dir,
            usage_log=entry.usage_log,
            package_log=entry.package_log,
            rankings_csv=rankings,
        )

    return [host for host in hosts.values() if host.has_raw_logs or host.has_rankings]


def discover_hosts(archive_root: str | Path) -> list[HostArtifacts]:
    """Search ``archive_root`` recursively for host log pairs and report CSVs."""
    archive_root = Path(archive_root)
    if not archive_root.is_dir():
        raise FileNotFoundError(f"Archive root not found: {archive_root}")

    found: dict[tuple[str, str], HostArtifacts] = {}

    for directory in [archive_root, *sorted(archive_root.rglob("*"))]:
        if not directory.is_dir():
            continue
        for host in _pair_logs_in_directory(directory):
            key = (host.host_id, str(host.directory.resolve()))
            found[key] = host

    return sorted(found.values(), key=lambda item: (item.host_id, str(item.directory)))


def discover_reports(archive_root: str | Path) -> list[Path]:
    """Return every ``package_rankings.csv`` under ``archive_root``."""
    archive_root = Path(archive_root)
    if not archive_root.is_dir():
        raise FileNotFoundError(f"Archive root not found: {archive_root}")
    return _find_rankings_in_tree(archive_root)
