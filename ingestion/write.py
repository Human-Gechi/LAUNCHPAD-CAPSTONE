# Built-in
import os
from io import BytesIO

# Third-party
import boto3
import botocore.exceptions
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ingestion.config import get_config
from ingestion.utility import parquet_path, time_stamp
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


def get_dest_s3_client():
    """
    Get for s3 client for destination AWS account.

    Raises:
        botocore.exceptions.ProfileNotFound: If invalid profile name
    """
    try:
        # Session creation
        config = get_config()
        session = boto3.Session(
            profile_name=config["DST_PROFILE"], region_name=config["DST_REGION"]
        )
        ingest_logger.info("✅ Session created successfully")
        return session.client("s3")
    except botocore.exceptions.ProfileNotFound:
        ingest_logger.error("❌ Destination profile not found")


def write_parquet(df: pd.DataFrame, data_source: str, folder: str, filename: str) -> str:
    """
    Converts a pandas DataFrame to Parquet format and uploads it to the destination S3 raw bucket.

    Args:
        df (pd.DataFrame): The DataFrame to be converted and uploaded.
        data_source (str): The name of the data source (used for metadata and S3 key).
        folder(str): Folder path to files
        filename (str): The base name for the Parquet file in S3.

    Returns:
        str: The S3 key where the Parquet file was uploaded.

    Raises:
        botocore.exceptions.ClientError: If there is an error uploading to S3.
        botocore.exceptions.EndpointConnectionError: If there is a network issue connecting to S3.
    """
    config = get_config()
    # object meta data
    df = object_metadata(data_source, df)

    # Convert to parquet in memory
    buffer = BytesIO()

    # Convert DataFrame to Pyarrow table
    df.columns = df.columns.map(str)
    table = pa.Table.from_pandas(df)

    # Write table to parquet format
    pq.write_table(table, buffer)

    # Move cursor to start of program
    buffer.seek(0)

    # Build S3 source
    s3_key = parquet_path(folder, filename)

    # Upload to your S3 bucket
    try:
        s3_client = get_dest_s3_client()
        s3_client.put_object(Bucket=config["DST_BUCKET"], Key=s3_key, Body=buffer.getvalue())
        ingest_logger.info(f"✅Object {s3_key} sent ")
    except botocore.exceptions.ClientError as e:
        ingest_logger.error(f"❌An error occured {e}")
    except botocore.exceptions.EndpointConnectionError:
        ingest_logger.error("❌Check your network and try again later")


