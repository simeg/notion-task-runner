"""
Type-safe configuration management using Pydantic.

Provides validated configuration loading from environment variables
with clear error messages and automatic type conversion.
"""

from pathlib import Path
from typing import Literal

import requests
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from notion_task_runner.constants import (
    DEFAULT_EXPORT_DIR,
    NOTION_BASE_URL,
    VALID_EXPORT_TYPES,
    get_notion_headers,
)

# Valid export types for export tasks
ExportType = Literal["markdown", "html"]


class TaskConfig(BaseSettings):
    """
    Type-safe configuration for Notion-related tasks.

    This class automatically loads and validates configuration from environment
    variables using Pydantic. It ensures all required fields are present and
    validates their formats and constraints.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required Notion configuration
    notion_space_id: str = Field(
        ..., description="Notion workspace/space ID", min_length=1
    )
    notion_token_v2: str = Field(
        ..., description="Notion v2 authentication token", min_length=1
    )
    notion_api_key: str = Field(
        ..., description="Notion API key for external API access", min_length=1
    )

    # Download Export Task Specific
    downloads_directory_path: Path = Field(
        default=Path(DEFAULT_EXPORT_DIR),
        description="Directory path for downloaded exports",
    )
    export_type: ExportType = Field(
        default="markdown", description="Export format type"
    )
    flatten_export_file_tree: bool = Field(
        default=False, description="Whether to flatten the export file structure"
    )

    # Google Drive Upload Task Specific
    google_drive_service_account_secret_json: str = Field(
        ..., description="Google Drive service account JSON credentials", min_length=1
    )
    google_drive_root_folder_id: str = Field(
        ..., description="Google Drive root folder ID for uploads", min_length=1
    )

    # Global Configuration
    is_prod: bool = Field(default=False, description="Production mode flag")

    @field_validator("notion_api_key")
    @classmethod
    def validate_notion_api_key(cls, v: str) -> str:
        """Validate that Notion API key is not empty."""
        if not v.strip():
            raise ValueError("Notion API key cannot be empty")
        return v

    @field_validator("export_type")
    @classmethod
    def validate_export_type(cls, v: str) -> str:
        """Validate that export type is supported."""
        if v not in VALID_EXPORT_TYPES:
            raise ValueError(
                f"Invalid export type: {v}. Must be one of {', '.join(VALID_EXPORT_TYPES)}"
            )
        return v

    @field_validator("downloads_directory_path")
    @classmethod
    def validate_downloads_directory(cls, v: Path) -> Path:
        """Ensure downloads directory exists."""
        resolved_path = v.resolve()
        resolved_path.mkdir(parents=True, exist_ok=True)
        return resolved_path

    @property
    def notion_headers(self) -> dict[str, str]:
        """Get Notion API headers for this configuration."""
        return get_notion_headers(self.notion_api_key)

    def validate_notion_connectivity(self) -> bool:
        """
        Validate that the Notion API credentials work by making a simple API call.

        Returns:
            bool: True if credentials are valid and API is accessible
        """
        try:
            # Simple API call to check if credentials work
            response = requests.get(
                f"{NOTION_BASE_URL}/users/me", headers=self.notion_headers, timeout=10
            )

            return response.status_code == 200

        except Exception:
            return False

    @classmethod
    def from_env(cls) -> "TaskConfig":
        """
        Create TaskConfig from environment variables.

        This method is kept for backward compatibility with existing code.
        The Pydantic BaseSettings automatically loads from environment.
        """
        return cls()  # type: ignore[call-arg]

    def model_dump_safe(self) -> dict[str, str]:
        """
        Dump model data with sensitive fields masked.

        Returns configuration data suitable for logging or debugging
        with API keys and tokens masked for security.
        """
        data = self.model_dump()

        # Mask sensitive fields
        sensitive_fields = [
            "notion_token_v2",
            "notion_api_key",
            "google_drive_service_account_secret_json",
        ]

        for field in sensitive_fields:
            if data.get(field):
                # Show first 8 and last 4 characters with masking
                value = str(data[field])
                if len(value) > 12:
                    data[field] = f"{value[:8]}...{value[-4:]}"
                else:
                    data[field] = "***masked***"

        return data
