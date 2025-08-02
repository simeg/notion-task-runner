import os

import dotenv
import requests

dotenv.load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
ROW_BLOCK_ID = "21eaa18d-640d-8058-850e-f68839ab566c"  # a single table row block
url = f"https://api.notion.com/v1/blocks/{ROW_BLOCK_ID}"

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Replace with whatever values you want in each column
payload = {
    "table_row": {
        "cells": [
            [ { "type": "text", "text": { "content": "Updated Column 1" } } ],
            [ { "type": "text", "text": { "content": "1000000 kr" } } ],
        ]
    }
}

if __name__ == "__main__":
  response = requests.patch(url, headers=headers, json=payload)

  if response.status_code == 200:
      print("✅ Row updated!")
  else:
      print(f"❌ Failed: {response.status_code} - {response.text}")

