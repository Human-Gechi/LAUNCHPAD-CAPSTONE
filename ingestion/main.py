from ingestion.postgres import Postgres
from ingestion.sheets import SheetsManager, SheetsParser
from ingestion.s3_to_s3 import src_client, dst_client, SRC_BUCKET, DST_BUCKET, MoveData

base = 'raw'
def main():
    mover = MoveData(src_client, dst_client, SRC_BUCKET, DST_BUCKET)
    mover.ingest_files(base)

    sheets = SheetsManager()
    df = sheets.get_dataframe()
    parser = SheetsParser(dst_client, DST_BUCKET)
    parser.ingest_data(base, sheets, df)

    post = Postgres(dst_client, DST_BUCKET)
    print(post.ingest_data(base))

if __name__ == "__main__":
    main()