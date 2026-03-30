import os

import boto3
import pandas as pd
import pytest
from moto import mock_aws

from ingestion.write import get_dest_s3_client, object_metadata, write_parquet


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    monkeypatch.setenv("DST_BUCKET", "test-bucket")
    monkeypatch.setenv("DST_REGION", "eu-south-1")
    monkeypatch.delenv("DST_PROFILE", raising=False)


def test_object_metadata():
    data_source = "test"
    df = pd.DataFrame({"quantity": [1, 2]})

    result = object_metadata(data_source, df)

    assert f"{data_source}_extraction_date" in result.columns
    assert "origin" in result.columns
    assert all(result["origin"] == data_source)
    assert result.shape[0] == df.shape[0]
    assert isinstance(result, pd.DataFrame)


@mock_aws
def test_get_dest_s3_client():
    client = get_dest_s3_client()
    assert hasattr(client, "put_object")
    assert callable(client.put_object)


@mock_aws
def test_write_parquet():
    s3 = boto3.client("s3", region_name=os.getenv("DST_REGION"))
    s3.create_bucket(
        Bucket=os.getenv("DST_BUCKET"),
        CreateBucketConfiguration={"LocationConstraint": os.getenv("DST_REGION")},
    )

    df = pd.DataFrame({"quantity": [1, 2], "price": [3, 4]})
    folder = "raw/inventory"
    filename = "inventory_2050_03_01"
    data_source = "test"

    write_parquet(df, data_source, folder, filename)

    response = s3.list_objects_v2(Bucket=os.getenv("DST_BUCKET"), Prefix=folder)
    assert response["KeyCount"] == 1
    assert response["Contents"][0]["Key"].startswith(f"{folder}/{filename}")
