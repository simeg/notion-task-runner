import json
from typing import cast

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient
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

    def __init__(self, client: NotionClient, config: TaskConfig) -> None:
        self.client = client
        self.config = config

    def trigger_export_task(self) -> str | None:
        headers: dict[str, str] = {
            "Cookie": f"{self.TOKEN_V2}={self.config.notion_token_v2}",
            "Content-Type": "application/json",
        }
        response = self.client.post(
            self.ENQUEUE_ENDPOINT, data=self._get_task_json(), headers=headers
        )
        data = response

        if "taskId" not in data:
            log.error(f"Error: {data.get('name')} - {data.get('message')}")
            if data.get("name") == "UnauthorizedError":
                log.error(
                    "Your token is not valid anymore. Try logging in again and updating it."
                )
            return None

        return cast(str, data["taskId"])

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
