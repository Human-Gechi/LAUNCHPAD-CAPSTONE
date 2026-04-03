import os

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

from ingestion.s3_to_s3 import MoveData
from ingestion.write import write_parquet
from logs.log import get_ingest_logger

ingest_logger = get_ingest_logger()


class SheetsManager:
    """
    Manages connection to Google Sheet and methods to retrieve data as DataFrame.
    """

    def __init__(self, sheet_url=None, creds_file=None):
        """
        Initialize the SheetsManager with the Google Sheets URL and credentials file.

        Args:
            sheet_url (str, optional): The url of Google Sheet. If not provided,
            uses SHEETS_URL from environment.
            creds_file (str, optional): Path to the Google service account credentials json file.
        """
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        self.creds_file = creds_file or "crested-pursuit-457714-c8-f5a68d29f980.json"
        self.sheet_url = sheet_url or os.getenv("SHEETS_URL")
        self.creds = Credentials.from_service_account_file(self.creds_file, scopes=self.scope)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_url(self.sheet_url)
        self.worksheet = self.sheet.sheet1
        ingest_logger.info("✅ Worsheet found, opened")

    def get_dataframe(self):
        """
        Fetches all values(rows) fro the worksheet and return a DataFrame

        Returns:
            pd.DataFrame
        """
        data = self.worksheet.get_all_values()
        header, rows = data[0], data[1:]
        ingest_logger.info("✅ DataFrame created successfully")
        return pd.DataFrame(rows, columns=header)


class SheetsParser:
    """
    Handles ingesting data from Google Sheet into s3 bucket.
    """

    def __init__(self, dst_client, dst_bucket):
        """
        Initialize the SheetsParser with a destination client and bucket.

        Args:
            dst_client (boto3.client): Destination S3 client.
            dst_bucket (str): Destination S3 bucket name.
        """
        self.dst_client = dst_client
        self.dst_bucket = dst_bucket
        self.data_source = "sheets"

    def ingest_data(self, source, sheet_manager, df):
        """
        Ingest the provided DataFrame into s3 .

        Args:
            source (str): The s3 prefix/folder to write to.
            sheet_manager (SheetsManager)
            df (pd.DataFrame): The DataFrame to upload to s3 ucket

        Raises:
            gspread.exceptions.SpreadsheetNotFound
            gspread.exceptions
        """
        try:
            title_parts = sheet_manager.sheet.title.split("-")
            idx = title_parts.index("stores")
            sheets_title = title_parts[idx]
            data_class = MoveData(None, self.dst_client, None, self.dst_bucket)
            prefix = f"{source}/stores"
            file_existence = data_class.exists_by_basename(prefix, sheets_title)
            if not file_existence:
                write_parquet(df, self.data_source, prefix, sheets_title)
            else:
                ingest_logger.info(f"⏩ Skipping {prefix}/{sheets_title} exists in s3")
        except gspread.exceptions.SpreadsheetNotFound as e:
            ingest_logger.error(f"🚨 Spreadsheet Missing: {e}")
        except gspread.exceptions as e:
            ingest_logger.error(f"An unexpected error occured: {e}")
