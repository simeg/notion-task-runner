import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from notion_task_runner.tasks.backup.google_drive_upload_task import GoogleDriveUploadTask
from notion_task_runner.tasks.task_config import TaskConfig


@pytest.fixture
def mock_config(tmp_path):
    config = MagicMock(spec=TaskConfig)
    config.downloads_directory_path = tmp_path
    return config


@patch("notion_task_runner.tasks.backup.google_drive_upload_task.GoogleDriveUploader")
@patch("notion_task_runner.tasks.backup.google_drive_upload_task.ExportFileWatcher.wait_for_file")
def test_run_success(mock_wait_for_file, mock_uploader_cls, mock_config):
    dummy_file = Path("/fake/notion-backup.zip")
    mock_wait_for_file.return_value = dummy_file
    mock_uploader = MagicMock()
    mock_uploader.upload.return_value = True
    mock_uploader_cls.return_value = mock_uploader

    with patch.dict("os.environ", {"GOOGLE_DRIVE_ROOT_FOLDER_ID": "folder123"}):
        task = GoogleDriveUploadTask(mock_config)
        task.run()

    mock_wait_for_file.assert_called_once_with(mock_config.downloads_directory_path, "notion-backup")
    mock_uploader.upload.assert_called_once_with(dummy_file)

@patch("notion_task_runner.tasks.backup.google_drive_upload_task.GoogleDriveUploader")
@patch("notion_task_runner.tasks.backup.google_drive_upload_task.ExportFileWatcher.wait_for_file", return_value=Path("/fake/file.zip"))
def test_run_raises_if_upload_fails(mock_wait_for_file, mock_uploader_cls, mock_config):
    mock_uploader = MagicMock()
    mock_uploader.upload.return_value = False
    mock_uploader_cls.return_value = mock_uploader

    with patch.dict("os.environ", {"GOOGLE_DRIVE_ROOT_FOLDER_ID": "folder123"}):
        task = GoogleDriveUploadTask(mock_config)
        with pytest.raises(SystemExit):
            task.run()