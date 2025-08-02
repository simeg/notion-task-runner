from unittest.mock import MagicMock, patch

import pytest
from googleapiclient.errors import HttpError

from notion_task_runner.tasks.backup.google_drive_uploader import GoogleDriveUploader
from notion_task_runner.tasks.task_config import TaskConfig


@pytest.fixture
def dummy_secret():
    # A minimal but valid service account JSON string for testing
    return """{
        "type": "service_account",
        "project_id": "dummy",
        "private_key_id": "key_id",
        "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
        "client_email": "email@dummy.iam.gserviceaccount.com",
        "client_id": "client_id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/email@dummy.iam.gserviceaccount.com"
    }"""


@patch("notion_task_runner.tasks.backup.google_drive_uploader.build")
@patch("notion_task_runner.tasks.backup.google_drive_uploader.Credentials.from_service_account_info")
def test_upload_success(mock_creds, mock_build, tmp_path, dummy_secret):
    file_path = tmp_path / "export.zip"
    file_path.write_text("dummy content")

    mock_files_create = MagicMock()
    mock_files_create.execute.return_value = {"id": "file-id", "parents": ["root-id"]}
    mock_drive_service = MagicMock()
    mock_drive_service.files.return_value.create.return_value = mock_files_create
    mock_build.return_value = mock_drive_service

    mock_config = MagicMock(spec=TaskConfig)
    mock_config.google_drive_root_folder_id = "some-root-id"
    mock_config.google_drive_service_account_secret_json  = '{"is_json": "true"}'

    uploader = GoogleDriveUploader(mock_config)
    success = uploader.upload(file_path)

    assert success is True
    mock_drive_service.files.return_value.create.assert_called_once()


@patch("notion_task_runner.tasks.backup.google_drive_uploader.build")
@patch("notion_task_runner.tasks.backup.google_drive_uploader.Credentials.from_service_account_info")
def test_upload_file_does_not_exist(mock_creds, mock_build, tmp_path, dummy_secret):
    file_path = tmp_path / "missing.zip"

    mock_config = MagicMock(spec=TaskConfig)
    mock_config.google_drive_root_folder_id = "some-root-id"
    mock_config.google_drive_service_account_secret_json  = '{"is_json": "true"}'

    uploader = GoogleDriveUploader(mock_config)
    assert uploader.upload(file_path) is False


@patch("notion_task_runner.tasks.backup.google_drive_uploader.build")
@patch("notion_task_runner.tasks.backup.google_drive_uploader.Credentials.from_service_account_info")
def test_upload_http_error(mock_creds, mock_build, tmp_path, dummy_secret):
    file_path = tmp_path / "export.zip"
    file_path.write_text("dummy content")

    mock_files_create = MagicMock()
    mock_files_create.execute.side_effect = HttpError(resp=MagicMock(status=500, reason="Server Error"), content=b"fail")
    mock_drive_service = MagicMock()
    mock_drive_service.files.return_value.create.return_value = mock_files_create
    mock_build.return_value = mock_drive_service

    mock_config = MagicMock(spec=TaskConfig)
    mock_config.google_drive_root_folder_id = "some-root-id"
    mock_config.google_drive_service_account_secret_json  = '{"is_json": "true"}'

    uploader = GoogleDriveUploader(mock_config)
    assert uploader.upload(file_path) is False
