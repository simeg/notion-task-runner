from unittest.mock import patch

from notion_task_runner.notion import NotionClient


@patch("requests.post")
def test_post_sends_correct_headers_and_payload(mock_post, mock_post_response):
  mock_post.return_value = mock_post_response

  sut = NotionClient(token_v2="some-token", space_id="some-space-id")
  url = "https://api.notion.com/v1/fake-endpoint"
  payload = {"some": "data"}

  result = sut.post(url, json=payload)

  mock_post.assert_called_once_with(
      url,
      json=payload
  )
  assert result == {"key": "value"}


@patch("requests.patch")
def test_patch_sends_correct_headers_and_payload(mock_patch,
    mock_patch_response):
  mock_patch.return_value = mock_patch_response

  sut = NotionClient(token_v2="some-token", space_id="some-space-id")
  url = "https://api.notion.com/v1/blocks/abc123"
  payload = {"content": "update"}

  response = sut.patch(url, json=payload)

  mock_patch.assert_called_once_with(
      url,
      json=payload
  )
  assert response == mock_patch_response
