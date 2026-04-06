# Built-in
from datetime import datetime

from airflow.sdk import BaseHook


def get_aws_dst_params(conn_id="aws_dst"):
    """
    AWS connection where destination s3 buckets live
    """
    conn = BaseHook.get_connection(conn_id)
    return {
        "aws_access_key_id": conn.login,
        "aws_secret_access_key": conn.password,
        "region": conn.extra_dejson.get("region"),
        "bucket": conn.extra_dejson.get("bucket"),
    }


def time_stamp() -> datetime:
    """
    Full timestamp for file metadata

    Returns:
        timestamp
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def full_timestamp() -> datetime:
    """
    Full local (GMT+1) timestamp for file uniqueness

    Returns:
        timestamp
    """
    return datetime.now().strftime("%Y%m%dT%H%M%SZ")


# File path for files
def parquet_path(folder: str, filename: str) -> str:
    """
    File path for parquet files

    Args:
        folder (str): Folder which the object will be located (e.g., 'raw/inventory')
        filename (str): The base name for the Parquet file in S3.

    Returns:
        path: object file path
    """
    ts = full_timestamp()
    path = f"{folder}/{filename}_{ts}.parquet"
    return path
