import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("json_path", help="Path to service account JSON")
args = parser.parse_args()

with open(args.json_path, "r", encoding="utf-8") as f:
    json_data = json.load(f)

# Safely dump as a compact, escaped string
json_env_string = json.dumps(json_data)

print("Add this to your .env file:\n")
print(f"GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON='{json_env_string}'")