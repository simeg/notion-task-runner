import os
from pathlib import Path

from notion_task_runner.logger import get_logger

log = get_logger(__name__)


class GoogleCredentialsProvider:
    """
    Retrieves Google service account credentials for accessing the Google Drive API.

    This class checks environment variables for a service account secret, either as a raw JSON string
    or as a file path pointing to a JSON file. It provides a static method to return the credential
    as a string, supporting flexible configuration in different environments.
    """

    ENV_SECRET_JSON = "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON"
    ENV_SECRET_FILE_PATH = "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_FILE_PATH"

    @staticmethod
    def get_secret() -> str | None:
        """
        Attempts to retrieve the Google service account secret from either an environment variable
        or a file path specified by another environment variable.

        :return: The secret as a string, or None if not found or invalid.
        """
        secret = os.getenv(GoogleCredentialsProvider.ENV_SECRET_JSON)
        if secret and secret.strip():
            log.debug("Using Google Drive secret from environment variable.")
            return secret.strip()

        secret_file_path = os.getenv(GoogleCredentialsProvider.ENV_SECRET_FILE_PATH)
        if secret_file_path:
            try:
                file_path = Path(secret_file_path)
                if file_path.is_file():
                    content = file_path.read_text(encoding="utf-8").strip()
                    if content:
                        log.debug("Using Google Drive secret from file: %s", file_path)
                        return content
                    else:
                        log.warning("Secret file exists but is empty: %s", file_path)
                else:
                    log.warning("Secret file path does not exist: %s", file_path)
            except Exception as e:
                log.warning("Error reading secret file: %s", e)

        log.info("No Google Drive service account secret found.")
        return None
