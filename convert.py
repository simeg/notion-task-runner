"""
How to find Database ID:
1. Add page to this integration: https://www.notion.so/profile/integrations/internal/07d3b3f7f95d414cac6f40e98cbf0e2d
2. Go to page, click settings icon on DB -> "Copy link to view"
3. Get the ID from the URL, it should be a 32-character string.
4. Convert it here to get the UUID format
"""

"""
How to find Block ID:
1. Open the Notion page in your browser
2. Get link to any block by right-clicking on it and selecting "Copy link"
3. Get the ID from the URL, it should be a 32-character string
4. Convert it here to get the UUID format
5. Call this and find the block ID in the output

curl -X GET 'https://api.notion.com/v1/blocks/{page_id}/children' \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28"
"""

def convert_to_uuid(notion_id: str) -> str:
    """Convert a 32-character Notion ID to hyphenated UUID format."""
    if len(notion_id) != 32:
        raise ValueError(f"Invalid Notion ID: {notion_id}")
    return f"{notion_id[:8]}-{notion_id[8:12]}-{notion_id[12:16]}-{notion_id[16:20]}-{notion_id[20:]}"


if __name__ == "__main__":
    raw_ids = [
    "1fdaa18d640d80b9949dc635e356e994"
    ]

    for raw_id in raw_ids:
        try:
            print(convert_to_uuid(raw_id))
        except ValueError as e:
            print(f"Error: {e}")