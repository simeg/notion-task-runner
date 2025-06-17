# Python tool commands through Poetry
POETRY_RUN=poetry run
SRC=src/

.PHONY: default check-style format-code check-types sort-imports lint coverage coverage-html test clean ci format help run

default: lint  ## Default target: run linting and type checks

check-style:  ## Run Ruff to check for lint issues
	$(POETRY_RUN) ruff check $(SRC)

fix-style:  ## Auto-fix lint issues with Ruff
	$(POETRY_RUN) ruff check $(SRC) --fix

format-code:  ## Run Black to format code
	$(POETRY_RUN) black $(SRC)

sort-imports:  ## Run isort to sort imports
	$(POETRY_RUN) isort $(SRC)

check-types:  ## Run MyPy to check type annotations
	$(POETRY_RUN) mypy $(SRC)

coverage:  ## Run tests with coverage output
	$(POETRY_RUN) pytest --cov=everdrive_version_notifier --cov-report=term-missing --cov-report=xml

coverage-html:  ## Run tests with HTML coverage report
	$(POETRY_RUN) pytest --cov=notion_task_runner --cov-report html

test:  ## Run all tests
	$(POETRY_RUN) pytest

lint: check-style format-code sort-imports check-types  ## Run all linting and type checks

format: fix-style format-code sort-imports  ## Run all formatters

clean:  ## Remove cache and coverage artifacts
	find . -type d -name '__pycache__' -exec rm -r {} +
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage

ci: coverage  ## Run all pre-checks for CI

run:  ## Run the Notion task runner script
	$(POETRY_RUN) python src/notion_task_runner/task_runner.py

help:  ## Show help info for each Makefile command
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'