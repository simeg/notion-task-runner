import os
import pytest
from notion_task_runner.tasks.task_config import TaskConfig


def set_env(**kwargs):
    for key, value in kwargs.items():
        os.environ[key] = value


def clear_env(*keys):
    for key in keys:
        os.environ.pop(key, None)


def test_from_env_success(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTION_API_KEY", "fake-api-key")
    monkeypatch.setenv("NOTION_SPACE_ID", "fake-space-id")
    monkeypatch.setenv("NOTION_TOKEN_V2", "fake-token")
    monkeypatch.setenv("EXPORT_TYPE", "markdown")
    monkeypatch.setenv("FLATTEN_EXPORT_FILE_TREE", "True")
    monkeypatch.setenv("DOWNLOADS_DIRECTORY_PATH", str(tmp_path))

    config = TaskConfig.from_env()

    assert config.notion_api_key == "fake-api-key"
    assert config.notion_space_id == "fake-space-id"
    assert config.notion_token_v2 == "fake-token"
    assert config.export_type == "markdown"
    assert config.flatten_export_file_tree is True
    assert config.downloads_directory_path == tmp_path


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    monkeypatch.setenv("NOTION_SPACE_ID", "fake-space-id")
    monkeypatch.setenv("NOTION_TOKEN_V2", "fake-token")

    with pytest.raises(SystemExit):
        TaskConfig.from_env()


def test_missing_space_id_or_token(monkeypatch):
    monkeypatch.setenv("NOTION_API_KEY", "fake-api-key")
    monkeypatch.delenv("NOTION_SPACE_ID", raising=False)
    monkeypatch.setenv("NOTION_TOKEN_V2", "fake-token")

    with pytest.raises(SystemExit):
        TaskConfig.from_env()

    monkeypatch.setenv("NOTION_SPACE_ID", "fake-space-id")
    monkeypatch.delenv("NOTION_TOKEN_V2", raising=False)

    with pytest.raises(SystemExit):
        TaskConfig.from_env()


@pytest.mark.parametrize("invalid_export_type", ["pdf", "json", "doc"])
def test_invalid_export_type(monkeypatch, invalid_export_type):
    monkeypatch.setenv("NOTION_API_KEY", "fake-api-key")
    monkeypatch.setenv("NOTION_SPACE_ID", "fake-space-id")
    monkeypatch.setenv("NOTION_TOKEN_V2", "fake-token")
    monkeypatch.setenv("EXPORT_TYPE", invalid_export_type)

    with pytest.raises(SystemExit):
        TaskConfig.from_env()


def test_default_download_dir_created(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTION_API_KEY", "fake-api-key")
    monkeypatch.setenv("NOTION_SPACE_ID", "fake-space-id")
    monkeypatch.setenv("NOTION_TOKEN_V2", "fake-token")
    monkeypatch.setenv("DOWNLOADS_DIRECTORY_PATH", str(tmp_path))

    config = TaskConfig.from_env()

    assert config.downloads_directory_path.exists()
    assert config.downloads_directory_path.is_dir()