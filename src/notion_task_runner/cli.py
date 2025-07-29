"""
Enhanced CLI interface using Typer for the Notion Task Runner.

Provides a rich command-line interface with better help text, validation,
and multiple command options for different operational modes.
"""

import asyncio
import sys
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from notion_task_runner.container import ApplicationContainer
from notion_task_runner.logging import configure_logging, get_logger
from notion_task_runner.task_runner import TaskRunner

app = typer.Typer(
    name="notion-task-runner",
    help="Automatically manage and backup Notion pages",
    rich_markup_mode="rich",
)

console = Console()


def version_callback(value: bool) -> None:
    """Show version information."""
    if value:
        console.print("notion-task-runner version 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool, typer.Option("--version", callback=version_callback, help="Show version")
    ] = False,
    json_logs: Annotated[
        bool, typer.Option("--json-logs", help="Output logs in JSON format")
    ] = False,
    log_level: Annotated[
        str,
        typer.Option(
            "--log-level", help="Set logging level (DEBUG, INFO, WARNING, ERROR)"
        ),
    ] = "INFO",
) -> None:
    """Notion Task Runner - Automatically manage and backup your Notion pages."""
    configure_logging(json_logs=json_logs, log_level=log_level)


@app.command()
def run(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be done without executing"),
    ] = False,
    task_filter: Annotated[
        str,
        typer.Option("--task", help="Run only specific task (e.g., 'pas', 'stats')"),
    ] = "",
) -> None:
    """
    Run all Notion tasks or filter by specific task types.

    This command executes the configured tasks to update your Notion pages
    with calculated values and statistics.
    """

    async def run_async_tasks() -> None:
        log = get_logger(__name__)

        try:
            # Initialize DI container
            container = ApplicationContainer()
            container.wire(modules=["notion_task_runner.task_runner"])

            # Get tasks and config from container
            tasks = container.all_tasks()
            config = container.task_config()

            # Filter tasks if requested
            if task_filter:
                filtered_tasks = [
                    task
                    for task in tasks
                    if task_filter.lower() in task.__class__.__name__.lower()
                ]
                if not filtered_tasks:
                    console.print(
                        f"[red]No tasks found matching filter: {task_filter}[/red]"
                    )
                    raise typer.Exit(1)
                tasks = filtered_tasks

            if dry_run:
                console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
                _show_task_plan(tasks)
                return

            # Validate connectivity
            with console.status("Validating Notion connectivity..."):
                if not config.validate_notion_connectivity():
                    console.print(
                        "[red]❌ Failed to validate Notion API connectivity[/red]"
                    )
                    raise typer.Exit(1)
                console.print("[green]✅ Notion API connectivity validated[/green]")

            # Run tasks
            runner = TaskRunner(tasks=tasks, config=config)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task_progress = progress.add_task("Running Notion tasks...", total=None)
                await runner.run_async()
                progress.update(task_progress, completed=True)

            console.print("[green]✅ All tasks completed successfully[/green]")

        except Exception as e:
            log.error(f"Task execution failed: {e}")
            console.print(f"[red]❌ Task execution failed: {e}[/red]")
            raise typer.Exit(1) from e

    # Run the async function
    asyncio.run(run_async_tasks())


