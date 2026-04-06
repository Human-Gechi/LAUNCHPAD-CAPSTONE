# Built-in
import os
from io import BytesIO

# Third-party
import boto3
import botocore.exceptions
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ingestion.utility import get_aws_dst_params, parquet_path, time_stamp
from logs.log import get_ingest_logger

ingest_logger = get_ingest_logger()


def object_metadata(data_source: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds metadata to dataframe.

    Args:
        source(str): Data source
        df(pd.DataFrame) : Pandas DataFrame

    Returns:
        DataFrame
    """
    df = df.copy()
    df[f"{data_source}_extraction_date"] = time_stamp()
    df["origin"] = data_source
    ingest_logger.info("✅ Metadata added successfully")
    return df


def get_dest_s3_client(conn_id="aws_dst"):
    """
    Get for s3 client for destination AWS account.

    Args:
        conn_id
    Returns:
            str: The S3 key where the Parquet file was uploaded.

    Raises:
        botocore.exceptions.NoCredentialsError: If credentials are invalid
    """
    try:
        aws_params = get_aws_dst_params(conn_id)
        return boto3.client(
            "s3",
            aws_access_key_id=aws_params["aws_access_key_id"],
            aws_secret_access_key=aws_params["aws_secret_access_key"],
            region_name=aws_params["region"],
        )
    except botocore.exceptions.NoCredentialsError:
        ingest_logger.error("❌ Destination Credentials invalid ")


def write_parquet(
    df: pd.DataFrame, data_source: str, folder: str, filename: str, conn_id="aws_dst"
) -> str:
    """
    Converts a pandas DataFrame to Parquet format and uploads it to the destination S3 raw bucket.

    Args:
        df (pd.DataFrame): The DataFrame to be converted and uploaded.
        data_source (str): The name of the data source (used for metadata and S3 key).
        folder(str): Folder path to files
        filename (str): The base name for the Parquet file in S3.
        conn_id: Airflow connection to amazon s3

    Returns:
        str: The S3 key where the Parquet file was uploaded.

    Raises:
        botocore.exceptions.ClientError: If there is an error uploading to S3.
        botocore.exceptions.EndpointConnectionError: If there is a network issue connecting to S3.
    """
    df = object_metadata(data_source, df)

    buffer = BytesIO()

    df.columns = df.columns.map(str)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, buffer)

    buffer.seek(0)

    s3_key = parquet_path(folder, filename)

    try:
        s3_client = get_dest_s3_client(conn_id)
        aws_params = get_aws_dst_params(conn_id)
        s3_client.put_object(Bucket=aws_params["bucket"], Key=s3_key, Body=buffer.getvalue())
        ingest_logger.info(f"✅Object {s3_key} sent ")
    except botocore.exceptions.ClientError as e:
        ingest_logger.error(f"❌An error occured {e}")
    except botocore.exceptions.EndpointConnectionError:
        ingest_logger.error("❌Check your network and try again later")
