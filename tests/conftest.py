import pytest
from unittest.mock import MagicMock, AsyncMock

from notion_task_runner.tasks.pas.sum_calculator import SumCalculator


# ========================
# Calculator Fixtures
# ========================

@pytest.fixture
def calculator():
  # Create a mock calculator that uses the real SumCalculator method
  # to ensure it behaves like the real one, but can be mocked in tests.
  # This allows us to assert things like assert_called_once_with() on it.
  sum_calculator = SumCalculator()
  real_method = sum_calculator.calculate_total_for_column
  calculator = MagicMock(spec=SumCalculator)
  calculator.calculate_total_for_column = MagicMock(side_effect=real_method)
  return calculator


@pytest.fixture
def mock_calculator_30():
  calculator = MagicMock()
  calculator.calculate_total_for_column.return_value = 30
  return calculator


# ========================
# Notion Client Fixtures
# ========================

@pytest.fixture
def mock_notion_client_200():
  client = MagicMock()
  
  # Create a mock response with proper methods
  mock_response = MagicMock()
  mock_response.status_code = 200
  mock_response.status = 200
  mock_response.text = AsyncMock(return_value="OK")
  mock_response.raise_for_status = MagicMock(return_value=None)  # Don't use AsyncMock for this
  
  client.patch = AsyncMock(return_value=mock_response)
  client.post = AsyncMock()
  return client


@pytest.fixture
def mock_notion_client_400():
  import aiohttp
  client = MagicMock()
  
  # Create a mock response that raises ClientResponseError on raise_for_status()
  mock_response = MagicMock()
  mock_response.status_code = 400
  mock_response.status = 400
  mock_response.text = AsyncMock(return_value="Bad Request")
  # Use regular MagicMock for raise_for_status, not AsyncMock
  def raise_for_status():
    raise aiohttp.ClientResponseError(
      request_info=MagicMock(), 
      history=(),
      status=400,
      message="Bad Request"
    )
  mock_response.raise_for_status = raise_for_status
  
  client.patch = AsyncMock(return_value=mock_response)
  # Return a dict with error status for post calls to database
  client.post = AsyncMock(return_value={"status": 400, "message": "Bad Request"})
  return client


@pytest.fixture
def mock_client_single_page():
    mock = MagicMock()
    mock.post = AsyncMock(return_value={
        "results": [{"id": "1"}, {"id": "2"}],
        "has_more": False
    })
    return mock

@pytest.fixture
def mock_client_empty_response():
  client = MagicMock()
  client.post = AsyncMock(return_value={
    "results": [],
    "next_cursor": None
  })
  return client


@pytest.fixture
def mock_client_paginated():
  client = MagicMock()
  client.post = AsyncMock(side_effect=[
    {"results": [{"id": "1"}], "next_cursor": "cursor-1"},
    {"results": [{"id": "2"}], "next_cursor": None}
  ])
  return client


@pytest.fixture
def mock_client_malformed_response():
  client = MagicMock()
  client.post = AsyncMock(return_value={})  # Missing 'results' and 'next_cursor'
  return client


# ========================
# Database Fixtures
# ========================

@pytest.fixture
def mock_db_w_props():
  db = MagicMock()
  db.fetch_rows = AsyncMock(return_value=[
    {"properties": {"Slutpris": {"number": 10}}},
    {"properties": {"Slutpris": {"number": 20}}},
  ])
  return db


@pytest.fixture
def mock_db_empty_list():
  db = MagicMock()
  db.fetch_rows = AsyncMock(return_value=[])
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