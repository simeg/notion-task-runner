"""
Test helper functions and utilities.

This module contains common test helpers that are used across multiple test files.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from tests.conftest import TEST_API_KEY, TEST_SPACE_ID


@contextmanager
def mock_notion_client_creation(config=None):
    """
    Context manager for creating mock AsyncNotionClient instances.

    This helper reduces the boilerplate of patching the AsyncNotionClient
    constructor and validation in tests.

    Args:
        config: Optional config to use. If None, creates a default mock config.

    Yields:
        AsyncNotionClient: A mock client instance
    """
    if config is None:
        config = MagicMock()
        config.notion_api_key = TEST_API_KEY
        config.notion_space_id = TEST_SPACE_ID

    with (patch.object(AsyncNotionClient, '__new__', return_value=object.__new__(AsyncNotionClient)),
          patch.object(AsyncNotionClient, '_validate_config')):
        client = AsyncNotionClient(config)
        client.config = config
        yield client


def create_mock_database_rows(count: int = 2, column_name: str = "Slutpris", base_value: int = 10):
    """
    Create mock database rows for testing.

    Args:
        count: Number of rows to create
        column_name: Name of the column containing numeric values
        base_value: Base value for calculations (rows will have base_value * index)

    Returns:
        List of mock database row dictionaries
    """
    return [
        {"properties": {column_name: {"number": base_value * (i + 1)}}}
        for i in range(count)
    ]


def create_mock_config(**overrides):
    """
    Create a mock TaskConfig with sensible defaults.

    Args:
        **overrides: Any config attributes to override

    Returns:
        MagicMock: A mock config object
    """
    config = MagicMock()
    config.notion_api_key = TEST_API_KEY
    config.notion_space_id = TEST_SPACE_ID
    config.validate_notion_connectivity.return_value = True

    # Apply any overrides
    for key, value in overrides.items():
        setattr(config, key, value)

    return config
