from unittest.mock import MagicMock

import pytest
from requests import HTTPError

from notion_task_runner.notion import NotionDatabase
from notion_task_runner.tasks.task_config import TaskConfig
from tests.conftest import mock_client_empty_response


def test_fetch_rows_single_page(mock_client_single_page):
  config = MagicMock(spec=TaskConfig)
  config.notion_api_key = "some-api-key"
  sut = NotionDatabase(client=mock_client_single_page, config=config)
  result = sut.fetch_rows("irrelevant-id")

  assert result == [{"id": "1"}, {"id": "2"}]
  mock_client_single_page.post.assert_called_once()


def test_fetch_rows_pagination(mock_client_paginated):
  config = MagicMock(spec=TaskConfig)
  config.notion_api_key = "some-api-key"
  sut = NotionDatabase(client=mock_client_paginated, config=config)
  result = sut.fetch_rows("irrelevant-id")

  assert result == [{"id": "1"}, {"id": "2"}]
  assert mock_client_paginated.post.call_count == 2


def test_fetch_rows_returns_empty_list(mock_client_empty_response):
  config = MagicMock(spec=TaskConfig)
  config.notion_api_key = "some-api-key"
  sut = NotionDatabase(client=mock_client_empty_response, config=config)
  result = sut.fetch_rows("irrelevant-id")

  assert result == []
  mock_client_empty_response.post.assert_called_once()


def test_fetch_rows_missing_keys(mock_client_malformed_response):
  config = MagicMock(spec=TaskConfig)
  config.notion_api_key = "some-api-key"
  sut = NotionDatabase(client=mock_client_malformed_response, config=config)

  with pytest.raises(KeyError):
    sut.fetch_rows("irrelevant-id")

def test_fetch_rows_when_no_id_provided(mock_client_malformed_response):
  config = MagicMock(spec=TaskConfig)
  config.notion_api_key = "some-api-key"
  sut = NotionDatabase(client=mock_client_malformed_response, config=config)

  with pytest.raises(ValueError):
    sut.fetch_rows()

def test_fetch_rows_when_client_returns_400(mock_notion_client_400):
  config = MagicMock(spec=TaskConfig)
  config.notion_api_key = "some-api-key"
  sut = NotionDatabase(client=mock_notion_client_400, config=config)

  with pytest.raises(HTTPError):
    sut.fetch_rows("irrelevant-id")
