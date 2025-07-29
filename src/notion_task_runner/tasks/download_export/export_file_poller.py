import json
from typing import Any

from tenacity import retry, stop_after_attempt, wait_fixed

from notion_task_runner.logging import get_logger
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class NoActivityError(Exception):
    pass


class StaleExportError(Exception):
    pass


class MissingExportLinkError(Exception):
    pass


class MalformedResponseError(Exception):
    pass


class ExportFilePoller:
    """
    Polls the Notion API for a downloadable export URL after triggering an export task.

    This class periodically checks the Notion `getNotificationLogV2` endpoint to retrieve the export link
    associated with a previously enqueued export task. It uses the export trigger timestamp to ensure that
    it only accepts new and relevant export notifications.
    """

    NOTIFICATION_ENDPOINT = "https://www.notion.so/api/v3/getNotificationLogV2"
    TOKEN_V2_KEY = "token_v2"
    DEFAULT_MAX_RETRIES = 500
    DEFAULT_RETRY_WAIT_SECONDS = 5

    def __init__(
        self,
        client: AsyncNotionClient,
        config: TaskConfig,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_wait_seconds: int = DEFAULT_RETRY_WAIT_SECONDS,
    ) -> None:
        self.client = client
        self.config = config
        self.DEFAULT_MAX_RETRIES = max_retries
        self.DEFAULT_RETRY_WAIT_SECONDS = retry_wait_seconds

    async def poll_for_download_url(self, export_trigger_timestamp: int) -> str | None:
        @retry(
            stop=stop_after_attempt(self.DEFAULT_MAX_RETRIES),
            wait=wait_fixed(self.DEFAULT_RETRY_WAIT_SECONDS),
        )
        async def _poll() -> str:
            try:
                return await self._try_get_download_url(export_trigger_timestamp)
            except (
                NoActivityError,
                StaleExportError,
                MissingExportLinkError,
                MalformedResponseError,
            ) as e:
                log.info(str(e))
                raise
            except Exception as e:
                log.error("Error polling download URL", exc_info=e)
                raise

        return await _poll()

    def _get_notification_json(self) -> str:
        return json.dumps(
            {
                "spaceId": self.config.notion_space_id,
                "size": 20,
                "type": "unread_and_read",
                "variant": "no_grouping",
            }
        )

    def _build_headers(self) -> dict[str, str]:
        return {
            "Cookie": f"{self.TOKEN_V2_KEY}={self.config.notion_token_v2}",
            "Content-Type": "application/json",
        }

    def _extract_activity_node(self, response: dict[str, Any]) -> dict[str, Any]:
        activity_map = response.get("recordMap", {}).get("activity")
        if not activity_map:
            raise NoActivityError("Waiting for Notion export to complete...")

        return dict[str, Any](next(iter(activity_map.values()))["value"])

    def _get_export_link(
        self, node: dict[str, Any], export_trigger_timestamp: int
    ) -> str:
        notification_start_timestamp = int(node["start_time"])
        if notification_start_timestamp < export_trigger_timestamp:
            raise StaleExportError(
                "Waiting for fresh Notion backup export notification..."
            )

        export_link = node.get("edits", [{}])[0].get("link")
        if not export_link:
            raise MissingExportLinkError("Download URL not present yet.")

        return str(export_link)

    async def _try_get_download_url(self, export_trigger_timestamp: int) -> str:
        headers = self._build_headers()
        response = await self.client.post(
            self.NOTIFICATION_ENDPOINT,
            headers=headers,
            data=self._get_notification_json(),
        )
        node = self._extract_activity_node(response)
        return self._get_export_link(node, export_trigger_timestamp)
