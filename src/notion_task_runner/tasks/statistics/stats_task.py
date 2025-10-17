import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp

from notion_task_runner.constants import (
    DATETIME_FORMAT,
    get_notion_block_update_url,
    get_notion_database_query_url,
    get_notion_headers,
)
from notion_task_runner.logging import get_logger
from notion_task_runner.notion import NotionDatabase
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.task import Task
from notion_task_runner.tasks.statistics.stats_fetcher import (
    DetailedWorkspaceStats,
    StatsFetcher,
)
from notion_task_runner.tasks.task_config import TaskConfig
from notion_task_runner.utils.http_client import HTTPClientMixin

log = get_logger(__name__)

"""

22eaa18d-640d-80cb-96a9-c634a1175591 column_list <-- main column

22eaa18d-640d-802c-8244-d52c5d91e4ed left column
22eaa18d-640d-8030-b346-cd39912d160b right column

22eaa18d-640d-80a4-ab34-f5f36679e772 child_database
22eaa18d-640d-805e-99c0-ea4335f3ebc9 divider
22eaa18d-640d-80cf-a3e1-c195a31f5ce8 child_database <-- This is the stats database ID
22eaa18d-640d-80c3-978a-e7f7d548f42e child_database <-- backup db
22eaa18d-640d-80b5-a815-daa58331c9f8 paragraph
"""


@dataclass
class RowIdAndTitle:
    id: str
    title: str


class StatsTask(Task, HTTPClientMixin):
    STATS_DB_ID = "22eaa18d-640d-80cf-a3e1-c195a31f5ce8"

    def __init__(
        self, client: AsyncNotionClient, db: NotionDatabase, config: TaskConfig
    ) -> None:
        self.client = client
        self.db = db
        self.config = config

    async def run(self) -> None:
        """
        Execute the statistics update task.

        Fetches workspace statistics and updates the stats database
        with current counts and metrics.
        """
        try:
            log.info("Starting Stats Task - fetching workspace statistics")

            fetcher = StatsFetcher(self.db)
            stats: DetailedWorkspaceStats = await fetcher.fetch()

            log.debug(
                f"Fetched stats: watches={len(stats.watches)}, adapters={len(stats.adapters)}, "
                f"cables={len(stats.cables)}, prylar={len(stats.prylar)}, vinyls={len(stats.vinyls)}"
            )

            rows_and_titles: list[RowIdAndTitle] = await self._get_row_and_title(
                self.STATS_DB_ID, str(self.config.notion_api_key)
            )

            row_lookup = {
                "Klockor": len(stats.watches),
                "Adaptrar": len(stats.adapters),
                "Kablar": len(stats.cables),
                "Prylar": len(stats.prylar),
                "Vinyler": len(stats.vinyls),
                "Total Kabellängd (m)": stats.total_cable_length_m,
            }

            failed_updates: list[tuple[str, Exception]] = []

            # Update stats in parallel using asyncio
            tasks = [self._update_last_updated_text()]
            for title, value in row_lookup.items():
                try:
                    row_id = self._get_row_id_by_title(title, rows_and_titles)
                    tasks.append(self._update_row_property(row_id, value))
                except ValueError as e:
                    log.error(f"Failed to find row for '{title}': {e}")
                    failed_updates.append((title, e))

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    log.error(f"Error updating task {i}: {result}")
                    failed_updates.append(("unknown", result))

            if failed_updates:
                error_msg = f"Failed to update {len(failed_updates)} stat(s)"
                log.error(error_msg)
                for item, error in failed_updates:
                    log.error(f"  - {item}: {error}")
                raise RuntimeError(error_msg)

            log.info("✅ Stats Task completed successfully")

        except Exception as e:
            log.error(f"❌ Stats Task failed: {e}")
            raise

    @staticmethod
    async def _get_row_and_title(database_id: str, token: str) -> list[RowIdAndTitle]:
        """Fetch all rows and their titles from the stats database."""
        url = get_notion_database_query_url(database_id)
        headers = get_notion_headers(token)

        page_ids_and_title = []
        has_more = True
        next_cursor = None

        async with aiohttp.ClientSession() as session:
            while has_more:
                payload: dict[str, Any | None] | dict[Any, Any] = (
                    {"start_cursor": next_cursor} if next_cursor else {}
                )
                async with session.post(url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()

                    for row in data["results"]:
                        row_id = row["id"]
                        sak_title = row["properties"]["Sak"]["title"][0]["text"][
                            "content"
                        ]
                        page_ids_and_title.append(
                            RowIdAndTitle(id=row_id, title=sak_title)
                        )

                    has_more = data.get("has_more", False)
                    next_cursor = data.get("next_cursor")

        return page_ids_and_title

    async def _update_row_property(
        self, page_id: str, new_value: Any, column_name: str = "Antal"
    ) -> None:
        """Update a number property in a database row."""
        url = f"https://api.notion.com/v1/pages/{page_id}"
        headers = get_notion_headers(self.config.notion_api_key)
        data = {"properties": {column_name: {"number": float(new_value)}}}

        await self._make_notion_request("PATCH", url, headers, data)

    async def _update_last_updated_text(self) -> None:
        """Update the 'last updated' timestamp on the stats page."""
        now = datetime.now(ZoneInfo("Europe/Stockholm"))
        time_and_date_now = now.strftime(DATETIME_FORMAT)

        block_id = "233aa18d-640d-80a5-987d-d6a98f96a8d0"
        url = get_notion_block_update_url(block_id)
        headers = get_notion_headers(self.config.notion_api_key)

        data = {
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"(Senast uppdaterad: {time_and_date_now})"
                        },
                        "annotations": {"italic": True, "color": "gray"},
                    },
                ]
            }
        }

        await self._make_notion_request("PATCH", url, headers, data)

    @staticmethod
    def _get_row_id_by_title(title: str, rows: list[RowIdAndTitle]) -> str:
        for row in rows:
            if row.title.strip().lower() == title.strip().lower():
                return row.id
        raise ValueError(f"Row with title '{title}' not found.")
