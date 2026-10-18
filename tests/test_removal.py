from datetime import datetime, timezone
from pathlib import Path

from unusedos.cli import main
from unusedos.removal import (
    default_unused_before,
    graph_from_groups,
    load_unused_packages,
    parse_apt_removed,
    read_safe_remove_list,
    removal_closure,
    select_safe_removals,
    unexpected_removals,
    unused_before_timestamp,
    write_safe_remove_files,
)


def _graph():
    return graph_from_groups(
        {
            "leaf": [],
            "mid": [["leaf"]],
            "used": [["mid"]],
            "alone": [],
            "alt-a": [],
            "alt-b": [],
            "either": [["alt-a", "alt-b"]],
        }
    )


def test_removal_closure_follows_reverse_depends():
    graph = _graph()
    assert removal_closure(graph, {"leaf"}) == {"leaf", "mid", "used"}
    assert removal_closure(graph, {"alone"}) == {"alone"}


def test_or_dependency_keeps_one_alternative():
    graph = _graph()
    unused = {"alt-a", "alt-b", "alone"}
    planned = select_safe_removals(graph, unused)
    assert planned.packages == ["alone", "alt-a"]
    assert "alt-b" not in planned.packages
    assert "either" not in planned.joint
    assert planned.joint <= unused


def test_or_dependency_of_an_unused_package_can_drop_both_alternatives():
    planned = select_safe_removals(_graph(), {"alt-a", "alt-b", "either"})
    assert planned.packages == ["alt-a", "alt-b", "either"]


def test_chain_into_a_used_package_is_excluded():
    graph = _graph()
    planned = select_safe_removals(graph, {"leaf", "mid", "alone"})
    assert planned.packages == ["alone"]


def test_unused_chain_lists_dependents_that_would_also_be_removed():
    graph = graph_from_groups({"leaf": [], "mid": [["leaf"]]})
    planned = select_safe_removals(graph, {"leaf", "mid"})
    assert planned.packages == ["leaf", "mid"]
    assert planned.also_removed["leaf"] == ("mid",)
    assert planned.also_removed["mid"] == ()


def test_write_safe_remove_files_are_editable(tmp_path: Path):
    graph = _graph()
    planned = select_safe_removals(graph, {"alone"})
    names_path, details_path = write_safe_remove_files(tmp_path, planned, "2025-10-02")
    text = names_path.read_text(encoding="utf-8")
    assert text.startswith("#")
    assert read_safe_remove_list(names_path) == ["alone"]
    assert details_path.read_text(encoding="utf-8").splitlines() == ["package\talso_removed", "alone\t"]


def test_load_unused_packages_uses_newest_access(tmp_path: Path):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "filesystem_files.tsv").write_text(
        "/bin/old\t1\t100\n/bin/new\t1\t500\n/bin/other\t1\t100\n",
        encoding="utf-8",
    )
    (tmp_path / "files_packages.csv").write_text(
        "/bin/old,demo:amd64\n/bin/new,demo:amd64\n/bin/other,kept\n",
        encoding="utf-8",
    )
    observed = load_unused_packages(tmp_path, cutoff=200)
    assert observed.unused == {"kept"}
    assert observed.used == {"demo"}


def test_parse_apt_removed_and_unexpected():
    output = "The following packages will be REMOVED:\n  alone alt-a:amd64\n0 upgraded, 0 newly installed, 2 to remove and 0 not upgraded.\n"
    removed = parse_apt_removed(output)
    assert removed == ["alone", "alt-a"]
    assert unexpected_removals(removed, {"alone"}) == ["alt-a"]


def test_default_unused_before_is_365_days():
    today = datetime(2026, 10, 2, 15, 0, tzinfo=timezone.utc)
    assert default_unused_before(today) == "2025-10-02"
    assert unused_before_timestamp("2025-10-02") == 1759363200


def test_cli_safe_remove_writes_list_after_dry_run(tmp_path: Path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "filesystem_files.tsv").write_text("/bin/alone\t1\t100\n", encoding="utf-8")
    (tmp_path / "files_packages.csv").write_text("/bin/alone,alone\n", encoding="utf-8")
    monkeypatch.setattr("unusedos.cli.load_apt_graph", lambda: graph_from_groups({"alone": []}))
    monkeypatch.setattr(
        "unusedos.cli.simulate_apt_remove",
        lambda packages: "The following packages will be REMOVED:\n  alone\n0 upgraded, 0 newly installed, 1 to remove and 0 not upgraded.\n",
    )
    out = tmp_path / "out"
    code = main(
        [
            "safe-remove",
            "--input-dir",
            str(tmp_path),
            "--output-dir",
            str(out),
            "--unused-before",
            "2025-10-02",
        ]
    )
    assert code == 0
    assert read_safe_remove_list(out / "safe-remove.txt") == ["alone"]


def test_cli_safe_remove_refuses_a_plan_that_removes_a_used_package(tmp_path: Path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "filesystem_files.tsv").write_text("/bin/alone\t1\t100\n", encoding="utf-8")
    (tmp_path / "files_packages.csv").write_text("/bin/alone,alone\n", encoding="utf-8")
    monkeypatch.setattr("unusedos.cli.load_apt_graph", lambda: graph_from_groups({"alone": []}))
    monkeypatch.setattr(
        "unusedos.cli.simulate_apt_remove",
        lambda packages: "The following packages will be REMOVED:\n  alone used\n",
    )
    out = tmp_path / "out"
    code = main(
        [
            "safe-remove",
            "--input-dir",
            str(tmp_path),
            "--output-dir",
            str(out),
            "--unused-before",
            "2025-10-02",
        ]
    )
    assert code == 1
    assert not (out / "safe-remove.txt").exists()
