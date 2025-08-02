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

The project now includes a rich CLI interface with multiple commands:

### Main Commands

```bash
# Run all tasks (main entry point)
poetry run notion-task-runner run

# Or use the make target
make run

# Run with specific task filter
poetry run notion-task-runner run --task pas

# Dry run mode (see what would be executed)
poetry run notion-task-runner run --dry-run

# Validate configuration
poetry run notion-task-runner validate

# Check application health
poetry run notion-task-runner health

# List available tasks
poetry run notion-task-runner list-tasks
```

### Getting Help

```bash
# Show all available commands
poetry run notion-task-runner --help

# Get help for a specific command
poetry run notion-task-runner run --help
```

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

### Required Variables
- `NOTION_API_KEY` – Alternative to `NOTION_TOKEN_V2`, used to authenticate with Notion's API.
- `NOTION_TOKEN_V2` – Legacy Notion token used for some internal API interactions.
- `NOTION_SPACE_ID` – ID of the Notion workspace.
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_SECRET_JSON` – JSON credentials for Google Drive service account.
- `GOOGLE_DRIVE_ROOT_FOLDER_ID` – Root folder ID in Google Drive, used to resolve target paths or fallback location.

### Optional Variables
- `IS_PROD` – Set to "true" to enable production mode (default: "false")

### Configuration Validation

Use the built-in validation command to check your setup:

```bash
poetry run notion-task-runner validate
```

This will verify all required environment variables are set and test API connectivity.

## 🧪 Testing

The project has comprehensive test coverage with 185+ tests covering all major functionality.

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage report
make coverage

# Run only specific test
poetry run pytest tests/path/to/test.py::test_function_name

# Run tests marked for development
poetry run pytest -m only

# Watch mode for development
make watch-test
```

## 📝 Notes

- This project is intentionally hands-off.
- If it stops working, check logs or manually run `make run`.
- Scheduling is handled via GitHub Actions, so this runs automatically on a schedule.