@app.command()
def validate() -> None:
    """
    Validate configuration and API connectivity.

    This command checks that all required environment variables are set
    and that the Notion API is accessible with the provided credentials.
    """
    log = get_logger(__name__)

    try:
        container = ApplicationContainer()
        config = container.task_config()

        console.print("🔍 Validating configuration...")

        # Check required environment variables
        validation_results = [
            ("Notion Space ID", bool(config.notion_space_id)),
            ("Notion Token V2", bool(config.notion_token_v2)),
            ("Notion API Key", bool(config.notion_api_key)),
            (
                "Google Drive Service Account",
                bool(config.google_drive_service_account_secret_json),
            ),
            ("Google Drive Root Folder", bool(config.google_drive_root_folder_id)),
        ]

        # Test Notion connectivity
        with console.status("Testing Notion API connectivity..."):
            notion_connectivity = config.validate_notion_connectivity()

        validation_results.append(("Notion API Connectivity", notion_connectivity))

        # Display results
        table = Table(title="Configuration Validation Results")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="bold")

        all_valid = True
        for component, is_valid in validation_results:
            status = "[green]✅ Valid[/green]" if is_valid else "[red]❌ Invalid[/red]"
            table.add_row(component, status)
            if not is_valid:
                all_valid = False

        console.print(table)

        if all_valid:
            console.print(
                "\n[green]🎉 All validations passed! Your configuration is ready.[/green]"
            )
            log.info("Configuration validation successful")
        else:
            console.print(
                "\n[red]❌ Some validations failed. Please check your configuration.[/red]"
            )
            log.error("Configuration validation failed")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]❌ Validation failed: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def list_tasks() -> None:
    """
    List all available tasks and their descriptions.

    Shows information about each task type that can be executed,
    including what Notion pages they update.
    """
    tasks_info = [
        ("PAS Page Task", "Updates 'Prylar Att Sälja' page with pricing data"),
        ("Prylarkiv Page Task", "Manages 'Prylarkiv' page for items and collections"),
        ("Car Costs Task", "Calculates and updates vehicle-related expenses"),
        ("Stats Task", "Generates and updates statistical summaries"),
        ("Audiophile Page Task", "Updates audio equipment pages with totals"),
    ]

    table = Table(title="Available Tasks")
    table.add_column("Task Name", style="cyan")
    table.add_column("Description", style="white")

    for name, description in tasks_info:
        table.add_row(name, description)

    console.print(table)


@app.command()
def health() -> None:
    """
    Check application health and service connectivity.

    Performs comprehensive health checks including API connectivity,
    configuration validation, and system resource checks.
    """
    log = get_logger(__name__)

    try:
        container = ApplicationContainer()
        config = container.task_config()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            health_task = progress.add_task("Performing health checks...", total=4)

            # Check 1: Configuration
            progress.update(health_task, description="Checking configuration...")
            config_ok = all(
                [config.notion_space_id, config.notion_token_v2, config.notion_api_key]
            )
            progress.advance(health_task)

            # Check 2: Notion API
            progress.update(health_task, description="Testing Notion API...")
            notion_ok = config.validate_notion_connectivity()
            progress.advance(health_task)

            # Check 3: File system
            progress.update(health_task, description="Checking file system access...")
            try:
                temp_file = Path.cwd() / ".health_check"
                temp_file.write_text("test")
                temp_file.unlink()
                fs_ok = True
            except Exception:
                fs_ok = False
            progress.advance(health_task)

            # Check 4: Memory/CPU (basic)
            progress.update(health_task, description="Checking system resources...")
            try:
                import psutil

                memory_ok = psutil.virtual_memory().percent < 90
                cpu_ok = psutil.cpu_percent(interval=1) < 90
                system_ok = memory_ok and cpu_ok
            except ImportError:
                system_ok = True  # Skip if psutil not available
            progress.advance(health_task)

        # Display results
        checks = [
            ("Configuration", config_ok),
            ("Notion API", notion_ok),
            ("File System", fs_ok),
            ("System Resources", system_ok),
        ]

        table = Table(title="Health Check Results")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="bold")

        all_healthy = True
        for component, is_healthy in checks:
            status = (
                "[green]✅ Healthy[/green]" if is_healthy else "[red]❌ Unhealthy[/red]"
            )
            table.add_row(component, status)
            if not is_healthy:
                all_healthy = False

        console.print(table)

        if all_healthy:
            console.print("\n[green]🎉 All health checks passed![/green]")
            log.info("Health check successful")
        else:
            console.print("\n[red]❌ Some health checks failed.[/red]")
            log.warning("Health check failed")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]❌ Health check failed: {e}[/red]")
        raise typer.Exit(1) from e


def _show_task_plan(tasks: list[Any]) -> None:
    """Show what tasks would be executed in dry-run mode."""
    table = Table(title="Execution Plan (Dry Run)")
    table.add_column("Task", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Description", style="white")

    for task in tasks:
        task_name = task.__class__.__name__
        task_type = task_name.replace("Task", "").replace("Page", "")
        description = f"Would execute {task_name}"
        table.add_row(task_name, task_type, description)

    console.print(table)


def main_cli() -> None:
    """Entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main_cli()
