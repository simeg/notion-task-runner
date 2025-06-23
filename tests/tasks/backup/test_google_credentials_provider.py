import os
import tempfile
from pathlib import Path
from unittest.mock import patch, ANY

from notion_task_runner.tasks.backup.google_credentials_provider import \
  GoogleCredentialsProvider


def test_get_secret_from_env_var(monkeypatch):
    monkeypatch.setenv(
        GoogleCredentialsProvider.ENV_SECRET_JSON,
        "  {\"type\": \"service_account\"}  "
    )

    result = GoogleCredentialsProvider.get_secret()
    assert result == "{\"type\": \"service_account\"}"


def test_get_secret_from_file(monkeypatch):
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write("  {\"type\": \"service_account\"}  ")
        tmp_path = tmp.name

    monkeypatch.delenv(GoogleCredentialsProvider.ENV_SECRET_JSON, raising=False)
    monkeypatch.setenv(GoogleCredentialsProvider.ENV_SECRET_FILE_PATH, tmp_path)

    result = GoogleCredentialsProvider.get_secret()
    assert result == "{\"type\": \"service_account\"}"

    os.remove(tmp_path)


def test_get_secret_from_file_empty(monkeypatch):
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write("")
        tmp_path = tmp.name

    monkeypatch.delenv(GoogleCredentialsProvider.ENV_SECRET_JSON, raising=False)
    monkeypatch.setenv(GoogleCredentialsProvider.ENV_SECRET_FILE_PATH, tmp_path)

    result = GoogleCredentialsProvider.get_secret()
    assert result is None

    os.remove(tmp_path)


def test_get_secret_file_does_not_exist(monkeypatch):
    fake_path = str(Path(tempfile.gettempdir()) / "nonexistent.json")

    monkeypatch.delenv(GoogleCredentialsProvider.ENV_SECRET_JSON, raising=False)
    monkeypatch.setenv(GoogleCredentialsProvider.ENV_SECRET_FILE_PATH, fake_path)

    result = GoogleCredentialsProvider.get_secret()
    assert result is None


def test_get_secret_returns_none_if_nothing_set(monkeypatch):
    monkeypatch.delenv(GoogleCredentialsProvider.ENV_SECRET_JSON, raising=False)
    monkeypatch.delenv(GoogleCredentialsProvider.ENV_SECRET_FILE_PATH, raising=False)

    result = GoogleCredentialsProvider.get_secret()
    assert result is None


@patch("notion_task_runner.tasks.backup.google_credentials_provider.Path.is_file", return_value=True)
@patch("notion_task_runner.tasks.backup.google_credentials_provider.Path.read_text", side_effect=OSError("Boom"))
def test_get_secret_logs_exception_when_file_read_fails(mock_read_text, mock_is_file, monkeypatch, caplog):
    monkeypatch.delenv(GoogleCredentialsProvider.ENV_SECRET_JSON, raising=False)
    monkeypatch.setenv(GoogleCredentialsProvider.ENV_SECRET_FILE_PATH, "/fake/path.json")

    with caplog.at_level("WARNING"):
        result = GoogleCredentialsProvider.get_secret()

    assert result is None
    assert any("Error reading secret file" in message for message in caplog.messages)