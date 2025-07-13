import threading
from typing import Any, cast

import requests
from requests import Session, cookies

from notion_task_runner.logger import get_logger

log = get_logger(__name__)


class NotionClient:
    """
    Thread-safe HTTP client for interacting with the Notion API.

    This class manages an authenticated session for each thread using thread-local storage.
    It supports making authenticated GET, POST, and PATCH requests to Notion endpoints,
    automatically handling session setup and header configuration.
    """

    def __init__(self) -> None:
        self._thread_local = threading.local()

    def post(
        self,
        url: str,
        data: str | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        response = self._request("POST", url, headers=headers, data=data, json=json)
        return cast(dict[str, Any], response.json())

    def patch(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        return self._request("PATCH", url, headers=headers, json=json)

    def get(
        self, url: str, headers: dict[str, str] | None = None, stream: bool = False
    ) -> requests.Response:
        return self._request("GET", url, headers=headers, stream=stream)

    def delete(
        self, url: str, headers: dict[str, str] | None = None
    ) -> requests.Response:
        return self._request("DELETE", url, headers=headers)

    def _request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        data: Any = None,
        json: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> requests.Response:
        session = self._get_thread_local_session()
        response = session.request(
            method, url, headers=headers, data=data, json=json, stream=stream
        )

        if not response.ok:
            log.error(f"HTTP Error: {response.status_code} {response.text}")
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                raise

        return response

    def _create_authenticated_session(self) -> Session:
        from notion_task_runner.tasks.task_config import TaskConfig

        config = TaskConfig.from_env()
        session = Session()
        session.cookies = cookies.cookiejar_from_dict(
            {"token_v2": config.notion_token_v2}
        )  # type: ignore[no-untyped-call]

        # Trigger Notion session state
        response = session.post("https://www.notion.so/api/v3/loadUserContent", json={})
        response.raise_for_status()

        # Optionally extract user ID and set header (like the original client)
        data = response.json()
        user_id = next(iter(data["recordMap"]["notion_user"].keys()))
        session.headers.update(
            {
                "x-notion-active-user-header": user_id,
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.notion.so/",
            }
        )
        return session

    def _get_thread_local_session(self) -> Session:
        if not hasattr(self._thread_local, "session"):
            self._thread_local.session = self._create_authenticated_session()
        return cast(Session, self._thread_local.session)
