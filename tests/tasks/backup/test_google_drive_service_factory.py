import json
from unittest.mock import MagicMock, patch

from notion_task_runner.tasks.backup.google_drive_service_factory import (
  GoogleDriveServiceFactory,
)


def test_create_returns_service_on_success():
  fake_credentials = {
    "type": "service_account",
    "project_id": "fake-project",
    "private_key_id": "some_key_id",
    "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
    "client_email": "fake@project.iam.gserviceaccount.com",
    "client_id": "fake-client-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fake@project.iam.gserviceaccount.com"
  }

  secret_json = json.dumps(fake_credentials)

  with patch(
      "notion_task_runner.tasks.backup.google_drive_service_factory.build") as mock_build, \
      patch(
          "notion_task_runner.tasks.backup.google_drive_service_factory.service_account.Credentials.from_service_account_info") as mock_creds:
    mock_creds.return_value = MagicMock()
    mock_build.return_value = "mock-service"

    service = GoogleDriveServiceFactory.create(secret_json)

    assert service == "mock-service"
    mock_creds.assert_called_once()
    mock_build.assert_called_once_with("drive", "v3",
                                       credentials=mock_creds.return_value)

def test_create_returns_none_if_secret_empty():
    result = GoogleDriveServiceFactory.create("   ")
    assert result is None


@patch("notion_task_runner.tasks.backup.google_drive_service_factory.log") # Silence logging for cleaner test output
def test_create_returns_none_on_exception(mock_log):
    with patch("notion_task_runner.tasks.backup.google_drive_service_factory.service_account.Credentials.from_service_account_info", side_effect=ValueError("boom")):
        result = GoogleDriveServiceFactory.create("{}")
        assert result is None
    mock_log.error.assert_called_once()
