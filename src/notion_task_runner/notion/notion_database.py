from typing import Any

import aiohttp
from tenacity import retry, stop_after_attempt, wait_fixed

from notion_task_runner.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_WAIT_SECONDS,
    get_notion_database_query_url,
    get_notion_headers,
)
from notion_task_runner.logging import get_logger
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class NotionDatabase:
    """
    Provides methods for querying data from a Notion database using the Notion API.

    This class wraps the API interaction for querying database entries, handling pagination and authentication.
    It relies on a configured AsyncNotionClient and API key provided via TaskConfig.
    """

    def __init__(
        self,
        client: AsyncNotionClient,
        config: TaskConfig,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_wait_seconds: int = DEFAULT_RETRY_WAIT_SECONDS,
    ) -> None:
        self.client = client
        self.config = config
        self.max_retries = max_retries
        self.retry_wait_seconds = retry_wait_seconds

    async def fetch_rows(self, database_id: str | None = None) -> list[dict[str, Any]]:
        """
        Fetch all rows from a Notion database with pagination support.

        Args:
            database_id: The ID of the database to query

        Returns:
            List of database row dictionaries

        Raises:
            ValueError: If database_id is not provided
            aiohttp.ClientError: If the API request fails
        """
        if not database_id:
            raise ValueError("No database ID provided.")

        log.debug(f"Fetching rows from database: {database_id}")

        url = get_notion_database_query_url(database_id)
        all_results = []
        next_cursor = None

        while True:
            payload = self._build_payload(next_cursor)
            data = await self._retry_fetch_rows(url, payload)

            if data.get("status", 200) != 200:
                raise aiohttp.ClientError(
                    f"Failed to fetch data from {database_id}, got: {data['status']} {data['message']}"
                )

            batch_size = len(data["results"])
            all_results.extend(data["results"])
            log.debug(f"Fetched {batch_size} rows (total: {len(all_results)})")

            next_cursor = data.get("next_cursor")
            if not next_cursor:
                break

        log.debug(
            f"Completed fetching {len(all_results)} total rows from database {database_id}"
        )
        return all_results

    async def _retry_fetch_rows(
        self, url: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_fixed(self.retry_wait_seconds),
        )
        async def _do_request() -> dict[str, Any]:
            return await self.client.post(
                url, headers=self._build_headers(), json=payload
            )

        return await _do_request()

    def _build_headers(self) -> dict[str, str]:
        return get_notion_headers(self.config.notion_api_key)

    def _build_payload(self, next_cursor: str | None) -> dict[str, Any]:
        return {"start_cursor": next_cursor} if next_cursor else {}
