from unittest.mock import MagicMock

import pytest
import tenacity

from notion_task_runner.tasks.download_export.export_file_poller import (
    ExportFilePoller,
    MissingExportLinkError,
    NoActivityError,
    StaleExportError,
)


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.notion_space_id = "test_space"
    config.notion_token_v2 = "test_token"
    return config


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def sut(mock_client, mock_config):
    return ExportFilePoller(client=mock_client, config=mock_config, max_retries=2, retry_wait_seconds=0)


@pytest.mark.asyncio
async def test_poll_success(sut, mock_client):
    from unittest.mock import AsyncMock
    mock_client.post = AsyncMock(return_value={
        "recordMap": {
            "activity": {
                "some_key": {
                    "value": {
                        "start_time": 100,
                        "edits": [{"link": "https://notion.so/download"}],
                    }
                }
            }
        }
    })

    url = await sut.poll_for_download_url(export_trigger_timestamp=99)
    assert url == "https://notion.so/download"


@pytest.mark.asyncio
async def test_poll_stale_export(sut, mock_client):
    from unittest.mock import AsyncMock
    mock_client.post = AsyncMock(return_value={
        "recordMap": {
            "activity": {
                "some_key": {
                    "value": {
                        "start_time": 50,
                        "edits": [{"link": "https://notion.so/download"}],
                    }
                }
            }
        }
    })

    with pytest.raises(tenacity.RetryError) as exc_info:
        await sut.poll_for_download_url(export_trigger_timestamp=99)

    assert isinstance(exc_info.value.last_attempt.exception(), StaleExportError)


@pytest.mark.asyncio
async def test_poll_missing_link(sut, mock_client):
    from unittest.mock import AsyncMock
    mock_client.post = AsyncMock(return_value={
        "recordMap": {
            "activity": {
                "some_key": {
                    "value": {
                        "start_time": 100,
                        "edits": [{}],
                    }
                }
            }
        }
    })

    with pytest.raises(tenacity.RetryError) as exc_info:
        await sut.poll_for_download_url(export_trigger_timestamp=99)

    assert isinstance(exc_info.value.last_attempt.exception(), MissingExportLinkError)


@pytest.mark.asyncio
async def test_poll_no_activity(sut, mock_client):
    from unittest.mock import AsyncMock
    mock_client.post = AsyncMock(return_value={
        "recordMap": {}
    })

    with pytest.raises(tenacity.RetryError) as exc_info:
        await sut.poll_for_download_url(export_trigger_timestamp=99)

    assert isinstance(exc_info.value.last_attempt.exception(), NoActivityError)

@pytest.mark.asyncio
async def test_poll_malformed_response(sut, mock_client):
    from unittest.mock import AsyncMock
    mock_client.post = AsyncMock(return_value={})

    with pytest.raises(tenacity.RetryError) as exc_info:
        await sut.poll_for_download_url(export_trigger_timestamp=99)

    assert isinstance(exc_info.value.last_attempt.exception(), NoActivityError)


@pytest.mark.asyncio
async def test_poll_retries_on_no_activity(mock_client, mock_config):
    from unittest.mock import AsyncMock
    sut = ExportFilePoller(client=mock_client, config=mock_config, max_retries=3, retry_wait_seconds=0)

    # Simulate NoActivityError for each retry attempt
    mock_client.post = AsyncMock(side_effect=[{}] * 3)  # Causes NoActivityError each time

    with pytest.raises(tenacity.RetryError) as exc_info:
        await sut.poll_for_download_url(export_trigger_timestamp=999)

    assert isinstance(exc_info.value.last_attempt.exception(), NoActivityError)

    assert mock_client.post.call_count == 3
