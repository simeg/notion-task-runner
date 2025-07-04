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
        session = self._get_thread_local_session()
        response = session.post(url, headers=headers, data=data, json=json)
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    def patch(
        self,
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        session = self._get_thread_local_session()
        response = session.patch(url, headers=headers, json=json)
        response.raise_for_status()
        return response

    def get(self, url: str, stream: bool) -> requests.Response:
        session = self._get_thread_local_session()
        response = session.get(url, stream=stream)
        response.raise_for_status()
        return response

    def _create_authenticated_session(self) -> Session:
        from notion_task_runner.tasks.task_config import TaskConfig

        config = TaskConfig.from_env()
        session = Session()
        session.cookies = cookies.cookiejar_from_dict({"token_v2": config.notion_token_v2})  # type: ignore[no-untyped-call]

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
