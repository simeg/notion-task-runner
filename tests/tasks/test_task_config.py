import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from notion_task_runner.tasks.task_config import DEFAULT_EXPORT_DIR, TaskConfig


@patch.dict(os.environ, {
    "NOTION_SPACE_ID": "space-id",
    "NOTION_TOKEN_V2": "token-v2",
    "NOTION_API_KEY": "api-key",
    "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON": '{"type": "service_account"}',
    "GOOGLE_DRIVE_ROOT_FOLDER_ID": "root-folder-id",
})
def test_task_config_from_env_valid(monkeypatch, tmp_path):
    monkeypatch.setenv("DOWNLOADS_DIRECTORY_PATH", str(tmp_path))
    monkeypatch.setenv("EXPORT_TYPE", "markdown")
    monkeypatch.setenv("FLATTEN_EXPORT_FILE_TREE", "true")

    config = TaskConfig.from_env()

    assert config.notion_space_id == "space-id"
    assert config.notion_token_v2 == "token-v2"
    assert config.notion_api_key == "api-key"
    assert config.google_drive_root_folder_id == "root-folder-id"
    assert config.google_drive_service_account_secret_json == '{"type": "service_account"}'
    assert config.downloads_directory_path == tmp_path.resolve()
    assert config.export_type == "markdown"
    assert config.flatten_export_file_tree is True


def test_task_config_missing_required_env_vars(monkeypatch, tmp_path):
    # Create an empty .env file to override the default one
    env_file = tmp_path / ".env"
    env_file.write_text("")

    # Change to temp directory so it loads the empty .env file
    monkeypatch.chdir(tmp_path)

    # Explicitly remove all required environment variables
    monkeypatch.delenv("NOTION_SPACE_ID", raising=False)
    monkeypatch.delenv("NOTION_TOKEN_V2", raising=False)
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_DRIVE_ROOT_FOLDER_ID", raising=False)

    with pytest.raises(ValidationError):
        TaskConfig()


@patch.dict(os.environ, {
    "NOTION_SPACE_ID": "space-id",
    "NOTION_TOKEN_V2": "token-v2",
    "NOTION_API_KEY": "api-key",
    "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON": '{"type": "service_account"}',
    "GOOGLE_DRIVE_ROOT_FOLDER_ID": "root-folder-id",
})
def test_config_download_export_task_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("DOWNLOADS_DIRECTORY_PATH", raising=False)
    monkeypatch.delenv("EXPORT_TYPE", raising=False)
    monkeypatch.delenv("FLATTEN_EXPORT_FILE_TREE", raising=False)

    monkeypatch.chdir(tmp_path)

    config = TaskConfig()

    assert config.downloads_directory_path == (tmp_path / DEFAULT_EXPORT_DIR).resolve()
    assert config.export_type == "markdown"
    assert config.flatten_export_file_tree is False


@patch.dict(os.environ, {
    "NOTION_SPACE_ID": "space-id",
    "NOTION_TOKEN_V2": "token-v2",
    "NOTION_API_KEY": "api-key",
    "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON": '{"type": "service_account"}',
    "GOOGLE_DRIVE_ROOT_FOLDER_ID": "root-folder-id",
    "EXPORT_TYPE": "pdf",  # Invalid type
})
def test_config_download_export_task_invalid_export_type():
    with pytest.raises(ValidationError):
        TaskConfig()
