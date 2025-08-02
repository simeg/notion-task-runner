"""
Integration tests for the Notion Task Runner.

These tests verify that the complete system works together properly,
including configuration, client setup, and task execution.
"""

import os
from unittest.mock import Mock, patch

import pytest

from notion_task_runner.notion import NotionDatabase
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.task_runner import TaskRunner
from notion_task_runner.tasks.task_config import TaskConfig


class TestIntegration:
    """Integration tests for the full task runner system."""

    @patch.dict(os.environ, {
        "IS_PROD": "false",
        "NOTION_SPACE_ID": "test-space-id",
        "NOTION_TOKEN_V2": "test-token-v2",
        "NOTION_API_KEY": "test-api-key",
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON": "test-service-account",
        "GOOGLE_DRIVE_ROOT_FOLDER_ID": "test-folder-id",
    })
    def test_task_config_from_env_success(self):
        """Test that TaskConfig can be loaded from environment variables."""
        config = TaskConfig.from_env()

        assert config.is_prod is False
        assert config.notion_space_id == "test-space-id"
        assert config.notion_token_v2 == "test-token-v2"
        assert config.notion_api_key == "test-api-key"
        assert config.google_drive_service_account_secret_json == "test-service-account"
        assert config.google_drive_root_folder_id == "test-folder-id"

    @patch.dict(os.environ, {
        "IS_PROD": "false",
        "NOTION_SPACE_ID": "test-space-id",
        "NOTION_TOKEN_V2": "test-token-v2",
        "NOTION_API_KEY": "test-api-key",
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON": "test-service-account",
        "GOOGLE_DRIVE_ROOT_FOLDER_ID": "test-folder-id",
    })
    @patch('requests.get')
    def test_task_config_validate_connectivity_success(self, mock_get):
        """Test that notion connectivity validation works."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        config = TaskConfig.from_env()
        assert config.validate_notion_connectivity() is True

    @patch.dict(os.environ, {
        "IS_PROD": "false",
        "NOTION_SPACE_ID": "test-space-id",
        "NOTION_TOKEN_V2": "test-token-v2",
        "NOTION_API_KEY": "test-api-key",
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON": "test-service-account",
        "GOOGLE_DRIVE_ROOT_FOLDER_ID": "test-folder-id",
    })
    @patch('requests.get')
    def test_task_config_validate_connectivity_failure(self, mock_get):
        """Test that notion connectivity validation handles failures."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        config = TaskConfig.from_env()
        assert config.validate_notion_connectivity() is False

    @patch.dict(os.environ, {
        "IS_PROD": "false",
        "NOTION_SPACE_ID": "test-space-id",
        "NOTION_TOKEN_V2": "test-token-v2",
        "NOTION_API_KEY": "test-api-key",
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON": "test-service-account",
        "GOOGLE_DRIVE_ROOT_FOLDER_ID": "test-folder-id",
    })
    @patch('aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_async_notion_client_initialization(self, mock_session_class):
        """Test that AsyncNotionClient can be initialized with config."""
        # Reset singleton before test
        await AsyncNotionClient.reset_singleton()

        mock_session = Mock()
        mock_session_class.return_value = mock_session

        config = TaskConfig.from_env()
        client = AsyncNotionClient(config)

        assert client.config == config

    def test_task_runner_initialization_validation_failure(self):
        """Test that TaskRunner fails if Notion validation fails."""
        mock_config = Mock()
        mock_config.validate_notion_connectivity.return_value = False
        mock_config.is_prod = False

        tasks = []  # Empty task list for testing

        with pytest.raises(RuntimeError, match="Notion API validation failed"):
            TaskRunner(tasks=tasks, config=mock_config)

    @patch.dict(os.environ, {
        "IS_PROD": "false",
        "NOTION_SPACE_ID": "test-space-id",
        "NOTION_TOKEN_V2": "test-token-v2",
        "NOTION_API_KEY": "test-api-key",
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON": "test-service-account",
        "GOOGLE_DRIVE_ROOT_FOLDER_ID": "test-folder-id",
    })
    @patch('requests.get')
    @patch('aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_notion_database_initialization(self, mock_session_class, mock_get):
        """Test that NotionDatabase can be initialized."""
        # Reset singleton before test
        await AsyncNotionClient.reset_singleton()

        # Mock connectivity validation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Mock client session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        config = TaskConfig.from_env()
        client = AsyncNotionClient(config)
        database = NotionDatabase(client, config)

        assert database.client == client
        assert database.config == config
        assert database.max_retries == 3
        assert database.retry_wait_seconds == 2

    @patch.dict(os.environ, {
        "IS_PROD": "false",
        "NOTION_SPACE_ID": "test-space-id",
        "NOTION_TOKEN_V2": "test-token-v2",
        "NOTION_API_KEY": "test-api-key",
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON": "test-service-account",
        "GOOGLE_DRIVE_ROOT_FOLDER_ID": "test-folder-id",
    })
    @patch('aiohttp.ClientSession')
    @pytest.mark.asyncio
    async def test_async_notion_client_singleton_behavior(self, mock_session_class):
        """Test that AsyncNotionClient behaves as a singleton."""
        # Reset singleton before test
        await AsyncNotionClient.reset_singleton()

        mock_session = Mock()
        mock_session_class.return_value = mock_session

        config = TaskConfig.from_env()

        # Create first instance
        client1 = AsyncNotionClient(config)

        # Create second instance - should be the same object
        client2 = AsyncNotionClient()

        # Both should be the exact same instance
        assert client1 is client2
        assert id(client1) == id(client2)
