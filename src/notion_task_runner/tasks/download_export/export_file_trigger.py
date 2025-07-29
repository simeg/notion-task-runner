import json
from typing import cast

from tenacity import retry, stop_after_attempt, wait_fixed

from notion_task_runner.logging import get_logger
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class ExportFileTrigger:
    """
    Triggers a Notion export task by enqueuing a request to the Notion API.

    This class builds and sends an export request to the Notion `enqueueTask` endpoint.
    It supports configuring export type, structure, timezone, and locale based on the provided TaskConfig.
    On success, it returns the task ID that can be used to track export progress.
    """

    ENQUEUE_ENDPOINT = "https://www.notion.so/api/v3/enqueueTask"
    TOKEN_V2 = "token_v2"

    def __init__(
        self,
        client: AsyncNotionClient,
        config: TaskConfig,
        max_retries: int = 3,
        retry_wait_seconds: int = 2,
    ) -> None:
        self.client = client
        self.config = config
        self.max_retries = max_retries
        self.retry_wait_seconds = retry_wait_seconds

    async def trigger_export_task(self) -> str | None:
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_fixed(self.retry_wait_seconds),
            reraise=True,
        )
        async def _do_trigger() -> str | None:
            headers: dict[str, str] = {
                "Cookie": f"{self.TOKEN_V2}={self.config.notion_token_v2}",
                "Content-Type": "application/json",
            }
            response = await self.client.post(
                self.ENQUEUE_ENDPOINT, data=self._get_task_json(), headers=headers
            )

            if "taskId" not in response:
                log.error(f"Error: {response.get('name')} - {response.get('message')}")
                if response.get("name") == "UnauthorizedError":
                    log.error(
                        "Your token is not valid anymore. Try logging in again and updating it."
                    )
                return None

            return cast(str, response["taskId"])

        return await _do_trigger()

    def _get_task_json(self) -> str:
        return json.dumps(
            {
                "task": {
                    "eventName": "exportSpace",
                    "request": {
                        "spaceId": self.config.notion_space_id,
                        "shouldExportComments": False,
                        "exportOptions": {
                            "exportType": self.config.export_type.lower(),
                            "flattenExportFiletree": self.config.flatten_export_file_tree,
                            "timeZone": "Europe/Stockholm",
                            "locale": "en",
                        },
                    },
                }
            }
        )
