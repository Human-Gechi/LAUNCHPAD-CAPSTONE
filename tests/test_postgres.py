from unittest.mock import MagicMock, patch

from ingestion.postgres import Postgres


def test_connect_rds_success():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.login = "FAKE_KEY"
    mock_conn.password = "FAKE_SECRET"
    mock_conn.port = 1234
    mock_conn.database = "FAKE_DB"

    mock_hook = MagicMock()
    mock_hook.get_conn.return_value = mock_conn

    with patch("ingestion.postgres.PostgresHook", return_value=mock_hook):
        pg = Postgres(dst_client="test-client", dst_bucket="test-bucket", conn_id="postgres_conn")
        conn = pg.connect_rds()
        assert conn == mock_conn
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_with("SELECT 1;")
        mock_cursor.fetchone.assert_called_once()
