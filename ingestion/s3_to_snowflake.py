import io
import os
import time

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

from ingestion.s3_to_s3 import S3ClientFactory
from log import ingest_logger

dst_client = S3ClientFactory.create_client("DST")
base = "raw/"

pq_to_sf_type = {
    "Int64": "NUMBER",
    "int64": "NUMBER",
    "Float64": "FLOAT",
    "float64": "FLOAT",
    "str": "VARCHAR",
    "object": "VARCHAR",
    "bool": "BOOLEAN",
    "datetime64[us]": "VARCHAR",
    "datetime64[ns]": "VARCHAR",
}


class SnowFlake:
    def __init__(self, dst_client, dst_bucket):
        self.user = os.getenv("SF_USER")
        self.password = os.getenv("SF_PASSWORD")
        self.account = os.getenv("SF_ACCOUNT")
        self.warehouse = os.getenv("SF_WH")
        self.database = os.getenv("SF_DB")
        self.schema = os.getenv("SF_SCHEMA")
        self.role = os.getenv("SF_ROLE")
        self.dst_client = dst_client
        self.dst_bucket = dst_bucket

    def conn_sf(self):
        """
        Establishes a connection to Snowflake Warehouse with credentials
        loaded from environment variables.

        Returns:
            conn: A connection object to the snowflake data warehouse
        """
        conn = snowflake.connector.connect(
            user=self.user,
            password=self.password,
            account=self.account,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema,
            role=self.role,
        )
        ingest_logger.info("✅ Connection to Snowflake obtained")
        return conn

    def parquet_dtypes_to_snowflake(self, pq_dtype):
        """
        Maps parquet files data type to snowflake built in data types

        Returns:
            Values specifying data type in snowflake
        """
        return pq_to_sf_type.get(pq_dtype)

    def table_exists(self, cur, table_name):
        """
        Checks for the existence of tables

        Returns:
            The count of values in the tables
        """
        cur.execute(
            f"""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{self.schema}'
            AND TABLE_NAME = '{table_name}'
        """
        )
        return cur.fetchone()[0] > 0

    def get_directories(self):
        """
        Return a set of unique directories under the given prefix.

        For instance:
            directories = raw/inventory, raw/products ........
            base_directory = raw (base)

        Returns:
            directories: Strings splitted at /
            directories : inventory, products
        """
        files = self.dst_client.list_objects_v2(Bucket=self.dst_bucket, Prefix=base)
        directories = set()
        for obj in files.get("Contents", []):
            key = obj["Key"]
            parts = key.split("/")
            if len(parts) > 1 and parts[1]:
                directories.add(parts[1])
        return directories

    def get_parquet_files_in_dir(self, directory):
        files = self.dst_client.list_objects_v2(
            Bucket=self.dst_bucket, Prefix=f"{base}{directory}/"
        )
        parquet_files = []
        for obj in files.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".parquet"):
                etag = obj["ETag"].strip('"')
                last_modified = obj["LastModified"]
                parquet_files.append({"key": key, "etag": etag, "last_modified": last_modified})
        return parquet_files

    def create_processed_files_table(self, conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS PROCESSED_FILES (
                    FILE_KEY VARCHAR(1024),
                    ETAG VARCHAR(64),
                    LAST_MODIFIED TIMESTAMP_NTZ,
                    PROCESSED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    PRIMARY KEY (FILE_KEY, ETAG)
                );
            """
            )

    def is_file_processed(self, cur, file_key, etag):
        cur.execute(
            "SELECT 1 FROM PROCESSED_FILES WHERE FILE_KEY = %s AND ETAG = %s",
            (
                file_key,
                etag,
            ),
        )
        return cur.fetchone() is not None

    def mark_file_processed(self, cur, file_key, etag, lastmodified):
        cur.execute(
            "INSERT INTO PROCESSED_FILES (FILE_KEY, ETAG, LAST_MODIFIED) VALUES (%s, %s, %s)",
            (file_key, etag, lastmodified),
        )

    def get_df(self, key):
        obj = self.dst_client.get_object(Bucket=self.dst_bucket, Key=key)
        data = obj["Body"].read()
        df = pd.read_parquet(io.BytesIO(data))
        df.columns = [c.upper() for c in df.columns]
        return df

    def get_columns_sql(self, df):
        columns = []
        for col, dtype in zip(df.columns, df.dtypes):
            sf_type = self.parquet_dtypes_to_snowflake(dtype.name)
            columns.append(f"{col} {sf_type}")
        return ", ".join(columns)

    def create_table(self, cur, table, columns_sql):
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table} ({columns_sql}, 
            ingestion_date TIMESTAMP_NTZ DEFAULT 
            CONVERT_TIMEZONE(\'Africa/Lagos\', CURRENT_TIMESTAMP())::TIMESTAMP_NTZ);
        """
        if not self.table_exists(cur, table):
            ingest_logger.info(f"Creating new table {table}")
            cur.execute(create_sql)

    def create_staging_table(self, cur, table, columns_sql):
        staging_table = f"{table}_STAGING"
        cur.execute(f"CREATE OR REPLACE TABLE {staging_table} ({columns_sql});")
        ingest_logger.info(f"Staging table {staging_table} created")
        return staging_table

    def upsert_batches(self, conn, cur, df, table, staging_table, batch_size, key):
        for start in range(0, len(df), batch_size):
            end = start + batch_size
            batch_df = df.iloc[start:end].reset_index(drop=True)
            cur.execute(f"TRUNCATE TABLE {staging_table}")
            write_pandas(conn, batch_df, staging_table)
            merge_sql = f"""
                MERGE INTO {table} t
                USING {staging_table} s
                ON ({" AND ".join([f't."{col}" = s."{col}"' for col in df.columns])})
                WHEN NOT MATCHED THEN
                INSERT ({', '.join([f'"{col}"' for col in df.columns])})
                VALUES ({', '.join([f's."{col}"' for col in df.columns])});
            """
            cur.execute(merge_sql)
            if cur.rowcount is not None:
                count = cur.rowcount
            else:
                0
            ingest_logger.info(f"📌 Upserted {count} rows into {table} from file {key}")

    def process_file(self, conn, cur, file_info, table, staging_table, batch_size, max_retries):
        key = file_info["key"]
        etag = file_info["etag"]
        last_modified = file_info["last_modified"]

        if self.is_file_processed(cur, key, etag):
            ingest_logger.info(f"File {key} (ETag: {etag}) already processed, ⏩ skipping.....")
            return

        ingest_logger.info(f"Processing new/changed file: {key} (ETag: {etag})")
        file_attempt = 0
        while file_attempt < max_retries:
            try:
                obj = self.dst_client.get_object(Bucket=self.dst_bucket, Key=key)
                data = obj["Body"].read()
                df = pd.read_parquet(io.BytesIO(data))
                df = df.drop_duplicates()
                df.columns = [c.upper() for c in df.columns]

                self.upsert_batches(conn, cur, df, table, staging_table, batch_size, key)
                self.mark_file_processed(cur, key, etag, last_modified)
                ingest_logger.info(f"✅ File {key} (ETag: {etag}) processed and marked.")
                break
            except Exception as e:
                file_attempt += 1
                wait = 2 ** (file_attempt - 1)
                ingest_logger.error(
                    f"Error processing file {key} (attempt {file_attempt}/{max_retries}): {e}"
                )
                if file_attempt < max_retries:
                    ingest_logger.info(f"Retrying in {wait} seconds...")
                    time.sleep(wait)
                else:
                    ingest_logger.error(
                        f"Failed to process file {key} after {max_retries} attempts. Skipping."
                    )

    def process_directory(self, conn, cur, directory, batch_size, max_retries):
        table = directory.upper()
        ingest_logger.info(f"🔄️ Processing directory: {directory} -> table: {table}")
        parquet_files = self.get_parquet_files_in_dir(directory)
        if not parquet_files:
            ingest_logger.info(f"No parquet files found in {directory}, ⏩ Skipping.....")
            return

        df = self.get_df(parquet_files[0]["key"])
        columns_sql = self.get_columns_sql(df)
        self.create_table(cur, table, columns_sql)
        staging_table = self.create_staging_table(cur, table, columns_sql)

        for file_info in parquet_files:
            self.process_file(conn, cur, file_info, table, staging_table, batch_size, max_retries)

        cur.execute(f"DROP TABLE IF EXISTS {staging_table}")
        ingest_logger.info(f"✅ Staging table {staging_table} dropped")

    def create_tables_from_directories(self):
        max_retries = 5
        batch_size = 50000
        attempt = 1
        directories = self.get_directories()

        while attempt <= max_retries:
            try:
                with self.conn_sf() as conn:
                    with conn.cursor() as cur:
                        self.create_processed_files_table(conn)
                        for directory in directories:
                            self.process_directory(conn, cur, directory, batch_size, max_retries)
                    break
            except Exception as e:
                ingest_logger.error(
                    f"Error in main pipeline (attempt {attempt}/{max_retries}): {e}"
                )
                if attempt < max_retries:
                    wait = 2 ** (attempt - 1)
                    ingest_logger.info(f"Retrying main pipeline in {wait} seconds...")
                    time.sleep(wait)
                    attempt += 1
                else:
                    ingest_logger.error(
                        f"Failed to complete pipeline after {max_retries} attempts."
                    )
                    break
