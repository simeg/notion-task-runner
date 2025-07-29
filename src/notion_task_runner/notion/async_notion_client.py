"""
Async HTTP client for interacting with the Notion API.

Provides async/await support for HTTP operations with connection pooling,
retry logic, and proper error handling using aiohttp.
"""

import asyncio
import threading
from typing import TYPE_CHECKING, Any

import aiohttp
from tenacity import retry, stop_after_attempt, wait_fixed

from notion_task_runner.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_WAIT_SECONDS,
    NOTION_INTERNAL_API_URL,
    get_notion_internal_headers,
)
from notion_task_runner.logging import get_logger

if TYPE_CHECKING:
    from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class AsyncNotionClient:
    """
    Thread-safe singleton async HTTP client for interacting with the Notion API.

    This class manages an authenticated aiohttp session for making async GET, POST,
    PATCH, and DELETE requests to Notion endpoints. Uses singleton pattern with
    connection pooling for optimal performance.
    """

    _instance: "AsyncNotionClient | None" = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, config: "TaskConfig | None" = None) -> "AsyncNotionClient":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: "TaskConfig | None" = None) -> None:
        if self._initialized:
            return

        if config is None:
            from notion_task_runner.tasks.task_config import TaskConfig

            config = TaskConfig.from_env()

        # Validate configuration for security
        self._validate_config(config)

        self.config = config
        self._session: aiohttp.ClientSession | None = None
        self._connector: aiohttp.TCPConnector | None = None
        AsyncNotionClient._initialized = True
        log.debug("AsyncNotionClient singleton initialized with validated config")

    async def __aenter__(self) -> "AsyncNotionClient":
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self) -> None:
        """Ensure the aiohttp session is created and authenticated."""
        if self._session is None or self._session.closed:
            await self._create_authenticated_session()

    async def _create_authenticated_session(self) -> None:
        """
        Create an authenticated aiohttp session for Notion API requests.

        Sets up connection pooling, cookies, and headers required for
        internal Notion API calls.
        """
        try:
            # Create connector with connection pooling and security settings
            self._connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
                # Security settings
                verify_ssl=True,  # Enforce SSL verification
                ssl_context=None,  # Use default SSL context (secure)
            )

            # Create session with authentication cookie
            cookie_jar = aiohttp.CookieJar()
            cookie_jar.update_cookies({"token_v2": self.config.notion_token_v2})

            self._session = aiohttp.ClientSession(
                connector=self._connector,
                cookie_jar=cookie_jar,
                timeout=aiohttp.ClientTimeout(total=30, connect=10),
                # Security settings
                trust_env=False,  # Don't trust environment proxy settings
                auto_decompress=True,  # Handle content encoding securely
            )

            # Trigger Notion session state to get user ID
            async with self._session.post(
                f"{NOTION_INTERNAL_API_URL}/loadUserContent", json={}
            ) as response:
                response.raise_for_status()
                data = await response.json()
                user_id = next(iter(data["recordMap"]["notion_user"].keys()))

            # Update session headers
            headers = get_notion_internal_headers(user_id)
            self._session.headers.update(headers)

            log.debug("Async Notion session authenticated successfully")

        except Exception as e:
            log.error(f"Failed to create authenticated async Notion session: {e}")
            await self.close()
            raise

    @retry(
        stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
        wait=wait_fixed(DEFAULT_RETRY_WAIT_SECONDS),
    )
    async def post(
        self,
        url: str,
        data: str | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make an async POST request."""
        await self._ensure_session()
        assert self._session is not None

        try:
            async with self._session.post(
                url, data=data, json=json, headers=headers
            ) as response:
                await self._handle_response_errors(response, "POST", url)
                return await response.json()  # type: ignore[no-any-return]
        except Exception as e:
            log.error(f"POST request failed {url}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
        wait=wait_fixed(DEFAULT_RETRY_WAIT_SECONDS),
    )
    async def patch(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> aiohttp.ClientResponse:
        """Make an async PATCH request."""
        await self._ensure_session()
        assert self._session is not None

        try:
            response = await self._session.patch(url, json=json, headers=headers)
            await self._handle_response_errors(response, "PATCH", url)
            return response
        except Exception as e:
            log.error(f"PATCH request failed {url}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
        wait=wait_fixed(DEFAULT_RETRY_WAIT_SECONDS),
    )
    async def get(
        self, url: str, headers: dict[str, str] | None = None
    ) -> aiohttp.ClientResponse:
        """Make an async GET request."""
        await self._ensure_session()
        assert self._session is not None

        try:
            response = await self._session.get(url, headers=headers)
            await self._handle_response_errors(response, "GET", url)
            return response
        except Exception as e:
            log.error(f"GET request failed {url}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
        wait=wait_fixed(DEFAULT_RETRY_WAIT_SECONDS),
    )
    async def delete(
        self, url: str, headers: dict[str, str] | None = None
    ) -> aiohttp.ClientResponse:
        """Make an async DELETE request."""
        await self._ensure_session()
        assert self._session is not None

        try:
            response = await self._session.delete(url, headers=headers)
            await self._handle_response_errors(response, "DELETE", url)
            return response
        except Exception as e:
            log.error(f"DELETE request failed {url}: {e}")
            raise

    async def _handle_response_errors(
        self, response: aiohttp.ClientResponse, method: str, url: str
    ) -> None:
        """Handle HTTP response errors with logging."""
        if not response.ok:
            error_text = await response.text()
            log.error(f"HTTP Error {method} {url}: {response.status} {error_text}")
            response.raise_for_status()

    async def close(self) -> None:
        """Close the aiohttp session and connector, clearing sensitive data."""
        if self._session and not self._session.closed:
            await self._session.close()

        if self._connector:
            await self._connector.close()

        # Wait for connections to close
        await asyncio.sleep(0.1)

        # Clear sensitive configuration data
        if hasattr(self, "config"):
            self.config = None  # type: ignore[assignment]

        log.debug("AsyncNotionClient session closed and sensitive data cleared")

    @staticmethod
    def _validate_config(config: "TaskConfig") -> None:
        """Validate configuration for security requirements."""
        if not config.notion_token_v2 or len(config.notion_token_v2) < 10:
            raise ValueError("Invalid or missing Notion token_v2")

        if not config.notion_api_key or len(config.notion_api_key) < 10:
            raise ValueError("Invalid or missing Notion API key")

        if not config.notion_space_id or len(config.notion_space_id) < 10:
            raise ValueError("Invalid or missing Notion space ID")

        # Ensure tokens don't contain suspicious characters
        suspicious_chars = ["<", ">", '"', "'", "&", "\n", "\r", "\t"]
        for char in suspicious_chars:
            if char in config.notion_token_v2 or char in config.notion_api_key:
                raise ValueError("Configuration contains potentially unsafe characters")

        log.debug("Configuration validation passed")

    @classmethod
    async def reset_singleton(cls) -> None:
        """Reset the singleton instance. Primarily used for testing."""
        with cls._lock:
            # Check if instance exists and has a session to close
            if (
                cls._instance
                and hasattr(cls._instance, "_session")
                and cls._instance._session
            ):
                await cls._instance.close()
            cls._instance = None
            cls._initialized = False
            log.debug("AsyncNotionClient singleton reset")
