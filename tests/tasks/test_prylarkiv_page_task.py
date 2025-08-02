from unittest.mock import MagicMock

import aiohttp
import pytest

from notion_task_runner.logging import configure_logging
from notion_task_runner.tasks.prylarkiv.prylarkiv_page_task import PrylarkivPageTask
from notion_task_runner.tasks.task_config import TaskConfig

# Configure logging for tests to work with caplog
configure_logging(json_logs=False, log_level="DEBUG")


@pytest.fixture
def mock_config():
  config = MagicMock(spec=TaskConfig)
  config.notion_api_key = "fake-key"
  return config


@pytest.fixture
def mock_client():
  from unittest.mock import AsyncMock
  client = MagicMock()

  # Create a mock response
  mock_response = MagicMock()
  mock_response.status_code = 200
  mock_response.status = 200
  mock_response.text = AsyncMock(return_value="OK")
  mock_response.raise_for_status = MagicMock(return_value=None)

  client.patch = AsyncMock(return_value=mock_response)
  return client


@pytest.fixture
def mock_db():
  from unittest.mock import AsyncMock
  db = MagicMock()
  db.fetch_rows = AsyncMock(return_value=[{} for _ in range(5)])  # simulate 5 entries
  return db


@pytest.mark.asyncio
async def test_run_updates_block_successfully(mock_client, mock_db, mock_config):
  task = PrylarkivPageTask(client=mock_client, db=mock_db, config=mock_config)
  await task.run()

  # Verify the call was made
  mock_client.patch.assert_called_once()

  # Check the arguments
  call_args, call_kwargs = mock_client.patch.call_args

  # Check URL
  expected_url = f"https://api.notion.com/v1/blocks/{task.BLOCK_ID}"
  assert call_args[0] == expected_url

  # Check headers
  expected_headers = {
    "Authorization": f"Bearer {mock_config.notion_api_key}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
  }
  assert call_kwargs["headers"] == expected_headers

  # Check JSON content structure
  json_data = call_kwargs["json"]
  assert "callout" in json_data
  assert "rich_text" in json_data["callout"]

  rich_text = json_data["callout"]["rich_text"]
  assert len(rich_text) == 3

  # Check first element (prefix)
  assert rich_text[0]["text"]["content"] == "Nästa nummer på pryl: "
  assert rich_text[0]["annotations"]["bold"] is True

  # Check second element (number)
  assert rich_text[1]["text"]["content"] == "6"
  assert rich_text[1]["annotations"]["code"] is True

  # Check third element (timestamp) - just verify structure, not exact time
  assert rich_text[2]["text"]["content"].startswith(" (Senast uppdaterad: ")
  assert rich_text[2]["text"]["content"].endswith(")")
  assert rich_text[2]["annotations"]["italic"] is True
  assert rich_text[2]["annotations"]["color"] == "gray"


@pytest.mark.asyncio
async def test_run_logs_failure_on_bad_response(mock_client, mock_db, mock_config,
    caplog):
  # Configure mock to raise an exception (which is what the improved error handling does)
  def raise_for_status():
    raise aiohttp.ClientResponseError(
      request_info=MagicMock(),
      history=(),
      status=500,
      message="Internal Server Error"
    )
  mock_client.patch.return_value.raise_for_status = raise_for_status
  task = PrylarkivPageTask(client=mock_client, db=mock_db, config=mock_config)

  with caplog.at_level("INFO"), pytest.raises(aiohttp.ClientResponseError):  # Now expects an exception to be raised
    await task.run()

  assert "❌ Prylarkiv Task failed" in caplog.text
