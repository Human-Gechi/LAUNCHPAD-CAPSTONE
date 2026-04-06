import io
import json
import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from moto import mock_aws

from ingestion.s3_to_s3 import MoveData, S3ClientFactory

folders = ["inventory", "products"]
file_types = {}


@pytest.fixture
def mock_conn():
    mock_conn = MagicMock()
    mock_conn.login = "FAKE_ACCESS_KEY"
    mock_conn.password = "FAKE_SECRET_ACCESS_KEY"
    mock_conn.extra_dejson = {
        "src_region": "us-west-2",
        "dst_region": "us-west-2",
        "src_bucket": "test-bucket-src",
        "dst_bucket": "test-bucket-dst",
    }
    with patch("ingestion.s3_to_s3.BaseHook.get_connection", return_value=mock_conn):
        yield mock_conn


@mock_aws
def test_validate_folders(mock_conn):
    source = "raw"
    src_client = S3ClientFactory.create_client("aws-src")
    src_client.create_bucket(
        Bucket=mock_conn.extra_dejson["src_bucket"],
        CreateBucketConfiguration={"LocationConstraint": mock_conn.extra_dejson["src_region"]},
    )
    src_client.put_object(
        Bucket=mock_conn.extra_dejson["src_bucket"],
        Key="raw/inventory/file1.csv",
        Body=b"test",
    )
    src_client.put_object(
        Bucket=mock_conn.extra_dejson["src_bucket"],
        Key="raw/products/file2.json",
        Body=b"test",
    )

    mover = MoveData(
        src_client, None, mock_conn.extra_dejson["src_bucket"], mock_conn.extra_dejson["dst_bucket"]
    )
    found_folders, file_types = mover.validate_folders(source)
    assert found_folders == {"inventory", "products"}
    assert file_types == {"inventory": {"csv"}, "products": {"json"}}


@mock_aws
def test_exist_by_basename(mock_conn):
    source = "raw"
    basename = "inventory_2023_05_10", "products"
    dst_client = S3ClientFactory.create_client("aws_dst")
    dst_client.create_bucket(
        Bucket=mock_conn.extra_dejson["dst_bucket"],
        CreateBucketConfiguration={"LocationConstraint": mock_conn.extra_dejson["dst_region"]},
    )
    for folder in folders:
        for base in basename:
            prefix = f"{source}/{folder}"
            dst_client.put_object(
                Bucket=mock_conn.extra_dejson["dst_bucket"],
                Key=f"{prefix}/{base}.parquet",
                Body=b"test",
            )

    mover = MoveData(
        None, dst_client, mock_conn.extra_dejson["src_bucket"], mock_conn.extra_dejson["dst_bucket"]
    )
    assert mover.exists_by_basename(prefix, base)


@mock_aws
def test_read_json_file(mock_conn):
    src_client = S3ClientFactory.create_client("aws_dst")
    src_client.create_bucket(
        Bucket=mock_conn.extra_dejson["src_bucket"],
        CreateBucketConfiguration={"LocationConstraint": mock_conn.extra_dejson["src_region"]},
    )

    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    key = "raw/inventory/test.json"
    src_client.put_object(
        Bucket=mock_conn.extra_dejson["src_bucket"], Key=key, Body=json.dumps(data).encode("utf-8")
    )
    mover = MoveData(
        src_client, None, mock_conn.extra_dejson["src_bucket"], mock_conn.extra_dejson["dst_bucket"]
    )

    df = mover.read_json_file(key)
    expected_df = pd.DataFrame(data)
    pd.testing.assert_frame_equal(df, expected_df)


@mock_aws
def test_read_csv_file(mock_conn):
    src_client = S3ClientFactory.create_client("aws_src")
    src_client.create_bucket(
        Bucket=mock_conn.extra_dejson["src_bucket"],
        CreateBucketConfiguration={"LocationConstraint": mock_conn.extra_dejson["src_region"]},
    )

    data = {"quantity": [1, 2, 3], "prices": [0, 1, 3]}

    key = "raw/inventory/test.csv"

    csv_buffer = io.StringIO()
    pd.DataFrame(data).to_csv(csv_buffer, index=False)
    src_client.put_object(
        Bucket=mock_conn.extra_dejson["src_bucket"],
        Key=key,
        Body=csv_buffer.getvalue().encode("utf-8"),
    )
    mover = MoveData(
        src_client, None, mock_conn.extra_dejson["src_bucket"], mock_conn.extra_dejson["dst_bucket"]
    )

    df = mover.read_csv_file(key)
    expected_df = pd.DataFrame(data)
    pd.testing.assert_frame_equal(df, expected_df)


