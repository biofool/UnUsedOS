from pathlib import Path

from unusedos.config import Settings
from unusedos.import_tools import import_host_directory


def test_import_host_directory_anonymizes(legacy_csv_fixture: Path, tmp_path: Path):
    settings = Settings(
        anonymize=True,
        anonymize_replacement="/redacted",
        anonymize_segments=["vigilent"],
    )
    dest = tmp_path / "out"
    import_host_directory(legacy_csv_fixture, dest, settings=settings)
    usage = (dest / "files_info.csv").read_text(encoding="utf-8")
    packages = (dest / "files_packages.csv").read_text(encoding="utf-8")
    assert "vigilent" not in usage
    assert "vigilent" not in packages
    assert "/redacted" in usage
