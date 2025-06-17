from typing import Any

from requests import HTTPError

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class NotionDatabase:
    """
    Provides methods for querying data from a Notion database using the Notion API.

    This class wraps the API interaction for querying database entries, handling pagination and authentication.
    It relies on a configured NotionClient and API key provided via TaskConfig.
    """

    def __init__(self, client: NotionClient, config: TaskConfig) -> None:
        self.client = client
        self.config = config

    def get_entries(self, database_id: str | None = None) -> list[dict[str, Any]]:
        if not database_id:
            raise ValueError("No database ID provided.")

        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        all_results = []
        next_cursor = None

        while True:
            payload: dict[str, str] | dict[str, Any] = (
                {"start_cursor": next_cursor} if next_cursor else {}
            )
            headers: dict[str, str] = {
                "Authorization": f"Bearer {self.config.notion_api_key}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            }
            data = self.client.post(url, headers=headers, json=payload)

            if data.get("status", 200) != 200:
                raise HTTPError(
                    f"Failed to fetch data, instead got: {data['status']} {data['message']}"
                )

            all_results.extend(data["results"])
            next_cursor = data.get("next_cursor")
            if not next_cursor:
                break

        return all_results
