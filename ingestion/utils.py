from datetime import datetime
from pathlib import Path
from log import ingest_logger

# Get Timestamp
def _time_stamp():
    """Timestamp Function"""
    return datetime.now().strftime("%Y-%m-%d")

#File path for files
def file_path(path: str, extension: str):
    """ "Function to convert files to parquet"""
    time = _time_stamp()
    filename = f"{path}_{time}.{extension}"
    ingest_logger.info(f"✅ Parquet file {filename} created")
    return Path(filename)