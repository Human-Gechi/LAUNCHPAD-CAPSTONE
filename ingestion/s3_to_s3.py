import boto3
import os
import botocore.exceptions
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
import json
import sys

from log import ingest_logger
from utility import parquet_path

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


class MoveData:
    def __init__(self, src_client, dst_client, src_bucket, dst_bucket):
        self.src_client = src_client
        self.dst_client = dst_client
        self.src_bucket = src_bucket
        self.dst_bucket = dst_bucket
        ingest_logger.info("✅ SRC & DST Buckets initialization")

    def validate_folders(self, source):
        resp = self.dst_client.list_objects_v2(Bucket=self.dst_bucket, Prefix=f"{source}/")
        folders = ["inventory", "shipments", "products", "warehouses", "suppliers"]
        found_folders = set()
        if "Contents" in resp:
            for obj in resp["Contents"]:
                key = obj["Key"]
                for folder in folders:
                    if key.startswith(f"{source}/{folder}/"):
                        found_folders.add(folder)
                    return found_folders
        for folder in folders:
            if folder in found_folders:
                ingest_logger.info(f"✅ Folder '{folder}' exists in {self.dst_bucket}")
            else:
                ingest_logger.error(f"❌ Folder '{folder}' NOT found in {self.dst_bucket}")

    def exist(self, source:str, filename:str) -> bool:
        folders = self.validate_folders()
        resp=self.dst_client.list_objects_v2(Bucket=self.dst_bucket,Prefix=f"{source}/{folders}")
        try:
            if "Contents" not in resp:
                    return False
            keys = [key["Key"] for key in resp["Contents"]]
            if filename in keys:
                ingest_logger.info(f"Found existing {filename} with key {keys}")

                return True
            else:
                ingest_logger.error(f"{filename} not found")
            return False
        except botocore.exceptions.EndpointConnectionError as e:
            ingest_logger.error(f"❌Check your network and try again later")


    def read_json_files(self,src_key):
        try:
            resp = self.src_client.get_object(Bucket=self.src_bucket,Key=src_key)
            content = resp["Body"].read().decode("utf-8")
            json_data = json.loads(content)
            ingest_logger.info(f"Reading JSON file from s3://{self.src_bucket}/{src_key}")

            if isinstance(json_data, list):
                pd.DataFrame(json_data)
            else:
                pd.DataFrame([json_data])
            return pd.DataFrame
        except botocore.exceptions.EndpointConnectionError as e:
            ingest_logger.error(f"❌Check your network and try again later")
            sys.exit(1)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                ingest_logger.error(f"{self.src_bucket} not found! Verify your bucket name")

    def read_csv_files(self,src_key):
        try:
            ingest_logger.info(f"Reading CSV file(s) from s3://{self.src_bucket}/{src_key}")
            resp = self.src_client.get_object(Bucket=self.src_bucket,Key=src_key)
            contents = resp["Body"].read().decode("utf-8")
            for content in contents:
                return pd.read_csv(StringIO(content))
        except botocore.exceptions.EndpointConnectionError as e:
            ingest_logger.error(f"❌Check your network and try again later")
            sys.exit(1)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                ingest_logger.error(f"{self.src_bucket} not found! Verify your bucket name")

    def process_json_files(self, source: str):
        resp = self.src_client.list_objects_v2(Bucket=self.src_bucket, Prefix=f"{source}/")
        dfs = []
        if "Contents" in resp:
            for obj in resp["Contents"]:
                key = obj["Key"]
                if key.endswith(".json"):
                    df = self.read_json_files(key)
                    ingest_logger.info(f"Processed JSON file: {key}")
                    dfs.append(df)
        return dfs

    def process_csv_files(self,source:str):
        resp = self.src_client.list_objects_v2(Bucket=self.src_bucket, Prefix=f"{source}/")
        dfs = []
        if "Contents" in resp:
            for obj in resp["Contents"]:
                key = obj["Key"]
                if key.endswith(".csv"):
                    df = self.read_csv_files(key)
                    ingest_logger.info(f"Processed JSON file: {key}")
                    dfs.append(df)
        return dfs

    def ingest_csv_files(self):
        pass

#if __name__ == "__main__":
    #mover = MoveData(src_client, dst_client, SRC_BUCKET, DST_BUCKET)
    #mover.exist("raw", "inventory_2026-03-10.csv")
    #mover.process_json_files("raw")
    #mover.process_csv_files("raw")
    #mover.validate_folders("raw")
