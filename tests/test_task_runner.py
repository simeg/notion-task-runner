import pytest
from unittest.mock import MagicMock, patch

from notion_task_runner.task_runner import TaskRunner
from notion_task_runner.tasks.task_config import TaskConfig
from notion_task_runner.notion import NotionClient

@pytest.fixture
def mock_config():
    return MagicMock(spec=TaskConfig)

@pytest.fixture
def mock_client():
    return MagicMock(spec=NotionClient)

@patch("notion_task_runner.task_runner.PrylarkivPageTask")
@patch("notion_task_runner.task_runner.PASPageTask")
def test_task_runner_runs_all_tasks(
    mock_pas_task, mock_prylarkiv_task, mock_client, mock_config
):
    # Arrange
    mock_pas_instance = MagicMock()
    mock_prylarkiv_instance = MagicMock()

    mock_pas_task.return_value = mock_pas_instance
    mock_prylarkiv_task.return_value = mock_prylarkiv_instance

    # Act
    runner = TaskRunner(mock_client, mock_config)
    runner.run()

    # Assert
    mock_pas_instance.run.assert_called_once()
    mock_prylarkiv_instance.run.assert_called_once()

@patch("notion_task_runner.task_runner.PrylarkivPageTask")
@patch("notion_task_runner.task_runner.PASPageTask")
def test_task_runner_handles_exceptions_gracefully(
    mock_pas_task, mock_prylarkiv_task,  mock_client, mock_config
):
    # Arrange
    mock_pas_instance = MagicMock()
    mock_pas_instance.run.side_effect = Exception("PAS failed")

    mock_prylarkiv_instance = MagicMock()

    mock_pas_task.return_value = mock_pas_instance
    mock_prylarkiv_task.return_value = mock_prylarkiv_instance

    # Act
    runner = TaskRunner(mock_client, mock_config)
    runner.run()

    # Assert: remaining tasks still run
    mock_prylarkiv_instance.run.assert_called_once()