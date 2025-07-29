from pathlib import Path
from unittest.mock import MagicMock

import pytest

from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.tasks.download_export.export_file_downloader import \
    ExportFileDownloader


@pytest.fixture
def fake_path(tmp_path):
    return tmp_path / "test.zip"


@pytest.mark.asyncio
async def test_download_and_verify_success(tmp_path):
    from unittest.mock import AsyncMock
    
    client = MagicMock(spec=AsyncNotionClient)
    downloader = ExportFileDownloader(client)

    # Mock response with iter_chunked
    async def mock_iter_chunked(size):
        yield b'data chunk'
    
    mock_content = MagicMock()
    mock_content.iter_chunked = mock_iter_chunked
    mock_response = MagicMock()
    mock_response.content = mock_content
    client.get = AsyncMock(return_value=mock_response)

    path = tmp_path / "downloaded.zip"
    result = await downloader.download_and_verify("http://fake.url/file.zip", path)

    assert result == path
    assert path.is_file()
    with open(path, "rb") as f:
        assert f.read() == b'data chunk'


@pytest.mark.asyncio
async def test_download_and_verify_fail_download(tmp_path):
    from unittest.mock import AsyncMock
    
    client = MagicMock(spec=AsyncNotionClient)
    downloader = ExportFileDownloader(client)

    # Simulate failed download (None returned)
    downloader._download_file = AsyncMock(return_value=None)

    path = tmp_path / "missing.zip"
    result = await downloader.download_and_verify("http://fake.url/fail.zip", path)

    assert result is None


@pytest.mark.asyncio
async def test_download_file_exception(tmp_path):
    from unittest.mock import AsyncMock
    
    client = MagicMock(spec=AsyncNotionClient)
    downloader = ExportFileDownloader(client)

    client.get.side_effect = Exception("network error")
    result = await downloader._download_file("http://fake.url/file.zip", tmp_path / "output.zip")

    assert result is None

@pytest.mark.asyncio
async def test_download_file_retries_on_failure(tmp_path: Path):
    from unittest.mock import AsyncMock
    
    client = MagicMock(spec=AsyncNotionClient)
    client.get.side_effect = Exception("network error")

    downloader = ExportFileDownloader(client, max_retries=3, retry_wait_seconds=0)
    path = tmp_path / "output.zip"

    result = await downloader._download_file("http://fake.url/file.zip", path)
    assert result is None
    assert client.get.call_count == 3

    # Ensure it retried 3 times
    assert client.get.call_count == 3