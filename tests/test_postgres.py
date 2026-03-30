from ingestion.postgres import Postgres
from unittest.mock import patch, MagicMock

def test_connect_rds_success():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,)

    with patch("psycopg2.connect", return_value=mock_conn):
        pg = Postgres(dst_client="test-client", dst_bucket="test-bucket")
        conn = pg.connect_rds()
        assert conn == mock_conn
        mock_conn.cursor.assert_called_once()
