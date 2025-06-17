from typing import Any

from notion_task_runner.logger import get_logger
from notion_task_runner.task_interface import Task
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class PrylarkivPageTask(Task):
    """
    Task that updates the 'Prylarkiv' Notion page with the next available item number.

    This task retrieves all entries from a specific Notion database ('Prylar'),
    calculates the next item number to be used, and updates a callout block in a Notion page
    with that number.

    Attributes:
        BLOCK_ID (str): Default ID of the callout block to update.
        DATABASE_ID (str): ID of the Notion database containing prylar entries.
    """

    BLOCK_ID = "213aa18d-640d-80d5-b119-cadcb301db84"
    DATABASE_ID = "1fdaa18d-640d-80e5-ae53-c80e2dc41474"

    def __init__(
        self,
        client: Any,
        db: Any,
        config: TaskConfig,
        block_id: str | None = None,
    ):
        from notion_task_runner.notion import NotionClient, NotionDatabase

        self.client: NotionClient = client
        self.db: NotionDatabase = db
        self.config = config
        self.block_id = block_id or self.BLOCK_ID

    def run(self) -> None:
        rows = self.db.get_entries(self.DATABASE_ID)
        next_pryl_number = int(len(rows) + 1)

        url = f"https://api.notion.com/v1/blocks/{self.block_id}"
        data = {
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Nästa nummer på pryl: "},
                        "annotations": {"bold": True},
                    },
                    {
                        "type": "text",
                        "text": {"content": f"{next_pryl_number}"},
                        "annotations": {"code": True},
                    },
                ]
            }
        }
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.config.notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        response = self.client.patch(url, json=data, headers=headers)
        success = response.status_code == 200

        log.info(
            "✅ Updated Prylarkiv page!"
            if success
            else "❌ Failed to update Prylarkiv."
        )
