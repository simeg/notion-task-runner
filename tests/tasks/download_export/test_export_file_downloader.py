from pathlib import Path
from unittest.mock import MagicMock

import pytest

from notion_task_runner.notion import NotionClient
from notion_task_runner.tasks.download_export.export_file_downloader import \
    ExportFileDownloader


@pytest.fixture
def fake_path(tmp_path):
    return tmp_path / "test.zip"


def test_download_and_verify_success(tmp_path):
    client = MagicMock(spec=NotionClient)
    downloader = ExportFileDownloader(client)

    # Mock response with iter_content
    mock_response = MagicMock()
    mock_response.iter_content = MagicMock(return_value=[b'data chunk'])
    client.get.return_value = mock_response

    path = tmp_path / "downloaded.zip"
    result = downloader.download_and_verify("http://fake.url/file.zip", path)

    assert result == path
    assert path.is_file()
    with open(path, "rb") as f:
        assert f.read() == b'data chunk'


def test_download_and_verify_fail_download(tmp_path):
    client = MagicMock(spec=NotionClient)
    downloader = ExportFileDownloader(client)

    # Simulate failed download (None returned)
    downloader._download_file = MagicMock(return_value=None)

    path = tmp_path / "missing.zip"
    result = downloader.download_and_verify("http://fake.url/fail.zip", path)

    assert result is None


def test_download_file_exception(tmp_path):
    client = MagicMock(spec=NotionClient)
    downloader = ExportFileDownloader(client)

    client.get.side_effect = Exception("network error")
    result = downloader._download_file("http://fake.url/file.zip", tmp_path / "output.zip")

    assert result is None

def test_download_file_retries_on_failure(tmp_path: Path):
    client = MagicMock(spec=NotionClient)
    client.get.side_effect = Exception("network error")

    downloader = ExportFileDownloader(client, max_retries=3, retry_wait_seconds=0)
    path = tmp_path / "output.zip"

    result = downloader._download_file("http://fake.url/file.zip", path)
    assert result is None
    assert client.get.call_count == 3

    # Ensure it retried 3 times
    assert client.get.call_count == 3