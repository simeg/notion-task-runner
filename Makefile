# Python tool commands through Poetry
POETRY_RUN=poetry run
SRC=src/
WATCH_FILES = find . -type f

.PHONY: default setup check-style fix-style format-code sort-imports check-types coverage coverage-html test lint format clean ci run watch watch-test watch-test-only help

## Default target: run linting and type checks
default: lint

## Setup: Install Poetry dependencies and verify installation
setup:
	@echo "Installing dependencies with Poetry..."
	poetry install
	@echo "Verifying installation..."
	$(POETRY_RUN) ruff --version
	$(POETRY_RUN) black --version
	$(POETRY_RUN) mypy --version
	@echo "Setup complete! You can now run 'make ci' or other targets."

## Run Ruff to check for lint issues
check-style:
	$(POETRY_RUN) ruff check $(SRC)

convert:
	$(POETRY_RUN) python convert.py

## Auto-fix lint issues with Ruff
fix-style:
	$(POETRY_RUN) ruff check $(SRC) --fix

## Run Black to format code
format-code:
	$(POETRY_RUN) black $(SRC)

## Run isort to sort imports
sort-imports:
	$(POETRY_RUN) isort $(SRC)

## Run MyPy to check type annotations
check-types:
	$(POETRY_RUN) mypy $(SRC)

## Run tests with coverage output
coverage:
	$(POETRY_RUN) pytest --cov=notion_task_runner --cov-report=term-missing --cov-report=xml

## Run tests with HTML coverage report
coverage-html:
	$(POETRY_RUN) pytest --cov=notion_task_runner --cov-report html

## Run all tests
test:
	$(POETRY_RUN) pytest

## Run all linting and type checks
lint: check-style format-code sort-imports check-types

## Run all formatters
format: fix-style format-code sort-imports

## Remove cache and coverage artifacts
clean:
	find . -type d -name '__pycache__' -exec rm -r {} +
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage

## Run all pre-checks for CI
ci: lint run coverage

## Run the Notion task runner with INFO level logging
run:
	$(POETRY_RUN) notion-task-runner --log-level INFO run

## Run the Notion task runner with DEBUG level logging
run-debug:
	$(POETRY_RUN) notion-task-runner --log-level DEBUG run

## Watch for changes and re-run the main script
watch:
	$(WATCH_FILES) | entr -c make run

## Watch for changes and re-run all tests
watch-test:
	$(WATCH_FILES) | entr -c make test

## Watch for changes and run only tests marked with @pytest.mark.only
watch-test-only:
	$(WATCH_FILES) | entr -c poetry run pytest -m only

## Show help info for each Makefile command
help:
	@awk ' \
		BEGIN { FS = ":.*##"; print "Available targets:\n" } \
		/^[a-zA-Z0-9_-]+:.*##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } \
		/^##/ { sub(/^## /, "", $$0); getline line; if (match(line, /^([a-zA-Z0-9_-]+):/)) printf "  \033[36m%-20s\033[0m %s\n", substr(line, RSTART, RLENGTH-1), $$0 } \
	' Makefile
