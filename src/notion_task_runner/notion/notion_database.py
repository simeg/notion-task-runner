from typing import Any

from requests import HTTPError
from tenacity import retry, stop_after_attempt, wait_fixed

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

    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_WAIT_SECONDS = 2

    def __init__(
        self,
        client: NotionClient,
        config: TaskConfig,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_wait_seconds: int = DEFAULT_RETRY_WAIT_SECONDS,
    ) -> None:
        self.client = client
        self.config = config
        self.max_retries = max_retries
        self.retry_wait_seconds = retry_wait_seconds

    def fetch_rows(self, database_id: str | None = None) -> list[dict[str, Any]]:
        if not database_id:
            raise ValueError("No database ID provided.")

        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        all_results = []
        next_cursor = None

        while True:
            payload = self._build_payload(next_cursor)
            data = self._retry_fetch_rows(url, payload)

            if data.get("status", 200) != 200:
                raise HTTPError(
                    f"Failed to fetch data, instead got: {data['status']} {data['message']}"
                )

            all_results.extend(data["results"])
            next_cursor = data.get("next_cursor")
            if not next_cursor:
                break

        return all_results

    def _retry_fetch_rows(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_fixed(self.retry_wait_seconds),
        )
        def _do_request() -> dict[str, Any]:
            return self.client.post(url, headers=self._build_headers(), json=payload)

        return _do_request()

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def _build_payload(self, next_cursor: str | None) -> dict[str, Any]:
        return {"start_cursor": next_cursor} if next_cursor else {}
