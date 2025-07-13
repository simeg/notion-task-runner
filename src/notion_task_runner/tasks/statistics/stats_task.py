import concurrent.futures
from dataclasses import dataclass
from typing import Any

import requests

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient, NotionDatabase
from notion_task_runner.task import Task
from notion_task_runner.tasks.statistics.stats_fetcher import (
    StatsFetcher,
    WorkspaceStats,
)
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)

"""
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


class StatsTask(Task):
    STATS_DB_ID = "22eaa18d-640d-80cf-a3e1-c195a31f5ce8"

    def __init__(
        self, client: NotionClient, db: NotionDatabase, config: TaskConfig
    ) -> None:
        self.client = client
        self.db = db
        self.config = config

    def run(self) -> None:
        fetcher = StatsFetcher(self.db)
        stats: WorkspaceStats = fetcher.fetch()

        rows_and_titles: list[RowIdAndTitle] = self._get_row_and_title(
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

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for title, value in row_lookup.items():
                row_id = self._get_row_id_by_title(title, rows_and_titles)
                futures.append(
                    executor.submit(self._update_row_property, row_id, value)
                )

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    log.error(f"Error updating row: {e}")

        log.info("✅ Updated Stats database with new values.")

    @staticmethod
    def _get_row_and_title(database_id: str, token: str) -> list[RowIdAndTitle]:
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        page_ids_and_title = []
        has_more = True
        next_cursor = None

        while has_more:
            payload: dict[str, Any | None] | dict[Any, Any] = (
                {"start_cursor": next_cursor} if next_cursor else {}
            )
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            for row in data["results"]:
                row_id = row["id"]
                sak_title = row["properties"]["Sak"]["title"][0]["text"]["content"]
                page_ids_and_title.append(RowIdAndTitle(id=row_id, title=sak_title))

            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")

        return page_ids_and_title

    def _update_row_property(
        self, page_id: str, new_value: Any, column_name: str = "Antal"
    ) -> Any:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        headers = {
            "Authorization": f"Bearer {self.config.notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        data = {"properties": {column_name: {"number": float(new_value)}}}

        response = requests.patch(url, headers=headers, json=data)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            log.error(f"HTTP Error: {e.response.status_code} {e.response.text}")
            raise
        return response.json()

    @staticmethod
    def _get_row_id_by_title(title: str, rows: list[RowIdAndTitle]) -> str:
        for row in rows:
            if row.title.strip().lower() == title.strip().lower():
                return row.id
        raise ValueError(f"Row with title '{title}' not found.")
