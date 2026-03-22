import os

import gspread
import pandas as pd
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

from ingestion.s3_to_s3 import MoveData, S3ClientFactory
from ingestion.write import write_parquet
from log import ingest_logger

load_dotenv()

DST_ACCESS_KEY = os.getenv("DST_ACCESS_KEY")
DST_SECRET_KEY = os.getenv("DST_SECRET_KEY")
DST_BUCKET = os.getenv("DST_BUCKET")
DST_REGION = os.getenv("DST_REGION")

dst_client = S3ClientFactory.create_client(DST_ACCESS_KEY, DST_SECRET_KEY, DST_REGION)


class SheetsManager:
    def __init__(self, sheet_url=None, creds_file=None):
        self.scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        self.creds_file = creds_file or "crested-pursuit-457714-c8-f5a68d29f980.json"
        self.sheet_url = sheet_url or os.getenv("SHEETS_URL")
        self.creds = Credentials.from_service_account_file(self.creds_file, scopes=self.scope)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_url(self.sheet_url)
        self.worksheet = self.sheet.sheet1
        ingest_logger.info("✅ Worsheet found, opened")

    def get_dataframe(self):
        data = self.worksheet.get_all_values()
        header, rows = data[0], data[1:]
        ingest_logger.info("✅ DataFrame created successfully")
        return pd.DataFrame(rows, columns=header)


class SheetsParser:
    def __init__(self, dst_client, dst_bucket):
        self.dst_client = dst_client
        self.dst_bucket = dst_bucket

    def ingest_data(self, source, sheet_manager, df):
        title_parts = sheet_manager.sheet.title.split("-")
        sheets_title = "-".join(title_parts[2:])
        data_class = MoveData(None, self.dst_client, None, self.dst_bucket)
        prefix = f"{source}/locations"
        file_existence = data_class.exists_by_basename(prefix, sheets_title)
        if not file_existence:
            write_parquet(df, source, "locations", sheets_title)
        else:
            ingest_logger.info(f"⏩ Skipping {prefix}/{sheets_title} exists in s3")


#sheets = SheetsManager()
#df = sheets.get_dataframe()
#parser = SheetsParser(dst_client, DST_BUCKET)
#parser.ingest_data("raw", sheets, df)
