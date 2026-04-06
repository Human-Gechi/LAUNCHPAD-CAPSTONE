base = "raw"


def main():
    """
    Main function for data ingestion ndata
    """
    from ingestion.postgres import Postgres
    from ingestion.s3_to_s3 import MoveData, S3ClientFactory
    from ingestion.s3_to_snowflake import SnowFlake
    from ingestion.sheets import SheetsManager, SheetsParser

    src_client = S3ClientFactory.create_client(conn_id="aws_src")
    dst_client = S3ClientFactory.create_client(conn_id="aws_dst")
    src_bucket = "supplychain360-data"
    dst_bucket = "supply-chain-360-data"

    mover = MoveData(src_client, dst_client, src_bucket, dst_bucket)
    mover.ingest_files(base)

    sheets = SheetsManager()
    df = sheets.get_dataframe()
    parser = SheetsParser(dst_client, dst_bucket)
    parser.ingest_data(base, sheets, df)

    post = Postgres(dst_client, dst_bucket)
    print(post.ingest_data(base))

    sf = SnowFlake(dst_client, dst_bucket)
    sf.create_tables_from_directories()
