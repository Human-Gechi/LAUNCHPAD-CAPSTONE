# Built-in
from datetime import datetime


# Get Timestamp
def time_stamp():
    """
    Full timestamp for file uniqueness

    Returns:
        timestamp
    """
    return datetime.utcnow().strftime("%Y-%m-%d")


def full_timestamp():
    """
    Full UTC timestamp for file uniqueness

    Returns:
        timestamp
    """
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


# File path for files
def parquet_path(source: str, filename: str, folder: str) -> str:
    """
    File path for pparquet files

    Args:
        source (str): The name of the data source (used for metadata and S3 key).
        filename (str): The base name for the Parquet file in S3.
        folder(str): Folder which the object will be located

    Returns:
        path: object file path
    """
    ts = full_timestamp()
    path = f"{source}/{folder}/{filename}_{ts}.parquet"
    return path
