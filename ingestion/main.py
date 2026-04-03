base = "raw"


def main():
    """
    Main function for data ingestion ndata
    """
    from ingestion.config import get_config
    from ingestion.postgres import Postgres
    from ingestion.s3_to_s3 import MoveData, S3ClientFactory
    from ingestion.s3_to_snowflake import SnowFlake
    from ingestion.sheets import SheetsManager, SheetsParser

    config = get_config()

    mover = MoveData(
        S3ClientFactory.create_client("SRC"),
        S3ClientFactory.create_client("DST"),
        config["SRC_BUCKET"],
        config["DST_BUCKET"],
    )
    print(mover)
    mover.ingest_files(base)

    sheets = SheetsManager()
    df = sheets.get_dataframe()
    parser = SheetsParser(S3ClientFactory.create_client("DST"), config["DST_BUCKET"])
    parser.ingest_data(base, sheets, df)

    post = Postgres(S3ClientFactory.create_client("DST"), config["DST_BUCKET"])
    print(post.ingest_data(base))

    sf = SnowFlake(S3ClientFactory.create_client("DST"), config["DST_BUCKET"])
    sf.create_tables_from_directories()


main()
