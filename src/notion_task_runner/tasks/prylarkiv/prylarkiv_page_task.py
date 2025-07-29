from datetime import datetime

import aiohttp

from notion_task_runner.constants import (
    DATETIME_FORMAT,
    get_notion_block_update_url,
    get_notion_headers,
)
from notion_task_runner.logging import get_logger
from notion_task_runner.notion import NotionDatabase
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.task import Task
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
        client: AsyncNotionClient,
        db: NotionDatabase,
        config: TaskConfig,
        block_id: str | None = None,
    ):
        self.client = client
        self.db = db
        self.config = config
        self.block_id = block_id or self.BLOCK_ID

    async def run(self) -> None:
        """
        Execute the prylarkiv update task.

        Fetches all items from the database, calculates the next item number,
        and updates the Notion page with this information.
        """
        try:
            log.info("Starting Prylarkiv Task - calculating next item number")

            rows = await self.db.fetch_rows(self.DATABASE_ID)
            next_pryl_number = len(rows) + 1

            log.debug(
                f"Found {len(rows)} existing items, next number: {next_pryl_number}"
            )

            now = datetime.now()
            time_and_date_now = now.strftime(DATETIME_FORMAT)

            url = get_notion_block_update_url(self.block_id)
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
                        {
                            "type": "text",
                            "text": {
                                "content": f" (Senast uppdaterad: {time_and_date_now})"
                            },
                            "annotations": {"italic": True, "color": "gray"},
                        },
                    ]
                }
            }

            headers = get_notion_headers(self.config.notion_api_key)

            response = await self.client.patch(url, json=data, headers=headers)
            response.raise_for_status()

            log.info("✅ Prylarkiv Task completed successfully")

        except aiohttp.ClientError as e:
            log.error(f"❌ Prylarkiv Task failed - API error: {e}")
            raise
        except Exception as e:
            log.error(f"❌ Prylarkiv Task failed: {e}")
            raise
