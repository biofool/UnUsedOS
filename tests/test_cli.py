from pathlib import Path

from unusedos.cli import main


def test_cli_analyze(host_fixture: Path, tmp_path: Path):
    out = tmp_path / "reports"
    code = main(["analyze", "--input-dir", str(host_fixture), "--host", "test-host", "--output-dir", str(out)])
    assert code == 0
    assert (out / "package_rankings.csv").is_file()


def test_cli_check_atime(mounts_fixture: Path):
    code = main(["check-atime", "--mounts", str(mounts_fixture)])
    assert code == 0


def test_cli_import(legacy_csv_fixture: Path, tmp_path: Path):
    dest = tmp_path / "imported"
    code = main(["import", "--source-dir", str(legacy_csv_fixture), "--dest-dir", str(dest)])
    assert code == 0
    assert (dest / "files_info.csv").is_file()
