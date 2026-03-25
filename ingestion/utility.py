# Built-in
from datetime import datetime


# Get Timestamp
def time_stamp() -> datetime:
    """
    Full timestamp for file uniqueness

    Returns:
        timestamp
    """
    return datetime.utcnow().strftime("%Y-%m-%d")


def full_timestamp() -> datetime:
    """
    Full UTC timestamp for file uniqueness

    Returns:
        timestamp
    """
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


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