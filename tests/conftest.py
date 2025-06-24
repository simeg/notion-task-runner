import pytest
from unittest.mock import MagicMock

from notion_task_runner.sum_calculator import SumCalculator


# ========================
# Calculator Fixtures
# ========================

@pytest.fixture
def calculator():
  # Create a mock calculator that uses the real SumCalculator method
  # to ensure it behaves like the real one, but can be mocked in tests.
  # This allows us to assert things like assert_called_once_with() on it.
  sum_calculator = SumCalculator()
  real_method = sum_calculator.calculate
  calculator = MagicMock(spec=SumCalculator)
  calculator.calculate = MagicMock(side_effect=real_method)
  return calculator


@pytest.fixture
def mock_calculator_30():
  calculator = MagicMock()
  calculator.calculate.return_value = 30
  return calculator


# ========================
# Notion Client Fixtures
# ========================

@pytest.fixture
def mock_notion_client_200():
  client = MagicMock()
  client.patch.return_value.status_code = 200
  return client


@pytest.fixture
def mock_notion_client_400():
  client = MagicMock()
  client.patch.return_value.status_code = 400
  return client


@pytest.fixture
def mock_client_single_page():
    mock = MagicMock()
    mock.post.return_value = {
        "results": [{"id": "1"}, {"id": "2"}],
        "has_more": False
    }
    return mock

@pytest.fixture
def mock_client_empty_response():
  client = MagicMock()
  client.post.return_value = {
    "results": [],
    "next_cursor": None
  }
  return client


@pytest.fixture
def mock_client_paginated():
  client = MagicMock()
  client.post.side_effect = [
    {"results": [{"id": "1"}], "next_cursor": "cursor-1"},
    {"results": [{"id": "2"}], "next_cursor": None}
  ]
  return client


@pytest.fixture
def mock_client_malformed_response():
  client = MagicMock()
  client.post.return_value = {}  # Missing 'results' and 'next_cursor'
  return client


# ========================
# Database Fixtures
# ========================

@pytest.fixture
def mock_db_w_props():
  db = MagicMock()
  db.fetch_rows.return_value = [
    {"properties": {"Slutpris": {"number": 10}}},
    {"properties": {"Slutpris": {"number": 20}}},
  ]
  return db


@pytest.fixture
def mock_db_empty_list():
  db = MagicMock()
  db.fetch_rows.return_value = []
  return db

# ========================
#	HTTP Response Fixtures
# ========================

@pytest.fixture
def mock_post_response():
    response = MagicMock()
    response.json.return_value = {"key": "value"}
    return response

@pytest.fixture
def mock_patch_response():
    return MagicMock()

@pytest.fixture
def mock_config():
    mock = MagicMock()
    mock.from_env.return_value = mock
    mock.notion_api_key = "some-api-key"
    return mock