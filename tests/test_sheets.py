import os
from unittest.mock import MagicMock, patch

import pandas as pd

from ingestion.sheets import SheetsManager, SheetsParser


def test_get_dataframe():
    data = [["quantity", "stock"], [1, 2], [25, 8]]
    header, rows = data[0], data[1:]
    expected_df = pd.DataFrame(data=rows, columns=header)
    with patch.object(SheetsManager, "get_dataframe", return_value=expected_df):
        df = SheetsManager.get_dataframe()
        pd.testing.assert_frame_equal(df, expected_df)


def test_ingest_data_writes_when_not_exists():
    mock_sheet_manager = MagicMock()
    mock_sheet_manager.sheet.title = "stores-DEC"

    df = pd.DataFrame({"quantity": [1, 2], "price": [3, 4]})
    with patch("ingestion.sheets.MoveData") as MockMoveData, patch(
        "ingestion.sheets.write_parquet"
    ) as Mock_write_parquet:
        dataclass = MockMoveData.return_value
        dataclass.exist_by_basenam.return_value = False
        parser = SheetsParser(dst_client="test-client", dst_bucket="test-bucket")
        parser.ingest_data("raw", mock_sheet_manager, df)


def test_ingest_data_skips_when_exists():
    mock_sheet_manager = MagicMock()
    mock_sheet_manager.sheet.title = "launchpad-stores"
    df = pd.DataFrame({"quantity": [1, 2], "price": [3, 4]})

    with patch("ingestion.sheets.MoveData") as MockMoveData, patch(
        "ingestion.sheets.write_parquet"
    ) as mock_write_parquet:
        instance = MockMoveData.return_value
        instance.exists_by_basename.return_value = True
        parser = SheetsParser(dst_client="test-client", dst_bucket="test-bucket")
        parser.ingest_data("raw", mock_sheet_manager, df)

        mock_write_parquet.assert_not_called()
