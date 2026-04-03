import os
import time

import pandas as pd
import psycopg2
from dotenv import load_dotenv

from ingestion.s3_to_s3 import MoveData
from ingestion.write import write_parquet
from logs.log import get_ingest_logger

ingest_logger = get_ingest_logger()

load_dotenv()

script_dir = os.path.dirname(os.path.abspath(__file__))
sql_path = os.path.join(script_dir, "tables.sql")


class Postgres:
    """
    Postgres

    Attributes:
        dst_client (str): AWS s3 destination client
        dst_bucket (str): AWS s3 destination bucket

    Methods:
        connect_rds:
            Makes a connection to AWS Relational Database Service
        get_table_names:
            Retrieves names of tables in AWS RDS
        ingest_data:
            Ingests data from RDS to s3 destination bucket
    """

    def __init__(self, dst_client, dst_bucket):
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.user = os.getenv("DB_USER")
        self.db = os.getenv("DB_NAME")
        self.password = os.getenv("DB_PASSWORD")
        self.dst_client = dst_client
        self.dst_bucket = dst_bucket
        self.data_source = "rds"

    def connect_rds(self):
        """
        Establishes a connection to the AWS RDS PostgreSQL database using credentials
        loaded from environment variables.

        Returns:
            conn: A connection object to the RDS instance.
        """
        retry = 5
        for attempt in range(retry):
            try:
                conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    dbname=self.db,
                    sslmode="require",
                    connect_timeout=30,
                )
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1;")
                        cur.fetchone()
                except Exception as e:
                    ingest_logger.error(f"❌ Connection test failed: {e}")
                    conn.close()
                    continue
                ingest_logger.info("✅ Connection to AWS RDS secured and tested")
                return conn
            except psycopg2.OperationalError as e:
                ingest_logger.error(f"{e}")
                time.sleep(5)
        ingest_logger.error("❌ Could not establish a valid connection to AWS RDS after retries.")
        return None

    def get_table_names(self):
        """
        Retrieves the names of tables from the AWS RDS database using the SQL
        query stored in tables.sql.

        Returns:
            list: A list of table names (str) present in the database.

        Raises:
        psycopg2.ProgrammingError : If query is invalid
        psycopg2.OperationalError : If an unusual error occured. Errors like Net. issues

        """
        try:
            conn = self.connect_rds()
            if conn is None:
                ingest_logger.error("❌ Could not establish a connection to AWS RDS.")
                return []
            with conn:
                with conn.cursor() as cur:
                    with open(sql_path) as f:
                        query = f.read()
                        cur.execute(query)
                        rows = cur.fetchall()
                        table_names = [row[0] for row in rows]
                        if table_names:
                            ingest_logger.info(f"✅ Number of tables present: {len(table_names)}")
                        else:
                            ingest_logger.warning("⚠️ No table names retrieved from the database.")
                    return table_names
        except psycopg2.ProgrammingError as e:
            ingest_logger.error(f"❌ Invalid query {e}")
            return []
        except psycopg2.OperationalError as e:
            ingest_logger.error(f"❌ An unexpected error occurred: {e}")
            return []

    def ingest_data(self, source: str, batch_size=10000, max_attempts=5):
        """
        Ingests data from each table in the AWS RDS database in batches, concatenates the
        batches, and writes the complete DataFrame for each table to an S3 bucket in Parquet format.

        Args:
            source (str): The source prefix for S3.
            batch_size (int, optional): Number of rows to fetch per batch. Defaults to 10,000.
            max_attempts (int, optional): Maximum retry attempts for each batch. Defaults to 3.
            base_delay (int, optional): Initial delay (seconds) for backoff. Defaults to 1.

        Raises:
            psycopg2.OperationalError : If an unusual error occured. Errors like Network issues
        """
        conn = self.connect_rds()
        if conn is None:
            ingest_logger.error("❌ Database connection failed")
            return None
        table_names = self.get_table_names()
        data_class = MoveData(None, self.dst_client, None, self.dst_bucket)
        prefix = f"{source}/transactions"
        for table in table_names:
            offset = 0
            batches = []
            while True:
                attempt = 1
                while attempt <= max_attempts:
                    with conn.cursor() as cur:
                        try:
                            query = f"SELECT * FROM {table} LIMIT {batch_size} OFFSET {offset}"
                            cur.execute(query)
                            cols = [col[0] for col in cur.description]
                            column_names = [col for col in cols]
                            rows = cur.fetchall()
                            if not rows:
                                break
                            df = pd.DataFrame(rows, columns=column_names)
                            batches.append(df)
                            offset += batch_size
                            break
                        except psycopg2.OperationalError as e:
                            ingest_logger.error(f"⚠️ Error on attempt {attempt} for {table}: {e}")
                            if attempt == max_attempts:
                                ingest_logger.error(
                                    f"""❌ Max attempts reached for {table} batch at offset {offset}
                                    ⏩ Skipping batch.
                                    """
                                )
                                break
                            backoff = 2 ** (attempt - 1)
                            ingest_logger.warning(f"⚠️ Retrying in {backoff}s.............")
                            time.sleep(backoff)
                            attempt += 1
                        except Exception as e:
                            ingest_logger.error(f"❌ Error fetching data from {table}: {e}")
                            break
                else:
                    break
                if not rows:
                    break

            if not batches:
                ingest_logger.warning(f"⚠️ Table {table} is empty.")
                continue
            ingest_logger.info(f"Extracting {table}..... from db")

            final_df = pd.concat(batches, ignore_index=True)
            file_existence = data_class.exists_by_basename(prefix, table)
            if not file_existence:
                write_parquet(final_df, self.data_source, prefix, table)
                ingest_logger.info(f"✅ Wrote {len(final_df)} rows from {table} to S3")
            else:
                ingest_logger.info(f"⏩ Skipping {prefix}/{table} exists in s3")
