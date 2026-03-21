import boto3
import os

from dotenv import load_dotenv

from log import ingest_logger

# Load environment variables
load_dotenv()

# S3 client
class S3ClientFactory:
    @staticmethod
    def create_client(access_key, secret_key, region):
        return boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

# Get credentials from env. file
SRC_ACCESS_KEY = os.getenv("SOURCE_ACCESS_KEY")
SRC_SECRET_KEY = os.getenv("SOURCE_SECRET_KEY")
SRC_BUCKET = os.getenv("SOURCE_BUCKET")
SRC_REGION = os.getenv("SOURCE_REGION")

DST_ACCESS_KEY = os.getenv("DESTINATION_ACCESS_KEY")
DST_SECRET_KEY = os.getenv("DESTINATION_SECRET_KEY")
DST_BUCKET = os.getenv("DESTINATIN_BUCKET")
DST_REGION = os.getenv("DESTINATION_REGION")
OBJECT_KEY = os.getenv("OBJECT_KEY")


src_client = S3ClientFactory.create_client(SRC_ACCESS_KEY, SRC_SECRET_KEY, SRC_REGION)
dst_client = S3ClientFactory.create_client(DST_ACCESS_KEY, DST_SECRET_KEY, DST_REGION)

class MoveData:
    def __init__(self, src_client, dst_client, src_bucket, dst_bucket):
        self.src_client = src_client
        self.dst_client = dst_client
        self.src_bucket = src_bucket
        self.dst_bucket = dst_bucket
        ingest_logger.info("✅ SRC & DST Buckets initialization")

    def copy_object(self, object_key):
        obj = self.src_client.get_object(Bucket=self.src_bucket, Key=object_key)
        ingest_logger.info("✅ SRC Bucket initialization")
