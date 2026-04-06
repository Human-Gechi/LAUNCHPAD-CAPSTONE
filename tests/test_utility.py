from unittest.mock import MagicMock, patch

from ingestion.utility import full_timestamp, get_aws_dst_params, parquet_path, time_stamp


def test_time_stamp_format():
    """Function to check if it retruns a timestamp"""
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


def test_get_aws_dst_params():
    mock_conn = MagicMock()
    mock_conn.login = "FAKE_KEY"
    mock_conn.password = "FAKE_SECRET"
    mock_conn.extra_dejson = {"region": "eu-north-1", "bucket": "test-bucket"}

    with patch("ingestion.utility.BaseHook.get_connection", return_value=mock_conn):
        params = get_aws_dst_params()
        assert params["aws_access_key_id"] == "FAKE_KEY"
        assert params["aws_secret_access_key"] == "FAKE_SECRET"
        assert params["region"] == "eu-north-1"
        assert params["bucket"] == "test-bucket"