@mock_aws
def test_process_json_files(mock_conn):
    src_client = S3ClientFactory.create_client("aws_dst")
    dst_client = S3ClientFactory.create_client("aws_src")
    src_client.create_bucket(
        Bucket=mock_conn.extra_dejson["src_bucket"],
        CreateBucketConfiguration={"LocationConstraint": mock_conn.extra_dejson["dst_region"]},
    )
    dst_client.create_bucket(
        Bucket=mock_conn.extra_dejson["dst_bucket"],
        CreateBucketConfiguration={"LocationConstraint": mock_conn.extra_dejson["dst_region"]},
    )

    # Upload files to source
    src_client.put_object(
        Bucket=mock_conn.extra_dejson["src_bucket"], Key="raw/inventory/file1.json", Body=b"{}"
    )
    src_client.put_object(
        Bucket=mock_conn.extra_dejson["src_bucket"], Key="raw/inventory/file2.json", Body=b"{}"
    )

    dst_client.put_object(
        Bucket=mock_conn.extra_dejson["dst_bucket"], Key="raw/inventory/file2.parquet", Body=b"{}"
    )

    mover = MoveData(
        src_client,
        dst_client,
        mock_conn.extra_dejson["src_bucket"],
        mock_conn.extra_dejson["dst_bucket"],
    )
    dfs = mover.process_json_files("raw/inventory")
    filenames = [fname for _, fname in dfs]
    assert set(filenames) == {"file1.json"}


@mock_aws
def test_process_csv_files(mock_conn):
    src_client = S3ClientFactory.create_client("aws_src")
    dst_client = S3ClientFactory.create_client("aws_dst")
    src_client.create_bucket(
        Bucket=mock_conn.extra_dejson["src_bucket"],
        CreateBucketConfiguration={"LocationConstraint": mock_conn.extra_dejson["src_region"]},
    )
    dst_client.create_bucket(
        Bucket=mock_conn.extra_dejson["dst_bucket"],
        CreateBucketConfiguration={"LocationConstraint": mock_conn.extra_dejson["dst_region"]},
    )

    data1 = {"quantity": [1, 2, 3, 4], "stock": [1, 2, 3, 4]}
    data2 = {"quantity": [1, 2, 3, 4], "stock": [1, 2, 3, 4]}
    key1 = "raw/inventory/file1.csv"
    key2 = "raw/inventory/file2.csv"

    csv_buffer = io.StringIO()
    pd.DataFrame(data1).to_csv(csv_buffer, index=False)
    src_client.put_object(
        Bucket=mock_conn.extra_dejson["src_bucket"],
        Key=key1,
        Body=csv_buffer.getvalue().encode("utf-8"),
    )
    csv_buffer = io.StringIO()
    pd.DataFrame(data2).to_csv(csv_buffer, index=False)
    src_client.put_object(
        Bucket=mock_conn.extra_dejson["src_bucket"],
        Key=key2,
        Body=csv_buffer.getvalue().encode("utf-8"),
    )

    dst_client.put_object(
        Bucket=mock_conn.extra_dejson["dst_bucket"], Key="raw/inventory/file2.parquet", Body=b"{}"
    )

    mover = MoveData(
        src_client,
        dst_client,
        mock_conn.extra_dejson["src_bucket"],
        mock_conn.extra_dejson["dst_bucket"],
    )
    dfs = mover.process_csv_files("raw/inventory")
    filenames = [fname for _, fname in dfs]
    assert set(filenames) == {"file1.csv"}

    dfs_dict = {fname: df for df, fname in dfs}
    pd.testing.assert_frame_equal(dfs_dict["file1.csv"], pd.DataFrame(data1))
