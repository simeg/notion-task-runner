from datetime import datetime
from typing import Any

from notion_task_runner.logger import get_logger
from notion_task_runner.task import Task
from notion_task_runner.tasks.pas.sum_calculator import SumCalculator
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class AudiophilePageTask(Task):

    CALLOUT_BLOCK_ID = "233aa18d-640d-80e4-a9d9-e7026992d380"
    DATABASE_ID = "233aa18d-640d-80a9-9b0b-e9a0383c906c"

    def __init__(
        self,
        client: Any,
        db: Any,
        config: TaskConfig,
        calculator: SumCalculator,
        block_id: str | None = None,
    ):
        from notion_task_runner.notion import NotionClient, NotionDatabase

        self.client: NotionClient = client
        self.db: NotionDatabase = db
        self.config = config
        self.calculator: SumCalculator = calculator
        self.block_id: str = block_id or self.CALLOUT_BLOCK_ID

    def run(self) -> None:
        rows = self.db.fetch_rows(self.DATABASE_ID)
        total_cost = self.calculator.calculate_total_for_column(rows, "Kostnad")

        now = datetime.now()
        time_and_date_now = now.strftime("%H:%M %d/%-m")

        url = f"https://api.notion.com/v1/blocks/{self.block_id}"
        data = {
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Mina audiophile saker. Total kostnad: "},
                        "annotations": {"bold": True},
                    },
                    {"type": "text", "text": {"content": f"{total_cost}kr"}},
                    {
                        "type": "text",
                        "text": {
                            "content": " (Senast uppdaterad: " + time_and_date_now + ")"
                        },
                        "annotations": {"italic": True, "color": "gray"},
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
            "✅ Updated Audiophile page!"
            if success
            else "❌ Failed to update Audiophile."
        )
