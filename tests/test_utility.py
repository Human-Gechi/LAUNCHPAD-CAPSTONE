from ingestion.utility import full_timestamp, parquet_path, time_stamp


def test_time_stamp_format():
    ts = time_stamp()
    # "YYYY-MM-DD HH:MM:SS"
    assert len(ts) == 19
    assert ts[4] == "-" and ts[7] == "-" and ts[13] == ":"


def test_full_timestamp_format():
    ts = full_timestamp()
    # "YYYYMMDDTHHMMSSZ"
    assert len(ts) == 16
    assert ts[8] == "T" and ts[-1] == "Z"


def test_parquet_path():
    folder = "raw/inventory"
    filename = "testfile"
    path = parquet_path(folder, filename)
    assert path.startswith(folder + "/" + filename + "_")
    assert path.endswith(".parquet")
