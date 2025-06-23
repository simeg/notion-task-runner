import os
from pathlib import Path

from notion_task_runner.logger import get_logger
from notion_task_runner.task import Task
from notion_task_runner.tasks.backup.export_file_watcher import ExportFileWatcher
from notion_task_runner.tasks.backup.google_credentials_provider import (
    GoogleCredentialsProvider,
)
from notion_task_runner.tasks.backup.google_drive_uploader import GoogleDriveUploader
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class GoogleDriveUploadTask(Task):
    """
    A task that uploads a Notion export file to Google Drive.

    This task waits for a file with a specific prefix to appear in the configured downloads directory.
    It then uploads the file to a Google Drive folder using service account credentials.
    """

    KEY_GOOGLE_DRIVE_ROOT_FOLDER_ID = "GOOGLE_DRIVE_ROOT_FOLDER_ID"
    KEY_GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON = (
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON"
    )
    KEY_GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_FILE_PATH = (
        "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_FILE_PATH"
    )

    def __init__(self, config: TaskConfig) -> None:
        self.config = config

    def run(self) -> None:
        log.info("------------ Starting Google Drive Upload Task ------------")

        file_dir = self.config.downloads_directory_path
        file_prefix = "notion-export"

        if not file_dir:
            log.error("DOWNLOADS_DIRECTORY_PATH is not set.")
            raise SystemExit(1)

        # Wait for the file to appear
        exported_file = ExportFileWatcher.wait_for_file(Path(file_dir), file_prefix)

        try:
            self.start_google_drive_backup(exported_file)
        except Exception as e:
            log.exception("Google Drive backup failed: %s", e)
            raise SystemExit(1) from e

        log.info("✅ Google Drive backup completed successfully.")

    def start_google_drive_backup(self, file_to_upload: Path) -> None:
        secret = GoogleCredentialsProvider.get_secret()
        if not secret:
            log.info("No secret provided. Unable to upload to Google Drive.")
            return

        folder_id = os.getenv(self.KEY_GOOGLE_DRIVE_ROOT_FOLDER_ID)
        if not folder_id:
            log.info(
                "Skipping Google Drive upload. %s is not set.",
                self.KEY_GOOGLE_DRIVE_ROOT_FOLDER_ID,
            )
            return

        uploader = GoogleDriveUploader(secret, folder_id)
        success = uploader.upload(file_to_upload)

        if not success:
            raise RuntimeError("Google Drive backup failed")
