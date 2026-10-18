"""Host collector caches package and filesystem lists, then attributes every file."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "collect-on-host.sh"
GENERIC = ROOT / "scripts" / "collect-generic-dirs.txt"


def _write_dpkg(bin_dir: Path, *, fail: bool = False) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    exe = bin_dir / "dpkg-query"
    if fail:
        exe.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    else:
        exe.write_text(
            "#!/bin/sh\n"
            "printf 'installed\\twidget\\n'\n"
            "printf 'installed\\tplugin:amd64\\n'\n"
            "printf 'config-files\\tgone\\n'\n",
            encoding="utf-8",
        )
    exe.chmod(0o755)


def _setup(tmp_path: Path) -> tuple[Path, Path, dict]:
    root = Path(os.path.realpath(tmp_path / "root"))
    out = Path(os.path.realpath(tmp_path / "out"))
    info = tmp_path / "dpkg-info"
    bin_dir = tmp_path / "bin"
    root.mkdir(parents=True)
    out.mkdir()
    info.mkdir()
    _write_dpkg(bin_dir)

    shipped = {
        "widget": [
            f"{root}/opt/widget/bin/widget",
            f"{root}/opt/widget/bin/widget-link",
            f"{root}/opt/widget/bin/missing",
            f"{root}/var/lib/widget",
            f"{root}/var/shared",
            f"{root}/var/shared/shipped.dat",
            f"{root}/home",
            "/.",
        ],
        "plugin:amd64": [
            f"{root}/var/lib/widget/plugins",
            f"{root}/var/shared",
            f"{root}/var/shared/shipped.dat",
            f"{root}/usr/bin/plugin",
        ],
        "gone": [
            f"{root}/var/lib/gone/secret",
        ],
    }
    for package, paths in shipped.items():
        (info / f"{package}.list").write_text("\n".join(paths) + "\n", encoding="utf-8")

    files = [
        root / "opt/widget/bin/widget",
        root / "var/lib/widget/state.db",
        root / "var/lib/widget/cache/blob",
        root / "var/lib/widget/plugins/extra.dat",
        root / "var/shared/x.dat",
        root / "var/shared/shipped.dat",
        root / "home/user/notes.txt",
        root / "usr/bin/plugin",
        root / "usr/bin/manual-tool",
        root / "opt/other/stray.dat",
        root / "var/lib/gone/secret",
    ]
    for path in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")
    (root / "opt/widget/bin/widget-link").symlink_to("widget")

    generic = tmp_path / "generic-dirs.txt"
    generic.write_text(
        "\n".join(
            [
                f"{root}/home",
                f"{root}/opt",
                f"{root}/usr",
                f"{root}/usr/bin",
                f"{root}/tmp",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    return root, out, {
        "env": env,
        "info": info,
        "generic": generic,
        "bin_dir": bin_dir,
    }


def _collect(root: Path, out: Path, meta: dict, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        "bash",
        str(SCRIPT),
        "-o",
        str(out),
        "--root",
        str(root),
        "--dpkg-info",
        str(meta["info"]),
        "--generic-dirs",
        str(meta["generic"]),
        "-v",
        *args,
    ]
    return subprocess.run(cmd, check=False, capture_output=True, text=True, env=meta["env"])


def _rows(path: Path, delimiter: str) -> set[tuple[str, str]]:
    rows: set[tuple[str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        left, right = line.split(delimiter, 1)
        rows.add((left, right))
    return rows


def _info_paths(path: Path) -> set[str]:
    paths = set()
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        file_path, mtime, atime = line.split("|")
        assert mtime.isdigit() and atime.isdigit()
        paths.add(file_path)
    return paths


def test_generic_dir_stoplist_covers_shared_roots():
    lines = {line.strip() for line in GENERIC.read_text(encoding="utf-8").splitlines()}
    for path in ("/home", "/usr", "/usr/bin", "/opt", "/var", "/var/log", "/var/lib", "/tmp"):
        assert path in lines


def test_attributes_shipped_and_created_files(tmp_path: Path):
    root, out, meta = _setup(tmp_path)
    result = _collect(root, out, meta)
    assert result.returncode == 0, result.stderr

    info = _info_paths(out / "files_info.csv")
    packages = _rows(out / "files_packages.csv", ",")
    shipped = _rows(out / "all_package_files.csv", "|")

    widget_bin = f"{root}/opt/widget/bin/widget"
    state = f"{root}/var/lib/widget/state.db"
    blob = f"{root}/var/lib/widget/cache/blob"
    extra = f"{root}/var/lib/widget/plugins/extra.dat"
    shared_file = f"{root}/var/shared/shipped.dat"
    shared_created = f"{root}/var/shared/x.dat"
    notes = f"{root}/home/user/notes.txt"
    stray = f"{root}/opt/other/stray.dat"
    manual = f"{root}/usr/bin/manual-tool"
    secret = f"{root}/var/lib/gone/secret"
    missing = f"{root}/opt/widget/bin/missing"
    link = f"{root}/opt/widget/bin/widget-link"

    assert widget_bin in info
    assert state in info
    assert blob in info
    assert extra in info
    assert notes in info
    assert stray in info
    assert manual in info
    assert secret in info
    assert link in info
    assert missing not in info

    assert (widget_bin, "widget") in packages
    assert (link, "widget") in packages
    assert (state, "widget") in packages
    assert (blob, "widget") in packages
    assert (extra, "plugin:amd64") in packages
    assert (shared_file, "widget") in packages
    assert (shared_file, "plugin:amd64") in packages
    assert (f"{root}/usr/bin/plugin", "plugin:amd64") in packages

    unpackaged = {notes, stray, manual, shared_created, secret}
    assert unpackaged.isdisjoint({path for path, _package in packages})

    assert (missing, "widget") in shipped
    assert (f"{root}/var/lib/widget", "widget") in shipped
    assert (state, "widget") not in shipped
    assert all(package != "gone" for _path, package in shipped)
    assert (secret, "gone") not in shipped

    cached = (out / "cache" / "packages.list").read_text(encoding="utf-8").split()
    assert cached == ["plugin:amd64", "widget"]


def test_reuses_caches_until_refresh(tmp_path: Path):
    root, out, meta = _setup(tmp_path)
    first = _collect(root, out, meta)
    assert first.returncode == 0, first.stderr

    created = root / "var/lib/widget/after.dat"
    created.parent.mkdir(parents=True, exist_ok=True)
    created.write_text("later", encoding="utf-8")
    _write_dpkg(meta["bin_dir"], fail=True)

    second = _collect(root, out, meta)
    assert second.returncode == 0, second.stderr
    assert "Using cached package list" in second.stderr
    assert "Using cached filesystem file list" in second.stderr
    assert str(created) not in _info_paths(out / "files_info.csv")

    _write_dpkg(meta["bin_dir"], fail=False)
    refreshed = _collect(root, out, meta, "--refresh")
    assert refreshed.returncode == 0, refreshed.stderr
    assert str(created) in _info_paths(out / "files_info.csv")
    assert (str(created), "widget") in _rows(out / "files_packages.csv", ",")
