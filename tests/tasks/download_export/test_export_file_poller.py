import itertools
from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch, ANY
from notion_task_runner.notion import NotionClient
from notion_task_runner.tasks.download_export.export_file_poller import \
  ExportFilePoller
from notion_task_runner.tasks.task_config import TaskConfig


@pytest.fixture
def mock_config():
    return TaskConfig(
        notion_token_v2="test-token",
        notion_space_id="test-space",
        notion_api_key="test-api-key",
        downloads_directory_path=Path("test-downloads-directory"),
        export_type="markdown",
        flatten_export_file_tree=True,
    )


@pytest.fixture
def sut(mock_config):
    client = MagicMock(spec=NotionClient)
    return ExportFilePoller(client, mock_config)


@patch("notion_task_runner.tasks.download_export.export_file_poller.log")
@patch("time.sleep", return_value=None)
def test_poll_returns_url_on_valid_response(mock_sleep, mock_log, sut):
    mock_response = {
        "recordMap": {
            "activity": {
                "some_id": {
                    "value": {
                        "start_time": 9999999999,
                        "edits": [{"link": "https://notion.so/download.zip"}]
                    }
                }
            }
        }
    }
    sut.client.post.return_value = mock_response
    url = sut.poll_for_download_url(100)
    assert url == "https://notion.so/download.zip"


@patch("notion_task_runner.tasks.download_export.export_file_poller.log")
@patch("time.sleep", return_value=None)
def test_poll_skips_old_notifications(mock_sleep, mock_log, sut):
    old_response = {
        "recordMap": {
            "activity": {
                "some_id": {
                    "value": {
                        "start_time": 50,  # older than trigger
                        "edits": [{"link": "https://notion.so/download.zip"}]
                    }
                }
            }
        }
    }
    sut.client.post.side_effect = itertools.chain([old_response] * 3, itertools.repeat({}))
    url = sut.poll_for_download_url(100)
    assert url is None


@patch("notion_task_runner.tasks.download_export.export_file_poller.log")
@patch("time.sleep", return_value=None)
def test_poll_handles_no_activity(mock_sleep, mock_log, sut):
    empty_response = {"recordMap": {}}
    sut.client.post.side_effect = itertools.chain([empty_response] * 3, itertools.repeat({}))
    url = sut.poll_for_download_url(100)
    assert url is None


@patch("notion_task_runner.tasks.download_export.export_file_poller.log")
@patch("time.sleep", return_value=None)
def test_poll_handles_missing_link(mock_sleep, mock_log, sut):
    response_missing_link = {
        "recordMap": {
            "activity": {
                "some_id": {
                    "value": {
                        "start_time": 9999999999,
                        "edits": [{}]
                    }
                }
            }
        }
    }
    sut.client.post.side_effect = itertools.chain([response_missing_link] * 3, itertools.repeat({}))
    url = sut.poll_for_download_url(100)
    assert url is None


@patch("notion_task_runner.tasks.download_export.export_file_poller.log")
@patch("time.sleep", return_value=None)
def test_poll_handles_exception(mock_sleep, mock_log, sut):
    sut.client.post.side_effect = Exception("Boom!")
    with pytest.raises(Exception, match="Boom!"):
        sut.poll_for_download_url(100)

@patch("notion_task_runner.tasks.download_export.export_file_poller.log")
@patch("time.sleep", return_value=None)
def test_poll_for_download_url_keyerror_on_value(mock_sleep, mock_log):
    mock_client = MagicMock(spec=NotionClient)
    mock_config = MagicMock(spec=TaskConfig)
    mock_config.notion_token_v2 = "test-token"
    mock_config.notion_space_id = "test-space"

    # This will make activity_map truthy, but the inner dict lacks the "value" key
    mock_client.post.return_value = {
        "recordMap": {
            "activity": {
                "some_id": {
                    # Missing "value" key will trigger KeyError at line 69
                }
            }
        }
    }

    sut = ExportFilePoller(mock_client, mock_config)
    result = sut.poll_for_download_url(export_trigger_timestamp=100)

    assert result is None
    mock_log.error.assert_called_with(
    "Error parsing response", exc_info=ANY)