import json
import time

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class ExportFilePoller:
    """
    Polls the Notion API for a downloadable export URL after triggering an export task.

    This class periodically checks the Notion `getNotificationLogV2` endpoint to retrieve the export link
    associated with a previously enqueued export task. It uses the export trigger timestamp to ensure that
    it only accepts new and relevant export notifications.
    """

    NOTIFICATION_ENDPOINT = "https://www.notion.so/api/v3/getNotificationLogV2"
    TOKEN_V2 = "token_v2"
    FETCH_DOWNLOAD_URL_RETRY_SECONDS = 5

    def __init__(self, client: NotionClient, config: TaskConfig):
        self.client = client
        self.config = config

    def poll_for_download_url(self, export_trigger_timestamp: int) -> str | None:

        # return "https://file.notion.so/f/t/fc0f29e2-8805-4aa4-84a1-cebae4623370/Export-11f38aa4-6901-4ade-bb4f-d4c062fe8809.zip?table=user_export&id=216d872b-594c-8102-9933-005d0857e033&spaceId=&expirationTimestamp=1750880316806&signature=LPCp0JP_ilqUDWvqgMBxMmmkhX1PtRQXpnioUAti2Ts&download=true&downloadName=fc0f29e2-8805-4aa4-84a1-cebae4623370%2FExport-11f38aa4-6901-4ade-bb4f-d4c062fe8809.zip"

        headers = {
            "Cookie": f"{self.TOKEN_V2}={self.config.notion_token_v2}",
            "Content-Type": "application/json",
        }

        for _ in range(500):
            time.sleep(self.FETCH_DOWNLOAD_URL_RETRY_SECONDS)

            response = self.client.post(
                self.NOTIFICATION_ENDPOINT,
                headers=headers,
                data=self._get_notification_json(),
            )

            try:
                data = response
                record_map = data.get("recordMap", {})
                activity_map = record_map.get("activity")

                if not activity_map:
                    log.info("Still waiting for Notion export to complete...")
                    continue

                node = next(iter(activity_map.values()))["value"]
                notification_start_timestamp = int(node["start_time"])

                if notification_start_timestamp < export_trigger_timestamp:
                    log.info("Waiting for fresh export notification...")
                    continue

                export_activity: str = node.get("edits", [{}])[0].get("link")
                if not export_activity:
                    log.info("Download URL not present yet. Retrying...")
                    continue

                return export_activity

            except Exception as e:
                log.error("Error parsing response", exc_info=e)
                continue

        return None

    def _get_notification_json(self) -> str:
        return json.dumps(
            {
                "spaceId": self.config.notion_space_id,
                "size": 20,
                "type": "unread_and_read",
                "variant": "no_grouping",
            }
        )
