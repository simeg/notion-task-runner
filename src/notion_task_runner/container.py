"""
Dependency injection container for the Notion Task Runner.

Provides centralized configuration and dependency management using
dependency-injector for better testability and maintainability.
"""

from dependency_injector import containers, providers

from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.notion.notion_database import NotionDatabase
from notion_task_runner.tasks.audiophile.audiophile_page_task import AudiophilePageTask
from notion_task_runner.tasks.car.car_costs_task import CarCostsTask
from notion_task_runner.tasks.pas.pas_page_task import PASPageTask
from notion_task_runner.tasks.pas.sum_calculator import SumCalculator
from notion_task_runner.tasks.prylarkiv.prylarkiv_page_task import PrylarkivPageTask
from notion_task_runner.tasks.record_shops.record_shops_task import RecordShopsTask
from notion_task_runner.tasks.statistics.stats_task import StatsTask
from notion_task_runner.tasks.task_config import TaskConfig


class ApplicationContainer(containers.DeclarativeContainer):
    """Application dependency injection container."""

    # Configuration
    wiring_config = containers.WiringConfiguration(
        modules=[
            "notion_task_runner.task_runner",
            "notion_task_runner.cli",
        ]
    )

    # Configuration provider
    config = providers.Configuration()

    # Task configuration
    task_config = providers.Singleton(TaskConfig.from_env)

    # Core clients
    async_notion_client = providers.Singleton(AsyncNotionClient, config=task_config)

    # Database interface
    notion_database = providers.Factory(
        NotionDatabase, client=async_notion_client, config=task_config
    )

    # Calculators
    sum_calculator = providers.Singleton(SumCalculator)

    # Tasks
    pas_page_task = providers.Factory(
        PASPageTask,
        client=async_notion_client,
        db=notion_database,
        config=task_config,
        calculator=sum_calculator,
    )

    prylarkiv_page_task = providers.Factory(
        PrylarkivPageTask,
        client=async_notion_client,
        db=notion_database,
        config=task_config,
    )

    car_costs_task = providers.Factory(
        CarCostsTask, client=async_notion_client, db=notion_database, config=task_config
    )

    stats_task = providers.Factory(
        StatsTask, client=async_notion_client, db=notion_database, config=task_config
    )

    audiophile_page_task = providers.Factory(
        AudiophilePageTask,
        client=async_notion_client,
        db=notion_database,
        config=task_config,
        calculator=sum_calculator,
    )

    record_shops_task = providers.Factory(
        RecordShopsTask,
        client=async_notion_client,
        db=notion_database,
        config=task_config,
    )

    # Task list provider
    all_tasks = providers.List(
        pas_page_task,
        prylarkiv_page_task,
        car_costs_task,
        stats_task,
        audiophile_page_task,
        record_shops_task,
    )
