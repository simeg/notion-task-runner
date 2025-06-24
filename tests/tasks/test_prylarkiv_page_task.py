import pytest
from unittest.mock import MagicMock
from notion_task_runner.tasks.prylarkiv_page_task import PrylarkivPageTask
from notion_task_runner.tasks.task_config import TaskConfig


@pytest.fixture
def mock_config():
    config = MagicMock(spec=TaskConfig)
    config.notion_api_key = "fake-key"
    return config


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.patch.return_value.status_code = 200
    return client


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.fetch_rows.return_value = [{} for _ in range(5)]  # simulate 5 entries
    return db


def test_run_updates_block_successfully(mock_client, mock_db, mock_config):
    task = PrylarkivPageTask(client=mock_client, db=mock_db, config=mock_config)
    task.run()

    expected_url = f"https://api.notion.com/v1/blocks/{task.BLOCK_ID}"
    expected_content = {
        "callout": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": "Nästa nummer på pryl: "},
                    "annotations": {"bold": True},
                },
                {
                    "type": "text",
                    "text": {"content": "6"},
                    "annotations": {"code": True},
                },
            ]
        }
    }

    mock_client.patch.assert_called_once_with(
        expected_url,
        json=expected_content,
        headers={
            "Authorization": f"Bearer {mock_config.notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
    )


def test_run_logs_failure_on_bad_response(mock_client, mock_db, mock_config, caplog):
    mock_client.patch.return_value.status_code = 500
    task = PrylarkivPageTask(client=mock_client, db=mock_db, config=mock_config)

    with caplog.at_level("INFO"):
        task.run()

    assert "❌ Failed to update Prylarkiv." in caplog.text