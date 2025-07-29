from pathlib import Path

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from notion_task_runner.logging import get_logger

log = get_logger(__name__)


class GoogleDriveClient:
    """
    Provides a client interface for uploading files to Google Drive.

    This class wraps the Google Drive API resource to upload local files (e.g., ZIP archives)
    to a specified folder using a provided service account session.
    It performs basic file checks and logs upload results.
    """

    def __init__(self, drive_service: Resource, root_folder_id: str) -> None:
        self.drive_service = drive_service
        self.root_folder_id = root_folder_id

    def upload(self, file_to_upload: Path) -> bool:
        """
        Uploads the given file to Google Drive.

        Args:
            file_to_upload (Path): The path to the file to upload.

        Returns:
            bool: True if upload succeeded, False otherwise.
        """
        log.info("Google Drive: uploading file '%s' ...", file_to_upload.name)

        if not file_to_upload.exists() or not file_to_upload.is_file():
            log.error(
                "Google Drive: file '%s' does not exist or is not a regular file",
                file_to_upload,
            )
            return False

        file_metadata = {
            "name": file_to_upload.name,
            "parents": [self.root_folder_id],
        }

        media = MediaFileUpload(str(file_to_upload), mimetype="application/zip")

        try:
            response = (
                self.drive_service.files()
                .create(body=file_metadata, media_body=media, fields="id, parents")
                .execute()
            )
        except HttpError as e:
            log.warning(
                "Google Drive: failed to upload '%s': %s",
                file_to_upload.name,
                e,
                exc_info=e,
            )
            return False

        log.info(
            "Google Drive: successfully uploaded '%s' with ID: %s",
            file_to_upload.name,
            response.get("id"),
        )
        return True
