from notion_task_runner.notion import NotionDatabase
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.tasks.base_page_task import NotionPageUpdateTask
from notion_task_runner.tasks.pas.sum_calculator import SumCalculator
from notion_task_runner.tasks.task_config import TaskConfig


class PASPageTask(NotionPageUpdateTask):
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
    COLUMN_NAME = "Slutpris"

    def __init__(
        self,
        client: AsyncNotionClient,
        db: NotionDatabase,
        config: TaskConfig,
        calculator: SumCalculator,
        block_id: str | None = None,
    ):
        super().__init__(client, db, config, calculator, block_id)

    def get_default_block_id(self) -> str:
        return self.BLOCK_ID

    def get_database_id(self) -> str:
        return self.DATABASE_ID

    def get_column_name(self) -> str:
        return self.COLUMN_NAME

    def get_display_text(self, total_value: float) -> str:
        return "Sålt för totalt: "

    def get_task_name(self) -> str:
        return "PAS Page Task"
