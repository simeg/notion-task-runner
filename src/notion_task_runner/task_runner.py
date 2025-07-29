"""
Task coordination and execution using dependency injection.

Refactored to use the dependency injection container for better
testability and separation of concerns.
"""

import asyncio
import concurrent.futures
from typing import Any

from dependency_injector.wiring import Provide, inject
from dotenv import load_dotenv

from notion_task_runner.container import ApplicationContainer
from notion_task_runner.logging import configure_logging, get_logger
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)

load_dotenv(override=False)


class TaskRunner:
    """
    Coordinates the execution of multiple Notion-related tasks concurrently.

    This class uses dependency injection to manage task instances and
    executes them in parallel using a ThreadPoolExecutor. Any exceptions
    are logged without halting execution of other tasks.
    """

    def __init__(self, tasks: list[Any], config: TaskConfig) -> None:
        # Only configure logging if we're running directly (not via CLI)
        # The CLI will handle logging configuration
        if __name__ == "__main__":
            if config.is_prod:
                log.info("Running in production mode")
                configure_logging(json_logs=True, log_level="INFO")
            else:
                log.info("Running in development mode")
                configure_logging(json_logs=False, log_level="DEBUG")
        else:
            # Just log the mode without reconfiguring logging
            mode = "production" if config.is_prod else "development"
            log.info(f"Running in {mode} mode")

        # Validate Notion connectivity at startup
        if not config.validate_notion_connectivity():
            log.error("Failed to validate Notion API connectivity")
            raise RuntimeError("Notion API validation failed")

        self.tasks = tasks
        self.config = config

        log.debug(
            f"TaskRunner initialized with {len(self.tasks)} tasks",
            task_count=len(self.tasks),
        )

    def run(self) -> None:
        """Execute all tasks concurrently."""
        log.debug("Starting task execution")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(task.run) for task in self.tasks]
            concurrent.futures.wait(futures)

            successful_tasks = 0
            failed_tasks = 0

            for i, future in enumerate(futures):
                task_name = self.tasks[i].__class__.__name__
                try:
                    future.result()
                    successful_tasks += 1
                    log.debug("Task completed successfully", task=task_name)
                except Exception as e:
                    failed_tasks += 1
                    log.error(
                        "Task failed", task=task_name, error=str(e), exc_info=True
                    )

            log.debug(
                "Task execution completed",
                successful_tasks=successful_tasks,
                failed_tasks=failed_tasks,
                total_tasks=len(self.tasks),
            )

    async def run_async(self) -> None:
        """Execute all tasks asynchronously."""
        log.debug("Starting async task execution")

        # Execute all tasks concurrently using asyncio.gather
        results = await asyncio.gather(
            *[task.run() for task in self.tasks], return_exceptions=True
        )

        successful_tasks = 0
        failed_tasks = 0

        for i, result in enumerate(results):
            task_name = self.tasks[i].__class__.__name__
            if isinstance(result, Exception):
                failed_tasks += 1
                log.error(
                    "Task failed", task=task_name, error=str(result), exc_info=True
                )
            else:
                successful_tasks += 1
                log.debug("Task completed successfully", task=task_name)

        log.debug(
            "Async task execution completed",
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            total_tasks=len(self.tasks),
        )


@inject
def create_task_runner(
    tasks: list[Any] = Provide[ApplicationContainer.all_tasks],
    config: TaskConfig = Provide[ApplicationContainer.task_config],
) -> TaskRunner:
    """Factory function to create TaskRunner with injected dependencies."""
    return TaskRunner(tasks=tasks, config=config)


if __name__ == "__main__":
    # Initialize DI container
    container = ApplicationContainer()
    container.wire(modules=[__name__])

    # Create and run task runner
    runner = create_task_runner()
    asyncio.run(runner.run_async())
