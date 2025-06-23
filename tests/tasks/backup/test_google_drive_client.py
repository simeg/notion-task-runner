from unittest.mock import MagicMock, patch
from googleapiclient.errors import HttpError

from notion_task_runner.tasks.backup.google_drive_client import \
  GoogleDriveClient


def test_upload_successful(tmp_path):
    file = tmp_path / "test.zip"
    file.write_text("dummy content")

    mock_drive_service = MagicMock()
    mock_create = mock_drive_service.files.return_value.create
    mock_create.return_value.execute.return_value = {"id": "123"}

    client = GoogleDriveClient(mock_drive_service, "root-folder-id")
    success = client.upload(file)

    assert success is True
    mock_create.assert_called_once()


def test_upload_file_not_found(tmp_path):
    file = tmp_path / "does_not_exist.zip"

    mock_drive_service = MagicMock()
    client = GoogleDriveClient(mock_drive_service, "root-folder-id")

    success = client.upload(file)

    assert success is False
    mock_drive_service.files.assert_not_called()



@patch("notion_task_runner.tasks.backup.google_drive_client.log") # Silence logging for cleaner test output
def test_upload_raises_http_error(mock_log, tmp_path):
  file = tmp_path / "test.zip"
  file.write_text("dummy content")

  mock_drive_service = MagicMock()
  mock_create = mock_drive_service.files.return_value.create

  # Simulate HTTP error with required response attributes
  mock_resp = MagicMock()
  mock_resp.status = 500
  mock_resp.reason = "Internal Server Error"
  mock_error = HttpError(resp=mock_resp, content=b"Upload failed")

  mock_create.return_value.execute.side_effect = mock_error

  client = GoogleDriveClient(mock_drive_service, "root-folder-id")
  success = client.upload(file)

  assert success is False
  mock_log.warning.assert_called_once()