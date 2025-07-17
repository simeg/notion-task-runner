from datetime import datetime

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient, NotionDatabase
from notion_task_runner.task import Task
from notion_task_runner.tasks.pas.sum_calculator import SumCalculator
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class PASPageTask(Task):
    """
    Task that updates the 'Prylar att sälja' Notion page with the total sum of sold items.

    This task retrieves all entries from a Notion database, calculates the total sum using
    the provided SumCalculator, and updates a specific callout block in the Notion page
    with the result.

    Attributes:
        BLOCK_ID (str): Default ID of the callout block to update.
        DATABASE_ID (str): ID of the Notion database containing items for sale.
    """

    BLOCK_ID = "215aa18d-640d-8043-b78c-fab9b2bdf7dc"
    DATABASE_ID = "1fbaa18d-640d-804d-82c0-ce27d072c10b"

    def __init__(
        self,
        client: NotionClient,
        db: NotionDatabase,
        config: TaskConfig,
        calculator: SumCalculator,
        block_id: str | None = None,
    ):
        self.client = client
        self.db = db
        self.config = config
        self.calculator = calculator
        self.block_id = block_id or self.BLOCK_ID

    def run(self) -> None:
        rows = self.db.fetch_rows(self.DATABASE_ID)
        total_sum = self.calculator.calculate(rows)

        now = datetime.now()
        time_and_date_now = now.strftime("%H:%M %d/%-m")

        url = f"https://api.notion.com/v1/blocks/{self.block_id}"
        data = {
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Sålt för totalt: "},
                        "annotations": {"bold": True},
                    },
                    {
                        "type": "text",
                        "text": {"content": f"{total_sum}kr"},
                        "annotations": {"bold": False},
                    },
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
            "✅ Updated Prylar Att Sälja page!"
            if success
            else "❌ Failed to update Prylar Att Sälja."
        )
