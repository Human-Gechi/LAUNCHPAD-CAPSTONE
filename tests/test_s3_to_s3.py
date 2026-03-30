import io
import json
import os

import pandas as pd
import pytest
from moto import mock_aws

from ingestion.s3_to_s3 import MoveData, S3ClientFactory

folders = ["inventory", "products"]


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    monkeypatch.setenv("DST_BUCKET", "test-bucket")
    monkeypatch.setenv("DST_REGION", "eu-south-1")
    monkeypatch.delenv("DST_PROFILE", raising=False)
    monkeypatch.setenv("DST_ACCESS_KEY", "fake-dst-access-key")
    monkeypatch.setenv("DST_SECRET_KEY", "fake-dst-secret-key")
    monkeypatch.setenv("SRC_BUCKET", "src-test-bucket")
    monkeypatch.setenv("SRC_REGION", "eu-south-1")
    monkeypatch.setenv("SRC_ACCESS_KEY", "fake-src-access-key")
    monkeypatch.setenv("SRC_SECRET_KEY", "fake-src-secret-key")


@mock_aws
def test_validate_folders():
    source = "raw"

    dst_client = S3ClientFactory.create_client("DST")
    dst_client.create_bucket(
        Bucket=os.getenv("DST_BUCKET"),
        CreateBucketConfiguration={"LocationConstraint": os.getenv("DST_REGION")},
    )

    for folder in folders:
        dst_client.put_object(
            Bucket=os.getenv("DST_BUCKET"),
            Key=f"{source}/{folder}/_2026_03_30.parquet",
            Body=b"test",
        )

    src_client = S3ClientFactory.create_client("SRC")
    mover = MoveData(src_client, dst_client, os.getenv("SRC_BUCKET"), os.getenv("DST_BUCKET"))

    found_folders = mover.validate_folders(source)
    assert found_folders == set(folders)


@mock_aws
def test_exist_by_basename():
    source = "raw"
    basename = ["inventory_2023_05_10", "products"]
    dst_client = S3ClientFactory.create_client("DST")
    dst_client.create_bucket(
        Bucket=os.getenv("DST_BUCKET"),
        CreateBucketConfiguration={"LocationConstraint": os.getenv("DST_REGION")},
    )

    for folder in folders:
        prefix = f"{source}/{folder}"
        dst_client.put_object(
            Bucket=os.getenv("DST_BUCKET"),
            Key=f"{prefix}/{basename}_.parquet",
            Body=b"test",
        )

    mover = MoveData(None, dst_client, os.getenv("SRC_BUCKET"), os.getenv("DST_BUCKET"))

    assert mover.exists_by_basename(prefix, basename)


@mock_aws
def test_read_json_file():
    src_client = S3ClientFactory.create_client("SRC")
    src_client.create_bucket(
        Bucket=os.getenv("SRC_BUCKET"),
        CreateBucketConfiguration={"LocationConstraint": os.getenv("SRC_REGION")},
    )

    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    key = "raw/inventory/test.json"
    src_client.put_object(
        Bucket=os.getenv("SRC_BUCKET"), Key=key, Body=json.dumps(data).encode("utf-8")
    )
    mover = MoveData(src_client, None, os.getenv("SRC_BUCKET"), os.getenv("DST_BUCKET"))

    df = mover.read_json_file(key)
    expected_df = pd.DataFrame(data)
    pd.testing.assert_frame_equal(df, expected_df)


@mock_aws
def test_read_csv_file():
    src_client = S3ClientFactory.create_client("SRC")
    src_client.create_bucket(
        Bucket=os.getenv("SRC_BUCKET"),
        CreateBucketConfiguration={"LocationConstraint": os.getenv("SRC_REGION")},
    )

    data = {"quantity": [1, 2, 3], "prices": [0, 1, 3]}

    key = "raw/inventory/test.csv"

    csv_buffer = io.StringIO()
    pd.DataFrame(data).to_csv(csv_buffer, index=False)
    src_client.put_object(
        Bucket=os.getenv("SRC_BUCKET"),
        Key=key,
        Body=csv_buffer.getvalue().encode("utf-8"),
    )
    mover = MoveData(src_client, None, os.getenv("SRC_BUCKET"), os.getenv("DST_BUCKET"))

    df = mover.read_csv_file(key)
    expected_df = pd.DataFrame(data)
    pd.testing.assert_frame_equal(df, expected_df)


@mock_aws
def test_process_json_files():
    src_client = S3ClientFactory.create_client("SRC")
    src_client.create_bucket(
        Bucket=os.getenv("SRC_BUCKET"),
        CreateBucketConfiguration={"LocationConstraint": os.getenv("SRC_REGION")},
    )

    data1 = [{"quantity": 1, "stock": 2}]
    data2 = [{"quantity": 3, "price": 4}]
    key1 = "raw/inventory/file1.json"
    key2 = "raw/inventory/file2.json"
    src_client.put_object(
        Bucket=os.getenv("SRC_BUCKET"), Key=key1, Body=json.dumps(data1).encode("utf-8")
    )
    src_client.put_object(
        Bucket=os.getenv("SRC_BUCKET"), Key=key2, Body=json.dumps(data2).encode("utf-8")
    )

    mover = MoveData(src_client, None, os.getenv("SRC_BUCKET"), os.getenv("DST_BUCKET"))

    dfs = mover.process_json_files("raw/inventory")
    filenames = [fname for _, fname in dfs]
    assert set(filenames) == {"file1.json", "file2.json"}

    dfs_dict = {fname: df for df, fname in dfs}
    pd.testing.assert_frame_equal(dfs_dict["file1.json"], pd.DataFrame(data1))
    pd.testing.assert_frame_equal(dfs_dict["file2.json"], pd.DataFrame(data2))


@mock_aws
def test_process_csv_files():
    src_client = S3ClientFactory.create_client("SRC")
    src_client.create_bucket(
        Bucket=os.getenv("SRC_BUCKET"),
        CreateBucketConfiguration={"LocationConstraint": os.getenv("SRC_REGION")},
    )

    data1 = {"quantity": [1, 2, 3, 4], "stock": [1, 2, 3, 4]}
    data2 = {"quantity": [1, 2, 3, 4], "stock": [1, 2, 3, 4]}
    key1 = "raw/inventory/file1.csv"
    key2 = "raw/inventory/file2.csv"

    csv_buffer = io.StringIO()
    pd.DataFrame(data1).to_csv(csv_buffer, index=False)
    src_client.put_object(
        Bucket=os.getenv("SRC_BUCKET"),
        Key=key1,
        Body=csv_buffer.getvalue().encode("utf-8"),
    )
    csv_buffer = io.StringIO()
    pd.DataFrame(data2).to_csv(csv_buffer, index=False)
    src_client.put_object(
        Bucket=os.getenv("SRC_BUCKET"),
        Key=key2,
        Body=csv_buffer.getvalue().encode("utf-8"),
    )
    mover = MoveData(src_client, None, os.getenv("SRC_BUCKET"), os.getenv("DST_BUCKET"))
    dfs = mover.process_csv_files("raw/inventory")
    filenames = [fname for _, fname in dfs]
    assert set(filenames) == {"file1.csv", "file2.csv"}

    dfs_dict = {fname: df for df, fname in dfs}
    pd.testing.assert_frame_equal(dfs_dict["file1.csv"], pd.DataFrame(data1))
    pd.testing.assert_frame_equal(dfs_dict["file2.csv"], pd.DataFrame(data2))
