import json
import os
import sys
import time
from io import StringIO

import boto3
import botocore.exceptions
import pandas as pd
from airflow.sdk import BaseHook

from ingestion.write import write_parquet
from logs.log import get_ingest_logger

ingest_logger = get_ingest_logger()


# S3 client
class S3ClientFactory:
    """
    Create a static boto3 S3 client using credentials and region from config for the given prefix.

    Args:
        prefix (str): The prefix for the config keys ('SRC' -> SOURCE or 'DST' -> DESTINATION).

    Returns:
        boto3.client: An S3 client configured with the credentials and region.
    """

    @staticmethod
    def create_client(conn_id):
        aws_conn = BaseHook.get_connection(conn_id)
        session = boto3.Session(
            aws_access_key_id=aws_conn.login,
            aws_secret_access_key=aws_conn.password,
            region_name=aws_conn.extra_dejson.get("region"),
        )
        return session.client("s3")


# Ingestion class
class MoveData:
    def __init__(self, src_client, dst_client, src_bucket, dst_bucket):
        """
        Initialize the MoveData class with source and destination S3 clients and bucket names.

        Args:
            src_client (boto3.client): Source S3 client.
            dst_client (boto3.client): Destination S3 client.
            src_bucket (str): Source S3 bucket name.
            dst_bucket (str): Destination S3 bucket name.
        """
        self.src_client = src_client
        self.dst_client = dst_client
        self.src_bucket = src_bucket
        self.dst_bucket = dst_bucket
        self.data_source = "s3"

    def validate_folders(self, source):
        """
        Validate folders and file types under a given S3 prefix.

        Args:
            source (str): The top-level prefix to search ('raw' folder).

        Returns:
            tuple: (folder names in a set, dynamic mapping folder to sets of file extensions)
        """
        folders = set()
        file_types = {}
        resp = self.src_client.list_objects_v2(Bucket=self.src_bucket, Prefix=f"{source}/")
        for obj in resp.get("Contents", []):
            key = obj["Key"]
            file_parts = key.split("/")
            if len(file_parts) > 1:
                folder = file_parts[1]
                folders.add(folder)
                filename = file_parts[-1]
                if "." in filename:
                    ext = filename.split(".")[-1]
                    file_types.setdefault(folder, set()).add(ext)

        return folders, file_types

    def exists_by_basename(self, prefix: str, base: str) -> bool:
        """
        Check if a file with the given base name(raw/inventory/inventory_2026_03_15.csv |
        inventory_2026_03_15) exists in the destination S3 bucket with the prefix.

        Args:
            prefix (str): The S3 prefix to search under.
            base (str): The base name of the file (without extension).

        Returns:
            bool: True if a matching file exists, False otherwise.
        """
        resp = self.dst_client.list_objects_v2(Bucket=self.dst_bucket, Prefix=prefix)
        if "Contents" in resp:
            for obj in resp["Contents"]:
                key = obj["Key"]
                dest_base = os.path.splitext(key.split("/")[-1])[0]
                if dest_base.startswith(base):
                    ingest_logger.info(f"✅ Found matching file: {key}")
                    return True
        ingest_logger.info(f"❌ No file found for base {base} under {prefix}")
        return False

    def read_json_file(self, s3_key):
        """
        Read a JSON file from the source S3 bucket and return it as a pandas DataFrame.

        Args:
            s3_key (str): The S3 key of the json file.

        Returns:
            pd.DataFrame

        Raises:
            botocore.exceptions.ClientError
            botocore.exceptions.EndpointConnectionError
        """
        try:
            resp = self.src_client.get_object(Bucket=self.src_bucket, Key=s3_key)
            content = resp["Body"].read().decode("utf-8")
            json_data = json.loads(content)
            ingest_logger.info(f"Reading JSON file from s3://{self.src_bucket}/{s3_key}")
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
        """
        Read a csv file from the source S3 bucket and return it as a pandas DataFrame.

        Args:
            s3_key (str): The S3 key of the csv file.

        Returns:
            pd.DataFrame

        Raises:
            botocore.exceptions.ClientError
            botocore.exceptions.EndpointConnectionError
        """
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

    def process_csv_files(self, prefix: str):
        """
        Process all csv files under the given the parent & child diectory in the source bucket.

        Args:
            prefix (str): The S3 prefix to search for csv files.

        Returns:
            list: List of tuples (DataFrame,filename) for each processed csv file.
        """
        resp = self.src_client.list_objects_v2(Bucket=self.src_bucket, Prefix=prefix)
        dfs = []
        if "Contents" in resp:
            for obj in resp["Contents"]:
                key = obj["Key"]
                if key.startswith(prefix) and key.endswith(".csv"):
                    base = os.path.splitext(key.split("/")[-1])[0]
                    if self.exists_by_basename(prefix, base):
                        ingest_logger.info(
                            f"⏩ Skipped reading {key} \
                        (already exists in dest bucket)"
                        )
                        continue
                    df = self.read_csv_file(key)
                    filename = key.split("/")[-1]
                    if df is not None:
                        ingest_logger.info(f"✅ Processed CSV file: {key}")
                        dfs.append((df, filename))
        return dfs

    def process_json_files(self, prefix: str):
        """
        Process all json files under the given prefix in the source S3 bucket.

        Args:
            prefix (str): The s3 prefix to search for json files.

        Returns:
            list: List of tuples (DataFrame, filename) for each processed json file.
        """
        resp = self.src_client.list_objects_v2(Bucket=self.src_bucket, Prefix=prefix)
        dfs = []
        if "Contents" in resp:
            for obj in resp["Contents"]:
                key = obj["Key"]
                if key.startswith(prefix) and key.endswith(".json"):
                    base = os.path.splitext(key.split("/")[-1])[0]
                    if self.exists_by_basename(prefix, base):
                        ingest_logger.info(
                            f"⏩ Skipped reading {key} \
                        (already exists in dest bucket)"
                        )
                        continue
                    df = self.read_json_file(key)
                    filename = key.split("/")[-1]
                    if df is not None:
                        ingest_logger.info(f"Processed JSON file: {key}")
                        dfs.append((df, filename))
        return dfs

    def ingest_files(self, source: str):
        """
        Ingest files from the source S3 bucket to the destination S3 bucket.
        Processes all folders and file types under the given source prefix i.e
        (everything under each child directory in the base directory "raw"),
        and writes them as parquet files to the destination.

        Args:
            source (str): The base directory to ingest files from ("raw").
        """
        max_retries = 5
        folders, file_types = self.validate_folders(source)
        for folder in folders:
            if not folder:
                continue
            file_ext = file_types.get(folder, set())
            prefix = f"{source}/{folder}"
            attempt = 1
            while attempt <= max_retries:
                try:
                    for file_type in file_ext:
                        if file_type == "csv":
                            csv_files = self.process_csv_files(prefix)
                            for df, filename in csv_files:
                                base = os.path.splitext(filename)[0]
                                write_parquet(df, self.data_source, prefix, base)
                                ingest_logger.info(
                                    f"✅ {prefix}/{base} written to s3 in attempt-{attempt}"
                                )
                        elif file_type == "json":
                            json_files = self.process_json_files(prefix)
                            for df, filename in json_files:
                                base = os.path.splitext(filename)[0]
                                write_parquet(df, self.data_source, prefix, base)
                                ingest_logger.info(
                                    f"✅ {prefix}/{base} written to s3 in attempt-{attempt}"
                                )
                    break
                except Exception as e:
                    ingest_logger.error(f"❌ Error during ingestion of {prefix}: {e}")
                    if attempt == max_retries:
                        ingest_logger.error(
                            f"❌ Max trials reached for {prefix}.Skipping insertion, try later"
                        )
                        break
                    backoff = 2 ** (attempt - 1)
                    ingest_logger.info(
                        f"Retrying {prefix} in {backoff} seconds (attempt {attempt}/{max_retries})."
                    )
                    time.sleep(backoff)
                    attempt += 1
