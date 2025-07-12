import concurrent.futures

from dotenv import load_dotenv

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient, NotionDatabase
from notion_task_runner.tasks import PrylarkivPageTask
from notion_task_runner.tasks.backup.google_drive_upload_task import (
    GoogleDriveUploadTask,
)
from notion_task_runner.tasks.car.car_costs_task import CarCostsTask
from notion_task_runner.tasks.car.car_metadata_task import CarMetadataTask
from notion_task_runner.tasks.download_export.export_file_task import ExportFileTask
from notion_task_runner.tasks.pas.pas_page_task import PASPageTask
from notion_task_runner.tasks.pas.sum_calculator import SumCalculator
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)

load_dotenv(override=False)


class TaskRunner:
    """
    Coordinates the execution of multiple Notion-related tasks concurrently.

    This class initializes and runs a sequence of task instances such as exporting, uploading, and page-specific processors.
    Tasks are executed in parallel using a ThreadPoolExecutor, and any exceptions are logged without halting execution.
    """

    def __init__(self, client: NotionClient, config: TaskConfig) -> None:
        if config.is_prod:
            log.info("Running in production mode.")
        else:
            log.info("Running in development mode.")

        database = NotionDatabase(client, config)

        self.tasks = [
            PASPageTask(
                client, NotionDatabase(client, config), config, SumCalculator()
            ),
            PrylarkivPageTask(client, NotionDatabase(client, config), config),
            ExportFileTask(client, config),
            GoogleDriveUploadTask(config),
            CarMetadataTask(client, config),
            CarCostsTask(client, database, config),
        ]

    def run(self) -> None:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(task.run) for task in self.tasks]
            concurrent.futures.wait(futures)

            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    log.error(f"Task failed: {e}")


if __name__ == "__main__":
    task_config = TaskConfig.from_env()
    app = TaskRunner(NotionClient(), task_config)
    app.run()
