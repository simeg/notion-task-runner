"""
Base class for Notion page update tasks.

This module provides a common foundation for tasks that update Notion pages
with calculated values from database queries.
"""

from abc import abstractmethod
from datetime import datetime
from typing import Any

from notion_task_runner.constants import (
    DATETIME_FORMAT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_WAIT_SECONDS,
    get_notion_block_update_url,
    get_notion_headers,
)
from notion_task_runner.logging import get_logger
from notion_task_runner.notion import NotionDatabase
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.task import Task
from notion_task_runner.tasks.pas.sum_calculator import SumCalculator
from notion_task_runner.tasks.task_config import TaskConfig
from notion_task_runner.utils.http_client import HTTPClientMixin

log = get_logger(__name__)


class NotionPageUpdateTask(Task, HTTPClientMixin):
    """
    Base class for tasks that update Notion pages with calculated values.

    This class provides common functionality for:
    - Fetching data from Notion databases
    - Calculating totals using SumCalculator
    - Updating callout blocks with formatted results
    - Proper error handling and retry logic

    Subclasses must implement abstract methods to specify:
    - Database and block IDs
    - Column name for calculations
    - Display text formatting
    """

    def __init__(
        self,
        client: AsyncNotionClient,
        db: NotionDatabase,
        config: TaskConfig,
        calculator: SumCalculator,
        block_id: str | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_wait_seconds: int = DEFAULT_RETRY_WAIT_SECONDS,
    ):
        self.client = client
        self.db = db
        self.config = config
        self.calculator = calculator
        self.block_id = block_id or self.get_default_block_id()
        self.max_retries = max_retries
        self.retry_wait_seconds = retry_wait_seconds

    @abstractmethod
    def get_default_block_id(self) -> str:
        """Return the default block ID for this task."""
        pass

    @abstractmethod
    def get_database_id(self) -> str:
        """Return the database ID to query for this task."""
        pass

    @abstractmethod
    def get_column_name(self) -> str:
        """Return the column name to calculate totals for."""
        pass

    @abstractmethod
    def get_display_text(self, total_value: float) -> str:
        """Return the main display text for the given total value."""
        pass

    @abstractmethod
    def get_task_name(self) -> str:
        """Return a human-readable name for this task (used in logging)."""
        pass

    async def run(self) -> None:
        """
        Execute the page update task.

        Fetches data, calculates totals, and updates the Notion page.
        Includes proper error handling and logging.
        """
        task_name = self.get_task_name()
        database_id = self.get_database_id()
        column_name = self.get_column_name()

        try:
            log.info(
                f"Starting {task_name} - fetching data from database {database_id}"
            )

            # Fetch data from database
            rows = await self.db.fetch_rows(database_id)
            log.debug(f"{task_name}: Retrieved {len(rows)} rows from database")

            # Calculate total
            total_value = self.calculator.calculate_total_for_column(rows, column_name)
            log.debug(f"{task_name}: Calculated total {column_name}: {total_value}")

            # Update the page
            await self._update_callout_block(total_value)

            log.info(f"✅ {task_name} completed successfully")

        except Exception as e:
            log.error(f"❌ {task_name} failed: {e}")
            raise

    async def _update_callout_block(self, total_value: float) -> None:
        """
        Update the callout block with the calculated total.

        Args:
            total_value: The calculated total to display

        Raises:
            aiohttp.ClientError: If the API request fails
        """
        now = datetime.now()
        time_and_date_now = now.strftime(DATETIME_FORMAT)

        url = get_notion_block_update_url(self.block_id)
        data = {
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": self.get_display_text(total_value)},
                        "annotations": {"bold": True},
                    },
                    {
                        "type": "text",
                        "text": {"content": f"{total_value}kr"},
                        "annotations": {"bold": False},
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": f" (Senast uppdaterad: {time_and_date_now})"
                        },
                        "annotations": {"italic": True, "color": "gray"},
                    },
                ]
            }
        }

        headers = get_notion_headers(self.config.notion_api_key)

        # Use retry logic for API calls
        await self._retry_update_block(url, data, headers)

    async def _retry_update_block(
        self, url: str, data: dict[str, Any], headers: dict[str, str]
    ) -> None:
        """
        Update block using the HTTP client mixin.

        Args:
            url: The API endpoint URL
            data: The request payload
            headers: The request headers

        Raises:
            aiohttp.ClientError: If all retry attempts fail
        """
        await self._make_notion_request("PATCH", url, headers, data)
