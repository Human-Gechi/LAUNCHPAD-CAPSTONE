import snowflake.connector
import os
import pandas as pd
from dotenv import load_dotenv
import pandas as pd
import io

from ingestion.s3_to_s3 import S3ClientFactory
from snowflake.connector.pandas_tools import write_pandas

from log import ingest_logger
load_dotenv()

DST_ACCESS_KEY = os.getenv("DST_ACCESS_KEY")
DST_SECRET_KEY = os.getenv("DST_SECRET_KEY")
DST_BUCKET = os.getenv("DST_BUCKET")
DST_REGION = os.getenv("DST_REGION")

dst_client = S3ClientFactory.create_client(DST_ACCESS_KEY, DST_SECRET_KEY, DST_REGION)
base = 'raw/'

pq_to_sf_type = {
    "Int64": "NUMBER",
    "int64": "NUMBER",
    "Float64": "FLOAT",
    "float64": "FLOAT",
    "str": "VARCHAR",
    "object": "VARCHAR",
    "bool": "BOOLEAN"
}

class SnowFlake:
    def __init__(self,dst_client, dst_bucket):
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
            role = self.role
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
        cur.execute(f"""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{self.schema}'
            AND TABLE_NAME = '{table_name}'
        """)
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
        for obj in files.get('Contents', []):
            key = obj["Key"]
            parts = key.split('/')
            if len(parts) > 1 and parts[1]:
                directories.add(parts[1])
        return directories

    def get_parquet_files_in_dir(self, directory):
        files = self.dst_client.list_objects_v2(Bucket=self.dst_bucket, Prefix=f'{base}{directory}/')
        parquet_files = []
        for obj in files.get('Contents', []):
            key = obj["Key"]
            if key.endswith('.parquet'):
                parquet_files.append(key)
        return parquet_files

    def create_tables_from_directories(self):
        conn = self.conn_sf()
        cur = conn.cursor()

        directories = self.get_directories()
        for directory in directories:
            table = directory.upper()
            ingest_logger.info(f"🔄️ Processing directory: {directory} -> table: {table}")

            parquet_files = self.get_parquet_files_in_dir(directory)
            dfs = []
            for key in parquet_files:
                obj = self.dst_client.get_object(Bucket=self.dst_bucket, Key=key)
                data = obj['Body'].read()
                df = pd.read_parquet(io.BytesIO(data))
                df = df.drop_duplicates()
                dfs.append(df)

            if not dfs:
                ingest_logger.info(f"No parquet files found in {directory}, ⏩ Skipping.....")
                continue
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df.columns = [c.upper() for c in combined_df.columns]

            columns = []
            for col, dtype in zip(combined_df.columns, combined_df.dtypes):
                    sf_type = self.parquet_dtypes_to_snowflake(dtype.name)
                    columns.append(f'{col} {sf_type}')
            columns_sql = ", ".join(columns)
            create_sql = f'CREATE TABLE IF NOT EXISTS {table} ({columns_sql});'

            if not self.table_exists(cur, table):
                ingest_logger.info(f"Creating and inserting into new table {table}")
                cur.execute(create_sql)
                write_pandas(conn, combined_df, table)
            else:
                staging_table = f"{table}_STAGING"
                cur.execute(f"CREATE OR REPLACE TABLE {staging_table} ({columns_sql});")
                write_pandas(conn, combined_df, staging_table)
                merge_sql = f"""
                    MERGE INTO {table} t
                    USING {staging_table} s
                    ON ({" AND ".join([f't."{col}" = s."{col}"' for col in combined_df.columns])})
                    WHEN NOT MATCHED THEN
                      INSERT ({', '.join([f'"{col}"' for col in combined_df.columns])})
                      VALUES ({', '.join([f's."{col}"' for col in combined_df.columns])});

                """
                cur.execute(merge_sql)
                count = cur.fetchone()[0]
                ingest_logger.info(f"📌 Upserted {count} rows into {table}")
                cur.execute(f"DROP TABLE IF EXISTS {staging_table}")
                ingest_logger.info("✅ Staging tables dropped")


        cur.close()
        conn.close()
sf = SnowFlake(dst_client, DST_BUCKET)
sf.create_tables_from_directories()