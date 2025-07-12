from dataclasses import dataclass
from typing import Any

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient, NotionDatabase
from notion_task_runner.task import Task
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


@dataclass
class Cost:
    name: str
    cost: int
    purchased_date: str


class CarCostsTask(Task):
    UNPREDICTABLE_BLOCK_ID_2025 = "21daa18d-640d-80ea-96b3-d68d178ddc2f"
    FIXED_BLOCK_ID_2025 = "21daa18d-640d-80c1-aefc-e5e9340b58c9"
    UNPREDICTABLE_BLOCK_ID_2024 = "21daa18d-640d-80fd-b901-c6e1ac5d801c"
    FIXED_BLOCK_ID_2024 = "21daa18d-640d-801e-ad2d-d1867cf9fe4e"
    OFORUTSAGBARA_KOSTNADER_DB_ID = "21baa18d-640d-804f-a5b5-e617807df483"
    FAST_KOSTNADER_DB_ID = "21caa18d-640d-8098-96fb-eff584db197f"

    def __init__(
        self,
        client: NotionClient,
        db: NotionDatabase,
        config: TaskConfig,
        block_id: str | None = None,
    ) -> None:
        self.client = client
        self.db = db
        self.config = config
        self.block_id = block_id or self.UNPREDICTABLE_BLOCK_ID_2025

    def run(self) -> None:
        cost_data = {
            2024: {"fixed": 0, "unpredictable": 0},
            2025: {"fixed": 0, "unpredictable": 0},
        }

        for year in cost_data:
            cost_data[year]["fixed"] = self._calculate_total_cost(
                self.FAST_KOSTNADER_DB_ID, year
            )
            cost_data[year]["unpredictable"] = self._calculate_total_cost(
                self.OFORUTSAGBARA_KOSTNADER_DB_ID, year
            )

        block_map = [
            (
                self.UNPREDICTABLE_BLOCK_ID_2025,
                "Oförutsägbara Kostnader",
                cost_data[2025]["unpredictable"],
            ),
            (self.FIXED_BLOCK_ID_2025, "Fasta Kostnader", cost_data[2025]["fixed"]),
            (
                self.UNPREDICTABLE_BLOCK_ID_2024,
                "Oförutsägbara Kostnader",
                cost_data[2024]["unpredictable"],
            ),
            (self.FIXED_BLOCK_ID_2024, "Fasta Kostnader", cost_data[2024]["fixed"]),
        ]

        responses = []
        for block_id, key, cost in block_map:
            response = self._update_callout(block_id, key, cost)
            responses.append(response)

        success = all(response.status_code == 200 for response in responses)

        if not success:
            log.error("Failed to update one or more blocks.")
            for response in responses:
                log.error(f"Response: {response.status_code} - {response.text}")

        log.info(
            "✅ Updated Bil Kostnader!" if success else "❌ Failed to update Bil page."
        )

    def _update_callout(self, block_id: str, key: str, cost: int) -> Any:
        url = f"https://api.notion.com/v1/blocks/{block_id}"

        data = {
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"{key}: "},
                        "annotations": {"bold": True},
                    },
                    {
                        "type": "text",
                        "text": {"content": f"{cost:,}".replace(",", " ") + " kr"},
                        "annotations": {"bold": False},
                    },
                ]
            }
        }

        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.config.notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        response = self.client.patch(url, json=data, headers=headers)
        return response

    def _calculate_total_cost(self, db_id: str, year: int) -> int:
        return sum(c.cost for c in self._fetch_costs(db_id, year))

    def _fetch_costs(self, db_id: str, year: int | None = -1) -> list[Cost]:
        rows = self.db.fetch_rows(db_id)
        cost_list = []

        for row in rows:
            props = row["properties"]
            name = (
                props["Komponent / Åtgärd"]["title"][0]["plain_text"]
                if props["Komponent / Åtgärd"]["title"]
                else ""
            )
            cost = props["Kostnad"]["number"]
            purchased_date = props["Inköpt / Åtgärdad"]["date"]["start"]
            # Ignore rows that are not in the specified year, unless no year was specified
            if not purchased_date.startswith(str(year)) and year != -1:
                continue
            cost_list.append(Cost(name=name, cost=cost, purchased_date=purchased_date))

        return cost_list
