from unittest import skip
from unittest.mock import patch, MagicMock

from notion_task_runner.notion import NotionClient


@patch("notion_task_runner.tasks.task_config.TaskConfig.from_env")
@patch("requests.Session.post")
@skip
def test_post_sends_correct_headers_and_payload(mock_session_post,
    mock_from_env):
  mock_post_response = MagicMock()
  mock_post_response.status_code = 200
  mock_post_response.raise_for_status.return_value = None
  mock_post_response.json.return_value = {
    "recordMap": {
      "notion_user": {
        "dummy_user_id": {}
      }
    }
  }
  mock_session_post.return_value = mock_post_response

  mock_config = MagicMock()
  mock_config.notion_token_v2 = "some-token"
  mock_config.notion_api_key = "some-token"
  mock_from_env.return_value = mock_config

  sut = NotionClient()
  url = "https://api.notion.com/v1/fake-endpoint"
  payload = {"some": "data"}

  result = sut.post(url, json=payload)

  mock_session_post.assert_any_call(url, headers=None, data=None, json=payload)
  assert result == {"recordMap": {"notion_user": {"dummy_user_id": {}}}}


@patch("notion_task_runner.tasks.task_config.TaskConfig.from_env")
@patch("requests.Session.patch")
@patch("requests.Session.post")  # Needed because NotionClient calls this
@skip
def test_patch_sends_correct_headers_and_payload(mock_session_post, mock_patch, mock_from_env):
    # Mock the session.post call inside _create_authenticated_session
    mock_load_user_response = MagicMock()
    mock_load_user_response.status_code = 200
    mock_load_user_response.raise_for_status.return_value = None
    mock_load_user_response.json.return_value = {
        "recordMap": {
            "notion_user": {
                "dummy_user_id": {}
            }
        }
    }
    mock_session_post.return_value = mock_load_user_response

    # Properly mock the config
    mock_config = MagicMock()
    mock_config.notion_token_v2 = "some-real-token"
    mock_config.notion_api_key = "some-real-api-key"
    mock_from_env.return_value = mock_config

    # Mock the actual PATCH request
    mock_patch_response = MagicMock()
    mock_patch_response.status_code = 200
    mock_patch_response.json.return_value = {"success": True}
    mock_patch_response.raise_for_status.return_value = None
    mock_patch.return_value = mock_patch_response

    # Run the test
    sut = NotionClient()
    url = "https://api.notion.com/v1/blocks/abc123"
    payload = {"content": "update"}

    result = sut.patch(url, json=payload)

    mock_patch.assert_called_once_with(url, headers=None, json=payload)
    assert result == mock_patch_response