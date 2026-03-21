import boto3
import sys
import os

from dotenv import load_dotenv

from log import ingest_logger
sys.path

load_dotenv()

import boto3

# Source bucket credentials
SRC_ACCESS_KEY = os.getenv("SOURCE_ACCESS_KEY")
SRC_SECRET_KEY = os.getenv("SOURCE_SECRET_KEY")
SRC_BUCKET = os.getenv("source-bucket-name")

# Destination bucket credentials
DST_ACCESS_KEY = os.getenv("DESTINATION_ACCESS_KEY")
DST_SECRET_KEY = os.getenv("DESTINATION_SECRET_KEY")
DST_BUCKET = os.getenv("destination-bucket-name")
OBJECT_KEY = os.getenv("your-object-key")

class MoveData():
    def __init__(self,source, destination):
        self.source = source
        self.destination = destination