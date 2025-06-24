# ruff: noqa: B008
import os
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import Literal, cast

from notion_task_runner.logger import get_logger
from notion_task_runner.utils import fail, get_or_raise

# Valid export types for export tasks
VALID_EXPORT_TYPES = ["markdown", "html"]
ExportType = Literal["markdown", "html"]

DEFAULT_EXPORT_DIR = "/tmp"


@dataclass(frozen=True)  # Make the class immutable
class TaskConfig:
    """
    Holds configuration for running Notion-related tasks, loaded from environment variables.

    This class provides configuration values for both exporting Notion data to disk and optionally uploading it
    to Google Drive. It reads environment variables and validates required inputs, ensuring the export directory exists,
    the export type is valid, and credentials are present.
    """

    notion_space_id: str | None
    notion_token_v2: str | None
    notion_api_key: str | None
    # ================================
    # Download Export Task Specific
    # ================================
    downloads_directory_path: Path
    export_type: ExportType
    flatten_export_file_tree: bool
    # ================================
    # Google Drive Upload Task Specific
    # ================================
    google_drive_service_account_secret_json: str | None = None
    google_drive_root_folder_id: str | None = None

    @staticmethod
    def from_env(external_log: Logger = get_logger(__name__)) -> "TaskConfig":
        notion_space_id = get_or_raise(external_log, "NOTION_SPACE_ID")
        notion_token_v2 = get_or_raise(external_log, "NOTION_TOKEN_V2")
        notion_api_key = get_or_raise(external_log, "NOTION_API_KEY")

        (
            downloads_dir_path,
            export_type,
            flatten_export_file_tree,
            downloads_directory,
        ) = TaskConfig._config_download_export_task(external_log)

        google_drive_service_account_secret_json = get_or_raise(
            external_log, "GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON"
        )
        google_drive_root_folder_id = get_or_raise(
            external_log, "GOOGLE_DRIVE_ROOT_FOLDER_ID"
        )

        return TaskConfig(
            notion_space_id=notion_space_id,
            notion_token_v2=notion_token_v2,
            notion_api_key=notion_api_key,
            # ================================
            # Download Export Task Specific
            # ================================
            downloads_directory_path=downloads_dir_path,
            export_type=export_type,
            flatten_export_file_tree=flatten_export_file_tree,
            # ================================
            # Google Drive Upload Task Specific
            # ================================
            google_drive_service_account_secret_json=google_drive_service_account_secret_json,
            google_drive_root_folder_id=google_drive_root_folder_id,
        )

    @staticmethod
    def _config_download_export_task(
        external_log: Logger = get_logger(__name__),
    ) -> tuple[Path, ExportType, bool, Path]:
        downloads_directory = Path(
            os.getenv("DOWNLOADS_DIRECTORY_PATH") or DEFAULT_EXPORT_DIR
        )
        export_type = os.getenv("EXPORT_TYPE", "markdown")
        flatten_export_file_tree = (
            os.getenv("FLATTEN_EXPORT_FILE_TREE", "False").lower() == "true"
        )

        if export_type not in VALID_EXPORT_TYPES:
            fail(
                external_log,
                f"Invalid export type: {export_type}. Must be one of {', '.join(VALID_EXPORT_TYPES)}",
            )

        export_type = cast(ExportType, export_type)

        # Ensure the downloads directory exists
        downloads_dir_path = Path(downloads_directory).resolve()
        downloads_dir_path.mkdir(parents=True, exist_ok=True)

        return (
            downloads_dir_path,
            export_type,
            flatten_export_file_tree,
            downloads_directory,
        )
