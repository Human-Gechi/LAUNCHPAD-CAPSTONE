# Built-in
import os
from io import BytesIO
from pathlib import Path

# Third-party
import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv
import botocore.exceptions

# Local modules
from log import ingest_logger
from .utility import time_stamp, parquet_path

load_dotenv()


DST_PROFILE = "dev-Supply-Chain"
DST_BUCKET = os.getenv("DESTINATI0N_BUCKET")

def object_metadata(source: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds metadata to dataframe.

    Args:
        source(str): Data source
        df(pd.DataFrame) : Pandas DataFrame
    
    Returns:
        DataFrame
    """
    df = df.copy()
    df["ingested_at"] = time_stamp()
    df["source"] = source
    ingest_logger
    return df

def get_dest_s3_client():
    """
    Get for s3 client for destination AWS account.  

    Raises:
        botocore.exceptions.ProfileNotFound: If invalid profile name 
    """
    try:
        session = boto3.Session(profile_name=DST_PROFILE)
        ingest_logger.info("✅ Session created successfully")
        return session.client("s3")
    except botocore.exceptions.ProfileNotFound:
        ingest_logger.error("❌ Destniation profile not found")

def write_parquet(df: pd.DataFrame, source: str, filename: str) -> str:
    """
    Converts a pandas DataFrame to Parquet format and uploads it to the destination S3 raw bucket.

    Args:
        df (pd.DataFrame): The DataFrame to be converted and uploaded.
        source (str): The name of the data source (used for metadata and S3 key).
        filename (str): The base name for the Parquet file in S3.

    Returns:
        str: The S3 key where the Parquet file was uploaded.

    Raises:
        botocore.exceptions.ClientError: If there is an error uploading to S3.
        botocore.exceptions.EndpointConnectionError: If there is a network issue connecting to S3.
    """
    # object meta data
    df = object_metadata(source, df)

    # Convert to parquet in memory
    buffer = BytesIO()

    #Convert DataFrame to Pyarrow table
    table = pa.Table.from_pandas(df)

    #Write table to parquet format
    pq.write_table(table, buffer)

    # Move cursor to start of program
    buffer.seek(0)

    # Build S3 source
    s3_key = parquet_path(source, filename)

    # Upload to your S3 bucket
    try:
        s3_client = get_dest_s3_client()
        s3_client.put_object(
            Bucket=DST_BUCKET,
            Key=s3_key,
            Body=buffer.getvalue()
        )
    except botocore.exceptions.ClientError as e:
        ingest_logger.error(f"❌An error occured {e}")
    except botocore.exceptions.EndpointConnectionError as e:
        ingest_logger.error(f"❌Check your network and try again later")