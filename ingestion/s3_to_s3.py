import boto3
import sys

from dotenv import load_dotenv

from log import ingest_logger
sys.path

load_dotenv()


s3 = boto3.resource("s3")
for bucket in s3.buckets.all():
    print(bucket.name)
    ingest_logger.info("Buckets list")