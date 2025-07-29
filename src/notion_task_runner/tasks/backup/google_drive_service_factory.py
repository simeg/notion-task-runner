import json

from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import Resource, build

from notion_task_runner.logging import get_logger

log = get_logger(__name__)


class GoogleDriveServiceFactory:
    """
    Factory class for creating a Google Drive API service instance using a service account.

    This class provides a static method to initialize and return an authenticated Google Drive API client.
    It handles parsing of the service account JSON and applies the appropriate OAuth scopes.
    """

    OAUTH_SCOPE_GOOGLE_DRIVE = "https://www.googleapis.com/auth/drive"

    @staticmethod
    def create(service_account_secret: str) -> Resource | None:
        """
        Creates and returns a Google Drive API service using a service account secret.

        :param service_account_secret: JSON string of the service account credentials
        :return: Authorized Google Drive API service or None if something goes wrong
        """
        if not service_account_secret.strip():
            log.error("Service account secret is empty")
            return None
        try:
            credentials: Credentials = (
                service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
                    json.loads(service_account_secret),
                    scopes=[GoogleDriveServiceFactory.OAUTH_SCOPE_GOOGLE_DRIVE],
                )
            )
            service = build("drive", "v3", credentials=credentials)
            return service

        except Exception as e:
            log.error("Failed to create Google Drive service: %s", e, exc_info=e)
            return None
