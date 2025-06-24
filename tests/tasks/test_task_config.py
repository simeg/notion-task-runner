import os
import pytest
from unittest.mock import patch

from notion_task_runner.tasks.task_config import TaskConfig, DEFAULT_EXPORT_DIR


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


@patch.dict(os.environ, {}, clear=True)
def test_task_config_missing_required_env_vars():
    with pytest.raises(SystemExit):
        TaskConfig.from_env()


def test_config_download_export_task_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("DOWNLOADS_DIRECTORY_PATH", raising=False)
    monkeypatch.delenv("EXPORT_TYPE", raising=False)
    monkeypatch.delenv("FLATTEN_EXPORT_FILE_TREE", raising=False)

    monkeypatch.chdir(tmp_path)

    downloads_path, export_type, flatten, _ = TaskConfig._config_download_export_task()

    assert downloads_path == (tmp_path / DEFAULT_EXPORT_DIR).resolve()
    assert export_type == "markdown"
    assert flatten is False


def test_config_download_export_task_invalid_export_type(monkeypatch):
    monkeypatch.setenv("EXPORT_TYPE", "pdf")  # Invalid type

    with pytest.raises(SystemExit):
        TaskConfig._config_download_export_task()