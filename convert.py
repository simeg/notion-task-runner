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
4. Run this script which will convert it to UUID format and call the Notion API to fetch children of that block
5. Find the correct block ID in the response

## Can't find the block ID you're looking for?
If the block you want to update is inside a column, for example, you first
need to fetch the parent block ID (the column block ID) and then use that to
fetch children all the way until you find the block you want to update.

This script prints the type of block and that's useful for knowing if you've 
searched deep enough.
"""

import dotenv

dotenv.load_dotenv()

def convert_to_uuid(notion_id: str) -> str:
    """Convert a 32-character Notion ID to hyphenated UUID format."""
    if len(notion_id) != 32:
        raise ValueError(f"Invalid Notion ID: {notion_id}")
    return f"{notion_id[:8]}-{notion_id[8:12]}-{notion_id[12:16]}-{notion_id[16:20]}-{notion_id[20:]}"

# if __name__ == "__main__":
    # raw_id = "21baa18d640d804fa5b5e617807df483"
    #
    # print(convert_to_uuid(raw_id))
    # SystemExit(0)

if __name__ == "__main__":
    raw_id = "21baa18d640d80cd86bde61f2d3a89ba"

    try:
        uuid = convert_to_uuid(raw_id)
        uuid = "21eaa18d-640d-80b2-bce4-e9ba5e63fb39"

        import requests
        import os

        page_id = uuid  # Replace with your actual page ID
        url = f"https://api.notion.com/v1/blocks/{page_id}/children"

        notion_api_key = os.getenv("NOTION_API_KEY")

        if not notion_api_key:
            raise ValueError("You need to set the Notion API key manually.")

        headers = {
            "Authorization": f"Bearer {notion_api_key}",
            "Notion-Version": "2022-06-28"
        }

        response = requests.get(url, headers=headers)

        for block in response.json()["results"]:
            print(block["id"], block["type"])

        if response.status_code == 200:
            print(response.json())
            # Uncomment to pretty print the JSON response
            # import json
            # print(json.dumps(response.json(), indent=4))
        else:
            print(
                f"Request failed with status code {response.status_code}: {response.text}")

    except ValueError as e:
        print(f"Error: {e}")