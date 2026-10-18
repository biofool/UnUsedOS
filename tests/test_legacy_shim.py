from access_times import read_csv_filter_convert


def test_legacy_access_times_shim(tmp_path):
    data = tmp_path / "data.log"
    data.write_text("/bin/a|1.0|2.0\n", encoding="utf-8")
    df, bad = read_csv_filter_convert(data, ["path", "creation_time", "access_time"], 2, "|")
    assert len(df) == 1
    assert bad == 0
