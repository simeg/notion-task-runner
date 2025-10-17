from notion_task_runner.notion import NotionDatabase
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.tasks.base_page_task import NotionPageUpdateTask
from notion_task_runner.tasks.pas.sum_calculator import SumCalculator
from notion_task_runner.tasks.task_config import TaskConfig


class AudiophilePageTask(NotionPageUpdateTask):
    """
    Task that updates the Audiophile Notion page with the total cost of equipment.

    This task retrieves all entries from the audiophile equipment database,
    calculates the total cost using the provided SumCalculator, and updates
    a specific callout block in the Notion page with the result.

    Attributes:
        CALLOUT_BLOCK_ID (str): Default ID of the callout block to update.
        DATABASE_ID (str): ID of the Notion database containing audiophile equipment.
    """

    CALLOUT_BLOCK_ID = "233aa18d-640d-80e4-a9d9-e7026992d380"
    DATABASE_ID = "233aa18d-640d-80a9-9b0b-e9a0383c906c"

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
        return self.CALLOUT_BLOCK_ID

    def get_database_id(self) -> str:
        return self.DATABASE_ID

    def get_column_name(self) -> str:
        return "Kostnad"

    def get_display_text(self, total_value: float) -> str:
        return "Mina HiFi hörlurar saker. Total kostnad: "

    def get_task_name(self) -> str:
        return "Audiophile Page Task"
