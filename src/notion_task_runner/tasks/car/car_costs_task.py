from dataclasses import dataclass

import aiohttp

from notion_task_runner.constants import get_notion_block_update_url, get_notion_headers
from notion_task_runner.logging import get_logger
from notion_task_runner.notion import NotionDatabase
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
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
        client: AsyncNotionClient,
        db: NotionDatabase,
        config: TaskConfig,
        block_id: str | None = None,
    ) -> None:
        self.client = client
        self.db = db
        self.config = config
        self.block_id = block_id or self.UNPREDICTABLE_BLOCK_ID_2025

    async def run(self) -> None:
        """
        Execute the car costs update task.

        Calculates fixed and unpredictable costs for 2024 and 2025,
        then updates the corresponding Notion page blocks.
        """
        try:
            log.info("Starting Car Costs Task - calculating costs for 2024 and 2025")

            cost_data = {
                2024: {"fixed": 0, "unpredictable": 0},
                2025: {"fixed": 0, "unpredictable": 0},
            }

            # Calculate costs for each year
            for year in cost_data:
                log.debug(f"Calculating costs for year {year}")
                cost_data[year]["fixed"] = await self._calculate_total_cost(
                    self.FAST_KOSTNADER_DB_ID, year
                )
                cost_data[year]["unpredictable"] = await self._calculate_total_cost(
                    self.OFORUTSAGBARA_KOSTNADER_DB_ID, year
                )
                log.debug(
                    f"Year {year}: Fixed={cost_data[year]['fixed']}, Unpredictable={cost_data[year]['unpredictable']}"
                )

            # Define blocks to update
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

            # Update all blocks
            failed_updates = []
            for block_id, key, cost in block_map:
                try:
                    log.debug(f"Updating block {block_id} with {key}: {cost}")
                    await self._update_callout(block_id, key, cost)
                except Exception as e:
                    log.error(f"Failed to update block {block_id}: {e}")
                    failed_updates.append((block_id, key, e))

            if failed_updates:
                error_msg = f"Failed to update {len(failed_updates)} block(s)"
                log.error(error_msg)
                for block_id, key, error in failed_updates:
                    log.error(f"  - {key} ({block_id}): {error}")
                raise RuntimeError(error_msg)

            log.info("✅ Car Costs Task completed successfully")

        except Exception as e:
            log.error(f"❌ Car Costs Task failed: {e}")
            raise

    async def _update_callout(self, block_id: str, key: str, cost: int) -> None:
        """
        Update a callout block with cost information.

        Args:
            block_id: The ID of the block to update
            key: The display name for the cost type
            cost: The cost value to display

        Raises:
            aiohttp.ClientError: If the API request fails
        """
        url = get_notion_block_update_url(block_id)

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

        headers = get_notion_headers(self.config.notion_api_key)

        try:
            response = await self.client.patch(url, json=data, headers=headers)
            response.raise_for_status()
        except aiohttp.ClientError as e:
            log.error(f"Failed to update callout block {block_id}: {e}")
            raise

    async def _calculate_total_cost(self, db_id: str, year: int) -> int:
        costs = await self._fetch_costs(db_id, year)
        return sum(c.cost for c in costs)

    async def _fetch_costs(self, db_id: str, year: int | None = -1) -> list[Cost]:
        rows = await self.db.fetch_rows(db_id)
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
