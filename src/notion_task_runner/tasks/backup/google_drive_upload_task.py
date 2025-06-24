from pathlib import Path

from notion_task_runner.logger import get_logger
from notion_task_runner.task import Task
from notion_task_runner.tasks.backup.export_file_watcher import ExportFileWatcher
from notion_task_runner.tasks.backup.google_drive_uploader import GoogleDriveUploader
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class GoogleDriveUploadTask(Task):
    """
    A task that uploads a Notion export file to Google Drive.

    This task waits for a file with a specific prefix to appear in the configured downloads directory.
    It then uploads the file to a Google Drive folder using service account credentials.
    """

    EXPORT_FILE_PREFIX = "notion-backup"

    def __init__(self, config: TaskConfig) -> None:
        self.config = config

    def run(self) -> None:
        # Wait for the file to appear
        exported_file = ExportFileWatcher.wait_for_file(
            Path(self.config.downloads_directory_path), self.EXPORT_FILE_PREFIX
        )

        try:
            self._start_google_drive_backup(exported_file)
        except Exception as e:
            log.exception("Google Drive backup failed: %s", e)
            raise SystemExit(1) from e

        log.info("✅ Google Drive backup completed successfully.")

    def _start_google_drive_backup(self, file_to_upload: Path) -> None:
        uploader = GoogleDriveUploader(self.config)
        success = uploader.upload(file_to_upload)

        if not success:
            raise RuntimeError("Google Drive backup failed")
