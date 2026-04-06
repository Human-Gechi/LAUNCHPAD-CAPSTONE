import io
import time

import pandas as pd
import snowflake.connector
from airflow.sdk import BaseHook
from snowflake.connector.pandas_tools import write_pandas

from logs.log import get_ingest_logger

ingest_logger = get_ingest_logger()

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
    """
    Handles the transfer of data from s3 objects (parquet files) to Snowflake tables.
    Provides methods for connecting to Snowflake, checking and creating tables,
    processing files, and tracking processed files.
    """

    def __init__(self, dst_client, dst_bucket, conn_id="snowflake_conn"):
        """
        Initialize with destination s3 client and bucket, and Airflow Snowflake connection ID.

        Args:
            dst_client (boto3.client): Destination S3 client.
            dst_bucket (str): Destination S3 bucket name.
            conn_id (str): Airflow connection ID for Snowflake.
        """
        self.dst_client = dst_client
        self.dst_bucket = dst_bucket
        self.conn_id = conn_id

        # Fetch credentials from Airflow Connection
        sf_conn = BaseHook.get_connection(self.conn_id)
        self.user = sf_conn.login
        self.password = sf_conn.password
        self.account = sf_conn.extra_dejson.get("account")
        self.warehouse = sf_conn.extra_dejson.get("warehouse")
        self.database = sf_conn.extra_dejson.get("database")
        self.schema = sf_conn.schema
        self.role = sf_conn.extra_dejson.get("role")

    def conn_sf(self):
        """
        Establishes a connection to Snowflake Warehouse with credentials from Airflow Connection.

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

    def parquet_dtypes_to_snowflake(self, pq_dtype: str):
        """
        Maps parquet files data type to snowflake built in data types

        Returns:
            Values specifying data type in snowflake
        """
        return pq_to_sf_type.get(pq_dtype)

    def table_exists(self, cur, table_name: str):
        """
        Checks for the existence of tables

        Returns:
            The count of values in the tables. If >0 => table exists and has contents
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
            directories = raw/inventory, raw/products, etc ........
            base_directory = raw (base)

        Returns:
            directories: Strings splitted at (/)
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

    def get_parquet_files_in_dir(self, directory: str):
        """
        Return a set of unique files under a particular directory

        Args:
            directory:  Unique directories

        Returns:
            directories: Strings splitted at (/)
            directories : inventory, products
        """
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
        """
        Create a table in Snowflake to record processed files and for idempotency.

        Args:
            conn: Snowflake connection.
        """
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.database}.{self.schema}.PROCESSED_FILES (
                    FILE_KEY VARCHAR(1024),
                    ETAG VARCHAR(64),
                    LAST_MODIFIED TIMESTAMP_NTZ,
                    PROCESSED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    PRIMARY KEY (FILE_KEY, ETAG)
                );
            """
            )

    def is_file_processed(self, cur, file_key: str, etag: str) -> bool:
        """
        Checks if a file has been processed

        Args:
            cur (snowflake.connector.cursor.SnowflakeCursor): Active Snowflake cursor.
            file_key (str): S3 key of the file.
            etag (str): ETag of the file.

        """
        cur.execute(
            "SELECT 1 FROM PROCESSED_FILES WHERE FILE_KEY = %s AND ETAG = %s",
            (
                file_key,
                etag,
            ),
        )
        return cur.fetchone() is not None

    def mark_file_processed(self, cur, file_key: str, etag: str, lastmodified):
        """
        Mark a file as processed by inserting its key, etag,
        and last modified timestamp into the tracking table.

        Args:
            cur (snowflake.connector.cursor.SnowflakeCursor): Snowflake cursor.
            file_key (str): s3 key of the file.
            etag (str): ETag of the file in s3
            lastmodified (datetime): Last modified timestamp of the file.
        """
        cur.execute(
            f"""INSERT INTO {self.database}.{self.schema}.PROCESSED_FILES 
            (FILE_KEY, ETAG, LAST_MODIFIED) VALUES (%s, %s, %s)""",
            (file_key, etag, lastmodified),
        )

    def get_df(self, key: str):
        """
        Retrieves a parquet file from S3 and load it into a pandas DataFrame.

        Args:
            key (str): key of the parquet file.

        Returns:
            pd.DataFrame
        """
        obj = self.dst_client.get_object(Bucket=self.dst_bucket, Key=key)
        data = obj["Body"].read()
        df = pd.read_parquet(io.BytesIO(data))
        df.columns = [c.upper() for c in df.columns]
        return df

    def get_columns_sql(self, df):
        """
        Generate a string for column definitions based on a DataFrame's columns
        and dtypes used to create tables

        Args:
            df (pd.DataFrame): DataFrame the clumns and dtypes are extracted

        Returns:
            str: SQL string for column definitions.
        """
        columns = []
        for col, dtype in zip(df.columns, df.dtypes):
            sf_type = self.parquet_dtypes_to_snowflake(dtype.name)
            columns.append(f"{col} {sf_type}")
        return ", ".join(columns)  # join each column and its dtype

    def create_table(self, cur, table: str, columns_sql: str):
        """
        Create a table in Snowflake if it does not already exist.

        Args:
            cur (snowflake.connector.cursor.SnowflakeCursor): Active Snowflake cursor.
            table (str): Table name.
            columns_sql (str): SQL string of column definitions.
        """
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.database}.{self.schema}.{table} ({columns_sql},
            ingestion_date TIMESTAMP_NTZ DEFAULT
            CONVERT_TIMEZONE(\'Africa/Lagos\', CURRENT_TIMESTAMP())::TIMESTAMP_NTZ);
        """
        if not self.table_exists(cur, table):
            ingest_logger.info(f"Creating new table {table}")
            cur.execute(create_sql)

    def create_staging_table(self, cur, table: str, columns_sql: str) -> str:
        """
        Create or replace a staging table in Snowflake for batch upserts(using MERGE INTO)

        Args:
            cur (snowflake.connector.cursor.SnowflakeCursor): Active Snowflake cursor.
            table (str): Table name.
            columns_sql (str): SQL string for defining columns

        Returns:
            str: The name of the staging table created.
        """
        staging_table = f"{table}_STAGING"
        cur.execute(
            f"""CREATE OR REPLACE TABLE {self.database}.{self.schema}.{staging_table} 
            ({columns_sql});"""
        )
        ingest_logger.info(f"Staging table {staging_table} created")
        return staging_table

    def upsert_batches(
        self, conn, cur, df: pd.DataFrame, table: str, staging_table: str, batch_size: str, key: str
    ) -> str:
        """
        Upsert data from a DataFrame into a Snowflake table in batches using a staging table.

        Args:
            conn : Snowflake connection.
            cur (snowflake.connector.cursor.SnowflakeCursor): Active Snowflake cursor.
            df (pd.DataFrame): DataFrame to upsert.
            table (str): Target table name.
            staging_table (str): Staging table name.
            batch_size (int): Number of rows per batch.
            key (str): s3 key of source object
        """
        for start in range(0, len(df), batch_size):
            end = start + batch_size
            batch_df = df.iloc[start:end].reset_index(drop=True)
            cur.execute(f"TRUNCATE TABLE {self.database}.{self.schema}.{staging_table}")
            write_pandas(conn, batch_df, staging_table)
            merge_sql = f"""
                MERGE INTO {self.database}.{self.schema}.{table} t
                USING {self.database}.{self.schema}.{staging_table} s
                ON ({" AND ".join([f't."{col}" = s."{col}"' for col in df.columns])})
                WHEN NOT MATCHED THEN
                INSERT ({", ".join([f'"{col}"' for col in df.columns])})
                VALUES ({", ".join([f's."{col}"' for col in df.columns])});
            """
            cur.execute(merge_sql)
            if cur.rowcount is not None:
                count = cur.rowcount
            else:
                0
            ingest_logger.info(f"📌 Upserted {count} rows into {table} from file {key}")

    def process_file(
        self,
        conn,
        cur,
        file_info: dict,
        table: str,
        staging_table: str,
        batch_size: int,
        max_retries: str,
    ):
        """
        Process a single parquet file from a directory:
        download, deduplicate, upsert to Snowflake, and mark as processed.

        Args:
            conn:  Snowflake connection.
            cur: Active Snowflake cursor.
            file_info (dict): Dict with keys 'key', 'etag', 'last_modified' for the file.
            table (str): Table name.
            staging_table (str): Staging table name.
            batch_size (int): Number of rows per batch.
            max_retries (int): Maximum number of retries for processing the file in a run.
        """
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

    def process_directory(self, conn, cur, directory: str, batch_size: int, max_retries: int):
        """
        Process all parquet files in a directory:
        create tables, upsert data, and clean up staging tables.

        Args:
            conn (snowflake.connector.connection.SnowflakeConnection): Snowflake connection.
            cur: Active Snowflake cursor.
            directory (str): Directory to process.
            batch_size (int): Number of rows per batch.
            max_retries (int): Maximum number of retries for processing files.
        """
        table = directory.upper()  # Snowflake is case sensitive
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

        cur.execute(f"DROP TABLE IF EXISTS {self.database}.{self.schema}.{staging_table}")
        ingest_logger.info(f"✅ Staging table {staging_table} dropped")

    def create_tables_from_directories(self):
        """
        Main pipeline to process all directories: create tables, process files, and handle retries"

        Retries the data pipeline up to max_retries times in case of errors.
        """
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
