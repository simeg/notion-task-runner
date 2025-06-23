import time
from datetime import datetime
from pathlib import Path

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient
from notion_task_runner.task import Task
from notion_task_runner.tasks.download_export.export_file_downloader import (
    ExportFileDownloader,
)
from notion_task_runner.tasks.download_export.export_file_poller import ExportFilePoller
from notion_task_runner.tasks.download_export.export_file_trigger import (
    ExportFileTrigger,
)
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class ExportFileTask(Task):
    """
    Coordinates the full Notion export workflow: triggering, polling, and downloading.

    This task orchestrates the Notion export process by:
    - Triggering an export task via the Notion API.
    - Polling for a download link once the export is ready.
    - Downloading and verifying the exported .zip file.

    It returns the path to the successfully downloaded export, or None if any step fails.
    """

    FETCH_DOWNLOAD_URL_RETRY_SECONDS = 5

    ENQUEUE_ENDPOINT = "https://www.notion.so/api/v3/enqueueTask"
    NOTIFICATION_ENDPOINT = "https://www.notion.so/api/v3/getNotificationLogV2"
    EXPORT_FILE_NAME = "notion-export"
    EXPORT_FILE_EXTENSION = ".zip"

    def __init__(self, client: NotionClient, config: TaskConfig) -> None:
        self.client = client
        self.config = config
        self.trigger = ExportFileTrigger(client, config)
        self.poller = ExportFilePoller(client, config)
        self.downloader = ExportFileDownloader(client)

    def run(self) -> Path | None:
        try:
            export_trigger_timestamp = int(time.time() * 1000)
            task_id = self.trigger.trigger_export_task()
            if not task_id:
                log.info("taskId could not be extracted")
                return None

            log.info("taskId extracted")

            download_url = self.poller.poll_for_download_url(export_trigger_timestamp)

            if not download_url:
                log.info("downloadLink could not be extracted")
                return None

            log.info("Download link extracted")
            file_name = f"{self.EXPORT_FILE_NAME}-{self.config.export_type}{'-flattened' if self.config.flatten_export_file_tree else ''}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}{self.EXPORT_FILE_EXTENSION}"
            download_path = Path(self.config.downloads_directory_path) / file_name

            downloaded_file = self.downloader.download_and_verify(
                download_url, download_path
            )
            if not downloaded_file:
                return None

            log.info(f"Download finished: {downloaded_file.name}")
            return downloaded_file

        except Exception as e:
            log.warning("Exception during export", exc_info=e)
            return None
