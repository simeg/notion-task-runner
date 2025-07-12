from typing import ClassVar

from requests import Response

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient
from notion_task_runner.task import Task
from notion_task_runner.tasks.car.car_model import Car
from notion_task_runner.tasks.car.car_scraper import CarScraper
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class CarMetadataTask(Task):
    CAR_REG_NUMBER: ClassVar[str] = "YMO642"
    BLOCK_ID: ClassVar[str] = "21caa18d-640d-8065-9f84-c9ba25d614c6"
    KEYS_AND_BLOCK_IDS: ClassVar[list[tuple[str, str]]] = [
        ("Regnr", "21eaa18d-640d-8058-850e-f68839ab566c"),
        ("Modell", "21eaa18d-640d-8081-b457-e9362cfd32ad"),
        ("År", "21eaa18d-640d-80a2-8ad5-c2279ba8f69a"),
        ("Besiktigad", "21eaa18d-640d-809f-8c95-de05cb7001c2"),
        ("Nästa besiktning", "21eaa18d-640d-8014-a739-cf745eaa0f77"),
        ("Årlig skatt", "21eaa18d-640d-8093-b1cc-e9f9fa5fba61"),
        ("Först registrerad", "21eaa18d-640d-80d4-a71f-e2a16b1e307c"),
        ("Mätarställning", "21eaa18d-640d-802c-b423-d63359e95d56"),
        ("Hästkrafter", "21eaa18d-640d-80b9-a2c3-da4fdd9c0929"),
    ]

    def __init__(
        self, client: NotionClient, config: TaskConfig, block_id: str | None = None
    ) -> None:
        self.client = client
        self.config = config
        self.block_id = block_id or self.BLOCK_ID

    def run(self) -> None:
        responses = self._update_car_metadata()
        success = all(response.status_code == 200 for response in responses)

        log.info(
            "✅ Updated Bil metadata!" if success else "❌ Failed to update Bil page."
        )

    def _update_car_metadata(self) -> list[Response]:
        scraper = CarScraper(self.client, self.config)
        car: Car = scraper.scrape(self.CAR_REG_NUMBER)
        table_lines = [
            ("Regnr", car.reg_number, "21eaa18d-640d-8058-850e-f68839ab566c"),
            ("Modell", car.model, "21eaa18d-640d-8081-b457-e9362cfd32ad"),
            ("År", str(car.model_year), "21eaa18d-640d-80a2-8ad5-c2279ba8f69a"),
            ("Besiktigad", car.inspected_at, "21eaa18d-640d-809f-8c95-de05cb7001c2"),
            (
                "Nästa besiktning",
                car.next_inspection_latest_at,
                "21eaa18d-640d-8014-a739-cf745eaa0f77",
            ),
            (
                "Årlig skatt",
                f"{car.tax_yearly_sek:,}".replace(",", " ") + " SEK",
                "21eaa18d-640d-8093-b1cc-e9f9fa5fba61",
            ),
            (
                "Först registrerad",
                car.registered_at,
                "21eaa18d-640d-80d4-a71f-e2a16b1e307c",
            ),
            (
                "Mätarställning",
                f"{car.mileage_km:,}".replace(",", " ") + " km",
                "21eaa18d-640d-802c-b423-d63359e95d56",
            ),
            (
                "Hästkrafter",
                f"{car.horsepower} hk",
                "21eaa18d-640d-80b9-a2c3-da4fdd9c0929",
            ),
        ]
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.config.notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        responses = []
        for label, value, row_block_id in table_lines:
            url = f"https://api.notion.com/v1/blocks/{row_block_id}"
            payload = {
                "table_row": {
                    "cells": [
                        [
                            {
                                "type": "text",
                                "annotations": {"bold": True},
                                "text": {"content": label},
                            }
                        ],
                        [{"type": "text", "text": {"content": value}}],
                    ]
                }
            }
            response: Response = self.client.patch(url, json=payload, headers=headers)
            if response.status_code != 200:
                log.error(f"Failed to update block {row_block_id}: {response.text}")
            else:
                log.info(f"Updated block {row_block_id} with {label}: {value}")
            responses.append(response)

        return responses
