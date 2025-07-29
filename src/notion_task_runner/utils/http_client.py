"""
HTTP client utilities for Notion API interactions.

This module provides common functionality for making HTTP requests
to the Notion API with proper error handling, retries, and logging.
"""

import asyncio
from typing import Any

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from notion_task_runner.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_WAIT_SECONDS,
)
from notion_task_runner.logging import get_logger

log = get_logger(__name__)


class NotionHTTPError(Exception):
    """Raised when Notion API returns an error response."""

    def __init__(
        self,
        status_code: int,
        message: str,
        response_data: dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        self.message = message
        self.response_data = response_data
        super().__init__(f"Notion API error {status_code}: {message}")


class HTTPClientMixin:
    """
    Mixin class providing common HTTP client functionality for Notion tasks.

    This mixin provides standardized methods for making HTTP requests with
    proper error handling, logging, and retry logic.
    """

    @retry(
        stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=DEFAULT_RETRY_WAIT_SECONDS, max=10),
        reraise=True,
    )
    async def _make_notion_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        data: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """
        Make a request to the Notion API with retry logic.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: Full URL to request
            headers: Request headers
            data: Request body data (for POST/PATCH)
            timeout: Request timeout in seconds

        Returns:
            Response data as dictionary

        Raises:
            NotionHTTPError: If the request fails after retries
            aiohttp.ClientError: For network-related errors
        """
        log.debug(f"Making {method} request to {url}")

        # Check if we have a client attribute (for testing compatibility)
        if hasattr(self, "client") and self.client:
            # Use the existing client method (likely a mock in tests)
            if method.upper() == "PATCH":
                response = await self.client.patch(url, headers=headers, json=data)
            elif method.upper() == "POST":
                response = await self.client.post(url, headers=headers, json=data)
            elif method.upper() == "GET":
                response = await self.client.get(url, headers=headers)
            else:
                response = await self.client.request(
                    method, url, headers=headers, json=data
                )

            # For compatibility with mock responses, try to get JSON data
            if hasattr(response, "json"):
                try:
                    # Try to call json() as async method first
                    response_data = await response.json()
                except TypeError:
                    # If not async (mock), get the value directly
                    response_data = (
                        response.json() if callable(response.json) else response.json
                    )
            else:
                response_data = {}

            # For test mocks, check if raise_for_status exists and call it
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()

            log.debug("Request successful")
            return response_data  # type: ignore[no-any-return]

        # Fallback to creating our own session (production use)
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)

            async with (
                aiohttp.ClientSession(timeout=timeout_obj) as session,
                session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                ) as response,
            ):
                response_data = await response.json()

                if not response.ok:
                    log.error(f"Notion API error: {response.status} - {response_data}")
                    raise NotionHTTPError(
                        status_code=response.status,
                        message=str(response_data),
                        response_data=response_data,
                    )

                log.debug(f"Request successful: {response.status}")
                return response_data  # type: ignore[no-any-return]

        except aiohttp.ClientError as e:
            log.error(f"HTTP client error: {e}")
            raise
        except Exception as e:
            log.error(f"Unexpected error in HTTP request: {e}")
            raise

    async def _make_parallel_requests(
        self,
        requests: list[tuple[str, str, dict[str, str], dict[str, Any] | None]],
        max_concurrent: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Make multiple requests in parallel with concurrency control.

        Args:
            requests: List of (method, url, headers, data) tuples
            max_concurrent: Maximum number of concurrent requests

        Returns:
            List of response data dictionaries in the same order as requests
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _make_request(
            request_data: tuple[str, str, dict[str, str], dict[str, Any] | None],
        ) -> dict[str, Any]:
            method, url, headers, data = request_data
            async with semaphore:
                return await self._make_notion_request(method, url, headers, data)

        log.info(
            f"Making {len(requests)} parallel requests (max {max_concurrent} concurrent)"
        )

        try:
            results = await asyncio.gather(*[_make_request(req) for req in requests])
            log.info(f"All {len(requests)} requests completed successfully")
            return results
        except Exception as e:
            log.error(f"Error in parallel requests: {e}")
            raise


async def validate_notion_connectivity(
    headers: dict[str, str],
    test_url: str,
    timeout: int = 10,
) -> bool:
    """
    Validate that we can connect to the Notion API.

    Args:
        headers: Headers for authentication
        test_url: URL to test connectivity against
        timeout: Request timeout in seconds

    Returns:
        True if connectivity is successful, False otherwise
    """
    try:
        timeout_obj = aiohttp.ClientTimeout(total=timeout)

        async with (
            aiohttp.ClientSession(timeout=timeout_obj) as session,
            session.get(url=test_url, headers=headers) as response,
        ):
            return response.status < 500  # Accept 4xx as "connected but unauthorized"

    except Exception as e:
        log.error(f"Connectivity validation failed: {e}")
        return False
