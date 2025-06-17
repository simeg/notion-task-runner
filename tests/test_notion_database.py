import pytest
from requests import HTTPError

from notion_task_runner.notion import NotionDatabase
from tests.conftest import mock_client_empty_response


def test_get_entries_single_page(mock_client_single_page):
  sut = NotionDatabase(client=mock_client_single_page)
  result = sut.get_entries("irrelevant-id")

  assert result == [{"id": "1"}, {"id": "2"}]
  mock_client_single_page.post_for_db.assert_called_once()


def test_get_entries_pagination(mock_client_paginated):
  sut = NotionDatabase(client=mock_client_paginated)
  result = sut.get_entries("irrelevant-id")

  assert result == [{"id": "1"}, {"id": "2"}]
  assert mock_client_paginated.post_for_db.call_count == 2


def test_get_entries_returns_empty_list(mock_client_empty_response):
  sut = NotionDatabase(client=mock_client_empty_response)
  result = sut.get_entries("irrelevant-id")

  assert result == []
  mock_client_empty_response.post_for_db.assert_called_once()


def test_get_entries_missing_keys(mock_client_malformed_response):
  sut = NotionDatabase(client=mock_client_malformed_response)

  with pytest.raises(KeyError):
    sut.get_entries("irrelevant-id")

def test_get_entries_when_no_id_provided(mock_client_malformed_response):
  sut = NotionDatabase(client=mock_client_malformed_response)

  with pytest.raises(ValueError):
    sut.get_entries()

def test_get_entries_when_client_returns_400(mock_notion_client_400):
  sut = NotionDatabase(client=mock_notion_client_400)

  with pytest.raises(HTTPError):
    sut.get_entries("irrelevant-id")
