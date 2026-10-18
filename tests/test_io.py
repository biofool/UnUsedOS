from pathlib import Path

from unusedos.anonymize import Anonymizer
from unusedos.io import read_csv_filter_convert, write_pipe_csv


def test_read_csv_filter_convert_skips_bad_rows(tmp_path: Path):
    data = tmp_path / "usage.log"
    data.write_text(
        "/bin/a|1000.0|2000.0\n/bad|x|y\n/bin/b|1000.0|3000.0\n",
        encoding="utf-8",
    )
    df, bad = read_csv_filter_convert(
        data, ["path", "creation_time", "access_time"], numeric_tail=2, delimiter="|"
    )
    assert len(df) == 2
    assert bad == 1


def test_write_pipe_csv_anonymizes_paths(tmp_path: Path):
    import pandas as pd

    df = pd.DataFrame({"path": ["/customer/vigilent/x"], "package": ["alpha"]})
    out = tmp_path / "out.csv"
    write_pipe_csv(
        df,
        out,
        ["path", "package"],
        anonymizer=Anonymizer(enabled=True, path_replacement="/redacted", segments=("vigilent",)),
    )
    text = out.read_text(encoding="utf-8")
    assert "vigilent" not in text
    assert "/redacted" in text
