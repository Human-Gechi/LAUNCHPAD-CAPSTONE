import os
from unittest.mock import MagicMock, patch

import boto3
import pandas as pd
import pytest
from moto import mock_aws

from ingestion.utility import get_aws_dst_params
from ingestion.write import get_dest_s3_client, object_metadata, write_parquet


def test_object_metadata():
    data_source = "test"
    df = pd.DataFrame({"quantity": [1, 2]})

    result = object_metadata(data_source, df)

    assert f"{data_source}_extraction_date" in result.columns
    assert "origin" in result.columns
    assert all(result["origin"] == data_source)
    assert result.shape[0] == df.shape[0]
    assert isinstance(result, pd.DataFrame)


@pytest.fixture
def get_aws_dst_params():
    mock_conn = MagicMock()
    mock_conn.login = "FAKE_KEY"
    mock_conn.password = "FAKE_SECRET"
    mock_conn.extra_dejson = {"region": "eu-north-1", "bucket": "test-bucket"}

    with patch("ingestion.utility.BaseHook.get_connection", return_value=mock_conn):
        yield mock_conn


@mock_aws
def test_get_dest_s3_client(get_aws_dst_params):
    client = get_dest_s3_client(conn_id="aws_dst")
    assert hasattr(client, "put_object")
    assert callable(client.put_object)


@mock_aws
def test_write_parquet(get_aws_dst_params):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=get_aws_dst_params.login,
        aws_secret_access_key=get_aws_dst_params.password,
        region_name=get_aws_dst_params.extra_dejson["region"],
    )
    s3.create_bucket(
        Bucket=get_aws_dst_params.extra_dejson["bucket"],
        CreateBucketConfiguration={"LocationConstraint": get_aws_dst_params.extra_dejson["region"]},
    )

    df = pd.DataFrame({"quantity": [1, 2], "price": [3, 4]})
    folder = "raw/inventory"
    filename = "inventory_2050_03_01"
    data_source = "test"

    write_parquet(df, data_source, folder, filename)

    response = s3.list_objects_v2(Bucket=get_aws_dst_params.extra_dejson["bucket"], Prefix=folder)
    assert response["KeyCount"] == 1
    assert response["Contents"][0]["Key"].startswith(f"{folder}/{filename}")
