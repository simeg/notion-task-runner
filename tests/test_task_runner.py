import pytest
import asyncio
from unittest.mock import MagicMock, patch

from notion_task_runner.task_runner import TaskRunner
from notion_task_runner.tasks.task_config import TaskConfig
from notion_task_runner.notion.async_notion_client import AsyncNotionClient

@pytest.fixture
def mock_config():
    return MagicMock(spec=TaskConfig)

@pytest.fixture
def mock_client():
    return MagicMock(spec=AsyncNotionClient)

@pytest.mark.asyncio
async def test_task_runner_runs_all_tasks(mock_config):
    from unittest.mock import AsyncMock
    
    # Arrange
    mock_task1 = MagicMock()
    mock_task1.run = AsyncMock()
    mock_task2 = MagicMock()
    mock_task2.run = AsyncMock()
    tasks = [mock_task1, mock_task2]

    # Mock the config's validate_notion_connectivity method and is_prod attribute
    mock_config.validate_notion_connectivity.return_value = True
    mock_config.is_prod = False

    # Act
    runner = TaskRunner(tasks=tasks, config=mock_config)
    await runner.run_async()

    # Assert
    mock_task1.run.assert_called_once()
    mock_task2.run.assert_called_once()

@pytest.mark.asyncio
async def test_task_runner_handles_exceptions_gracefully(mock_config):
    from unittest.mock import AsyncMock
    
    # Arrange
    mock_task1 = MagicMock()
    mock_task1.run = AsyncMock(side_effect=Exception("Task 1 failed"))

    mock_task2 = MagicMock()
    mock_task2.run = AsyncMock()
    tasks = [mock_task1, mock_task2]

    # Mock the config's validate_notion_connectivity method and is_prod attribute
    mock_config.validate_notion_connectivity.return_value = True
    mock_config.is_prod = False

    # Act
    runner = TaskRunner(tasks=tasks, config=mock_config)
    await runner.run_async()

    # Assert: remaining tasks still run even if one fails
    mock_task1.run.assert_called_once()
    mock_task2.run.assert_called_once()