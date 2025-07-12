# 🧠 Notion Task Runner [![Notion Task Runner](https://github.com/simeg/notion-task-runner/actions/workflows/notion-task-runner.yml/badge.svg)](https://github.com/simeg/notion-task-runner/actions/workflows/notion-task-runner.yml) [![codecov](https://codecov.io/gh/simeg/notion-task-runner/graph/badge.svg?token=QA0G9JV92I)](https://codecov.io/gh/simeg/notion-task-runner)

This project automates Notion page updates, exports and backups automatically.
It's easy to forget this exists — that's by design. It just runs.

![Full Flow](full_flow.png)

## 🤖 What it does

- Updates specific Notion pages based on custom logic.
- Triggers a full export of your Notion workspace.
- Waits for the export to finish and downloads the `.zip` file to a temporary location.
- Uploads the file to Google Drive.
- Logs everything neatly so you can inspect things if needed.

All logic is broken up into tasks that can be run independently or together.

## 🚀 How to run

To start the process manually:

```bash
make run
```

This is the main entry point that kicks off the entire export/download/upload pipeline.

## 🛠️ Make targets

| Target                 | Description                                                       |
|------------------------|-------------------------------------------------------------------|
| `make run`             | Run the task runner (trigger + download + optional upload)        |
| `make lint`            | Run all linters (style, types, imports)                           |
| `make format`          | Auto-format the code using `black` and `isort`                    |
| `make test`            | Run all tests                                                     |
| `make coverage`        | Run tests with coverage report                                    |
| `make check-types`     | Run `mypy` to validate typing                                     |
| `make sort-imports`    | Sort imports using `isort`                                        |
| `make check-style`     | Check formatting without making changes (black + isort)           |
| `make coverage-html`   | Generate an HTML report for test coverage                         |
| `make clean`           | Remove cache and temporary files                                  |
| `make ci`              | Run all CI checks (formatting, linting, type-checking, tests)     |
| `make help`            | Show all available `make` targets                                 |
| `make fix-style`       | Auto-fix lint issues using `ruff`                                 |
| `make format-code`     | Format code using `black`                                         |
| `make watch`           | Watch files and re-run the main script                            |
| `make watch-test`      | Watch files and re-run all tests                                  |
| `make watch-test-only` | Watch files and re-run only tests marked with `@pytest.mark.only` |

## 🔧 Configuration

All settings are pulled from environment variables and stored locally in `.env`. These include:

- `NOTION_API_KEY` – Alternative to `NOTION_TOKEN_V2`, used to authenticate with Notion's API.
- `NOTION_TOKEN_V2` – Legacy Notion token used for some internal API interactions.
- `NOTION_SPACE_ID` – ID of the Notion workspace.
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON` – JSON credentials for Google Drive service account.
- `GOOGLE_DRIVE_ROOT_FOLDER_ID` – Root folder ID in Google Drive, used to resolve target paths or
  fallback location.

## 🧪 Testing

You can run tests with:

```bash
make test
```

Or get a coverage report:

```bash
make coverage
```

## 📝 Notes

- This project is intentionally hands-off.
- If it stops working, check logs or manually run `make run`.
- Scheduling is handled via GitHub Actions, so this runs automatically on a schedule.
