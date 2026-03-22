import json
import os
import sys
from io import StringIO

import boto3
import botocore.exceptions
import pandas as pd
from dotenv import load_dotenv

from ingestion.write import write_parquet
from log import ingest_logger

# Load environment variables
load_dotenv()

# Get credentials from env. file
SRC_ACCESS_KEY = os.getenv("SRC_ACCESS_KEY")
SRC_SECRET_KEY = os.getenv("SRC_SECRET_KEY")
SRC_BUCKET = os.getenv("SRC_BUCKET")
SRC_REGION = os.getenv("SRC_REGION")

DST_ACCESS_KEY = os.getenv("DST_ACCESS_KEY")
DST_SECRET_KEY = os.getenv("DST_SECRET_KEY")
DST_BUCKET = os.getenv("DST_BUCKET")
DST_REGION = os.getenv("DST_REGION")
OBJECT_KEY = os.getenv("OBJECT_KEY")


# S3 client
class S3ClientFactory:
    @staticmethod
    def create_client(access_key, secret_key, region):
        return boto3.client("s3", aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)


src_client = S3ClientFactory.create_client(SRC_ACCESS_KEY, SRC_SECRET_KEY, SRC_REGION)
dst_client = S3ClientFactory.create_client(DST_ACCESS_KEY, DST_SECRET_KEY, DST_REGION)

# s3 folders
folders = {"inventory": "csv", "products": "csv", "suppliers": "csv", "warehouses": "csv", "shipments": "json"}


# Ingestion class
class MoveData:
    def __init__(self, src_client, dst_client, src_bucket, dst_bucket):
        self.src_client = src_client
        self.dst_client = dst_client
        self.src_bucket = src_bucket
        self.dst_bucket = dst_bucket

    def validate_folders(self, source):
        global folders
        resp = self.dst_client.list_objects_v2(Bucket=self.dst_bucket, Prefix=f"{source}/")
        found_folders = set()
        if "Contents" in resp:
            for obj in resp["Contents"]:
                key = obj["Key"]
                for folder in folders.keys():
                    if key.startswith(f"{source}/{folder}/"):
                        found_folders.add(folder)
        for folder in folders:
            if folder in found_folders:
                ingest_logger.info(f"✅ Folder '{folder}' exists in {self.dst_bucket}")
            else:
                ingest_logger.error(f"❌ Folder '{folder}' NOT found in {self.dst_bucket}")
        return found_folders

    def exists_by_basename(self, prefix: str, base: str) -> bool:
        paginator = self.dst_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.dst_bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.startswith(f"{prefix}/{base}_") and key.endswith(".parquet"):
                    ingest_logger.info(f"✅ Found matching file: {key}")
                    return True
        ingest_logger.info(f"❌ No file found for base {base} under {prefix}")
        return False

    def read_json_file(self, s3_key):
        try:
            resp = self.src_client.get_object(Bucket=self.src_bucket, Key=s3_key)
            content = resp["Body"].read().decode("utf-8")
            json_data = json.loads(content)
            ingest_logger.info(f"....Reading JSON file from s3://{self.src_bucket}/{s3_key}")
            if isinstance(json_data, list):
                return pd.DataFrame(json_data)
            else:
                return pd.DataFrame([json_data])
        except botocore.exceptions.EndpointConnectionError:
            ingest_logger.error("❌ Check your network and try again later")
            sys.exit(1)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                ingest_logger.error(f"❌ {self.src_bucket} not found! Verify your bucket name")

    def read_csv_file(self, s3_key):
        try:
            ingest_logger.info(f"Reading CSV file from s3://{self.src_bucket}/{s3_key}")
            resp = self.src_client.get_object(Bucket=self.src_bucket, Key=s3_key)
            contents = resp["Body"].read().decode("utf-8")
            return pd.read_csv(StringIO(contents))
        except botocore.exceptions.EndpointConnectionError:
            ingest_logger.error("❌ Check your network and try again later")
            sys.exit(1)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                ingest_logger.error(f"{self.src_bucket} not found! Verify your bucket name")

    def process_json_files(self, prefix: str):
        resp = self.src_client.list_objects_v2(Bucket=self.src_bucket, Prefix=prefix)
        dfs = []
        if "Contents" in resp:
            for obj in resp["Contents"]:
                key = obj["Key"]
                if key.startswith(prefix) and key.endswith(".json"):
                    df = self.read_json_file(key)
                    filename = key.split("/")[-1]
                    if df is not None:
                        ingest_logger.info(f"Processed JSON file: {key}")
                        dfs.append((df, filename))
        return dfs

    def process_csv_files(self, prefix: str):
        resp = self.src_client.list_objects_v2(Bucket=self.src_bucket, Prefix=prefix)
        dfs = []
        if "Contents" in resp:
            for obj in resp["Contents"]:
                key = obj["Key"]
                if key.startswith(prefix) and key.endswith(".csv"):
                    df = self.read_csv_file(key)
                    filename = key.split("/")[-1]
                    if df is not None:
                        ingest_logger.info(f"✅ Processed CSV file: {key}")
                        dfs.append((df, filename))
        return dfs

    def ingest_files(self, source: str):
        global folders
        try:
            for folder, filetype in folders.items():
                prefix = f"{source}/{folder}"

                if filetype == "csv":
                    csv_files = self.process_csv_files(prefix)
                    for df, filename in csv_files:
                        base = os.path.splitext(filename)[0]
                        if not self.exists_by_basename(prefix, base):
                            write_parquet(df, source, base, folder)
                            ingest_logger.info(f"✅ {prefix}/{base} written to s3")
                        else:
                            ingest_logger.info(f"⏩ Skipped {prefix}/{base} (file with base file '{base}' exists)")

                elif filetype == "json":
                    json_files = self.process_json_files(prefix)
                    for df, filename in json_files:
                        base = os.path.splitext(filename)[0]
                        if not self.exists_by_basename(prefix, base):
                            write_parquet(df, source, base, folder)
                            ingest_logger.info(f"✅ {prefix}/{base} written to s3")
                        else:
                            ingest_logger.info(f"⏩ Skipped {prefix}/{base} (file with base file '{base}' exists)")
        except Exception as e:
            ingest_logger.error(f"❌ Error during ingestion: {e}")


if __name__ == "__main__":
    mover = MoveData(src_client, dst_client, SRC_BUCKET, DST_BUCKET)
    mover.ingest_files("raw")
