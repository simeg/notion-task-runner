import pytest
from unittest.mock import MagicMock
from pathlib import Path
from notion_task_runner.tasks.download_export.export_file_task import ExportFileTask


@pytest.fixture
def mock_config():
    mock = MagicMock()
    mock.export_type = "html"
    mock.flatten_export_file_tree = False
    mock.downloads_directory_path = "/tmp"
    return mock


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def export_file_task(mock_client, mock_config):
    return ExportFileTask(client=mock_client, config=mock_config)


def test_run_success(monkeypatch, export_file_task, mock_config):
    export_file_task.trigger.trigger_export_task = MagicMock(return_value="fake-task-id")
    export_file_task.poller.poll_for_download_url = MagicMock(return_value="http://fake.url/export.zip")
    fake_file = Path("/tmp/notion-backup.html_2025-06-23_00-00-00.zip")
    export_file_task.downloader.download_and_verify = MagicMock(return_value=fake_file)

    result = export_file_task.run()

    assert result == fake_file


def test_run_fails_on_missing_task_id(export_file_task):
    export_file_task.trigger.trigger_export_task = MagicMock(return_value=None)

    result = export_file_task.run()

    assert result is None


def test_run_fails_on_missing_download_url(export_file_task):
    export_file_task.trigger.trigger_export_task = MagicMock(return_value="fake-task-id")
    export_file_task.poller.poll_for_download_url = MagicMock(return_value=None)

    result = export_file_task.run()

    assert result is None


def test_run_fails_on_download_error(export_file_task):
    export_file_task.trigger.trigger_export_task = MagicMock(return_value="fake-task-id")
    export_file_task.poller.poll_for_download_url = MagicMock(return_value="http://fake.url/export.zip")
    export_file_task.downloader.download_and_verify = MagicMock(return_value=None)

    result = export_file_task.run()

    assert result is None


def test_run_handles_exception_gracefully(export_file_task):
    export_file_task.trigger.trigger_export_task = MagicMock(side_effect=Exception("Boom"))

    result = export_file_task.run()

    assert result is None