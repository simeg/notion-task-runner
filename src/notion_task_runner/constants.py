"""
Constants used throughout the Notion Task Runner application.

This module centralizes all API endpoints, versions, and common configuration
values to reduce duplication and improve maintainability.
"""

# Notion API Configuration
NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_INTERNAL_API_URL = "https://www.notion.so/api/v3"


# API Endpoints
def get_notion_database_query_url(database_id: str) -> str:
    """Get the URL for querying a Notion database."""
    return f"{NOTION_BASE_URL}/databases/{database_id}/query"


def get_notion_block_update_url(block_id: str) -> str:
    """Get the URL for updating a Notion block."""
    return f"{NOTION_BASE_URL}/blocks/{block_id}"


def get_notion_headers(api_key: str) -> dict[str, str]:
    """Get standardized headers for Notion API requests."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }


def get_notion_internal_headers(user_id: str) -> dict[str, str]:
    """Get headers for internal Notion API requests with security headers."""
    return {
        "x-notion-active-user-header": user_id,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.notion.so/",
        # Security headers
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.notion.so",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }


# Default Configuration Values
DEFAULT_EXPORT_DIR = "/tmp"
VALID_EXPORT_TYPES = ["markdown", "html"]

# Retry Configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_WAIT_SECONDS = 2

# Date/Time Formatting
DATETIME_FORMAT = "%H:%M %d/%-m"
