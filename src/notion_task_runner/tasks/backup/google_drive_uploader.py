import json
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from notion_task_runner.logging import get_logger
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class GoogleDriveUploader:
    """
    Handles uploading of ZIP files to a specified Google Drive folder.

    This class wraps the Google Drive API and allows uploading of export files using a service account.
    It performs validation on the file before upload and logs the outcome of the operation.
    """

    def __init__(self, config: TaskConfig) -> None:
        self.config = config

    def upload(self, file_to_upload: Path) -> bool:
        log.info("Google Drive: uploading file '%s' ...", file_to_upload.name)
        if not file_to_upload.exists() or not file_to_upload.is_file():
            log.error(
                "Google Drive: file '%s' does not exist or is not a regular file",
                file_to_upload,
            )
            return False

        folder_id = self.config.google_drive_root_folder_id
        file_metadata = {"name": file_to_upload.name, "parents": [folder_id]}

        media = MediaFileUpload(file_to_upload, mimetype="application/zip")

        try:
            response = (
                self._create_drive_service()
                .files()
                .create(body=file_metadata, media_body=media, fields="id, parents")
                .execute()
            )
        except HttpError as e:
            log.warning("Google Drive: Exception during upload", exc_info=e)
            return False

        log.info(
            "Google Drive: successfully uploaded '%s' with ID: %s",
            file_to_upload.name,
            response.get("id"),
        )
        return True

    def _create_drive_service(self) -> Resource:
        secret = self.config.google_drive_service_account_secret_json.strip()
        credentials: Credentials = Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
            json.loads(secret), scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build("drive", "v3", credentials=credentials)
