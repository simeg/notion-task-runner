import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from notion_task_runner.logger import get_logger
from notion_task_runner.utils import fail

log = get_logger(__name__)

# Valid export types for export tasks
VALID_EXPORT_TYPES = ["markdown", "html"]
ExportType = Literal["markdown", "html"]

DEFAULT_EXPORT_DIR = "downloads"


@dataclass
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

    @staticmethod
    def from_env() -> "TaskConfig":
        notion_space_id = os.getenv("NOTION_SPACE_ID")
        notion_token_v2 = os.getenv("NOTION_TOKEN_V2")
        notion_api_key = os.getenv("NOTION_API_KEY")
        # downloads_directory_path = os.getenv("DOWNLOADS_DIRECTORY_PATH")

        if not notion_api_key:
            fail(log, "Missing required environment variable: NOTION_API_KEY")

        (
            downloads_dir_path,
            export_type,
            flatten_export_file_tree,
            downloads_directory,
        ) = TaskConfig._config_download_export_task(notion_space_id, notion_token_v2)

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
        )

    @staticmethod
    def _config_download_export_task(
        notion_space_id: str | None, notion_token_v2: str | None
    ) -> tuple[Path, ExportType, bool, Path]:
        downloads_directory = Path(
            os.getenv("DOWNLOADS_DIRECTORY_PATH") or DEFAULT_EXPORT_DIR
        )
        export_type = os.getenv("EXPORT_TYPE", "markdown")
        flatten_export_file_tree = (
            os.getenv("FLATTEN_EXPORT_FILE_TREE", "False").lower() == "true"
        )

        if not notion_space_id or not notion_token_v2:
            fail(
                log,
                "Missing required environment variables: NOTION_SPACE_ID and/or NOTION_TOKEN_V2",
            )

        if export_type not in VALID_EXPORT_TYPES:
            fail(
                log,
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
