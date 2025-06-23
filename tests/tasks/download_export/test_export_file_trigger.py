import pytest
from unittest.mock import MagicMock
from notion_task_runner.tasks.download_export.export_file_trigger import ExportFileTrigger


@pytest.fixture
def mock_config():
    mock = MagicMock()
    mock.notion_token_v2 = "fake-token"
    mock.notion_space_id = "fake-space"
    mock.export_type = "html"
    mock.flatten_export_file_tree = False
    return mock


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def trigger(mock_client, mock_config):
    return ExportFileTrigger(client=mock_client, config=mock_config)


def test_trigger_success(trigger, mock_client):
    mock_client.post.return_value = {"taskId": "abc123"}

    result = trigger.trigger_export_task()

    assert result == "abc123"
    mock_client.post.assert_called_once()


def test_trigger_error_without_task_id(trigger, mock_client):
    mock_client.post.return_value = {
        "name": "SomeError",
        "message": "Something went wrong",
    }

    result = trigger.trigger_export_task()

    assert result is None


def test_trigger_unauthorized_error(trigger, mock_client):
    mock_client.post.return_value = {
        "name": "UnauthorizedError",
        "message": "Invalid token",
    }

    result = trigger.trigger_export_task()

    assert result is None