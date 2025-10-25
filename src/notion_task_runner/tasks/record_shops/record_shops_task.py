"""
Task to update record shop opening hours callouts.

This task queries the record shops database, determines which shops are open
today and tomorrow based on their opening hours, and updates two callout blocks
with the formatted lists.
"""

from datetime import datetime, timedelta
from typing import Any

from notion_task_runner.constants import (
    get_notion_block_update_url,
    get_notion_headers,
)
from notion_task_runner.logging import get_logger
from notion_task_runner.notion import NotionDatabase
from notion_task_runner.notion.async_notion_client import AsyncNotionClient
from notion_task_runner.task import Task
from notion_task_runner.tasks.task_config import TaskConfig
from notion_task_runner.utils.http_client import HTTPClientMixin

log = get_logger(__name__)

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Custom ordering for city parts
CITY_PART_ORDER = [
    "Solna",
    "Bromma",
    "Södermalm",
    "Gamla Stan",
    "Lilla Essingen",
    "Kungsholmen",
    "S:t Eriksplan",
    "Odenplan",
    "Vanadisplan",
    "T-Centralen",
    "Nacka",
    "Söder om söder",
]


class RecordShopsTask(Task, HTTPClientMixin):
    """
    Task that updates record shop opening hours callouts.

    Queries the record shops database and updates two callout blocks:
    - One showing shops open today
    - One showing shops open tomorrow
    """

    DATABASE_ID = "284aa18d-640d-8032-83b5-d1b5424e70ac"
    CALLOUT_TODAY_ID = "292aa18d-640d-80d7-b372-ecea2b2fa6fc"
    CALLOUT_TOMORROW_ID = "292aa18d-640d-801f-8679-c641cd811a68"

    def __init__(
        self, client: AsyncNotionClient, db: NotionDatabase, config: TaskConfig
    ) -> None:
        self.client = client
        self.db = db
        self.config = config

    async def run(self) -> None:
        """
        Execute the record shops update task.

        Fetches all record shops, determines which are open today/tomorrow,
        and updates the callout blocks accordingly.
        """
        try:
            log.info("Starting Record Shops Task - fetching shop data")

            # Get current day and tomorrow
            today = datetime.now()
            tomorrow = today + timedelta(days=1)

            today_name = DAY_NAMES[today.weekday()]
            tomorrow_name = DAY_NAMES[tomorrow.weekday()]

            log.debug(
                f"Updating callouts for {today_name} (today) and {tomorrow_name} (tomorrow)"
            )

            # Fetch all shops from database
            shops = await self.db.fetch_rows(self.DATABASE_ID)
            log.debug(f"Retrieved {len(shops)} shops from database")

            # Get shops open today and tomorrow
            shops_today = self._get_shops_open_on_day(shops, today_name)
            shops_tomorrow = self._get_shops_open_on_day(shops, tomorrow_name)

            log.debug(
                f"Shops open today ({today_name}): {len(shops_today)}, "
                f"tomorrow ({tomorrow_name}): {len(shops_tomorrow)}"
            )

            # Update both callouts
            await self._update_callout(
                self.CALLOUT_TODAY_ID, today_name, shops_today, "today"
            )
            await self._update_callout(
                self.CALLOUT_TOMORROW_ID, tomorrow_name, shops_tomorrow, "tomorrow"
            )

            log.info("✅ Record Shops Task completed successfully")

        except Exception as e:
            log.error(f"❌ Record Shops Task failed: {e}")
            raise

    def _get_shops_open_on_day(
        self, shops: list[dict[str, Any]], day_name: str
    ) -> list[tuple[str, str, str]]:
        """
        Get list of shops open on a specific day in Stockholm.

        Args:
            shops: List of shop records from database
            day_name: Day name (Mon, Tue, Wed, Thu, Fri, Sat, Sun)

        Returns:
            List of tuples (shop_name, opening_hours, city_part) for Stockholm shops only
        """
        open_shops = []

        for shop in shops:
            name, hours_text, city, city_part = self._extract_shop_info(shop)

            # Only include Stockholm shops
            if city != "Stockholm":
                continue

            opening_hours = self._parse_opening_hours(hours_text, day_name)

            if opening_hours:
                open_shops.append((name, opening_hours, city_part))

        # Sort by custom city part order, then alphabetically by name
        def sort_key(shop: tuple[str, str, str]) -> tuple[int, str]:
            name, _, city_part = shop
            # Get index from CITY_PART_ORDER, use 999 for unknown city parts
            city_index = (
                CITY_PART_ORDER.index(city_part)
                if city_part in CITY_PART_ORDER
                else 999
            )
            return (city_index, name.lower())

        open_shops.sort(key=sort_key)
        return open_shops

    @staticmethod
    def _extract_shop_info(shop: dict[str, Any]) -> tuple[str, str, str, str]:
        """
        Extract shop name, opening hours, city, and city part from a shop record.

        Args:
            shop: Shop record from database

        Returns:
            Tuple of (shop_name, opening_hours_text, city, city_part)
        """
        properties = shop.get("properties", {})

        # Get shop name from title property
        title_prop = properties.get("Shop", {})
        title_array = title_prop.get("title", [])
        name = title_array[0].get("plain_text", "Unknown") if title_array else "Unknown"

        # Get opening hours from rich_text property
        hours_prop = properties.get("Opening Hours", {})
        hours_array = hours_prop.get("rich_text", [])
        hours_text = "".join([item.get("plain_text", "") for item in hours_array])

        # Get city from select property
        city_prop = properties.get("City", {})
        city_select = city_prop.get("select", {})
        city = city_select.get("name", "") if city_select else ""

        # Get city part from select property
        city_part_prop = properties.get("City Part", {})
        city_part_select = city_part_prop.get("select", {})
        city_part = (
            city_part_select.get("name", "Other") if city_part_select else "Other"
        )

        return name, hours_text, city, city_part

    def _parse_opening_hours(self, hours_text: str, day_name: str) -> str | None:
        """
        Parse opening hours text and extract hours for a specific day.

        Args:
            hours_text: Opening hours text (e.g., "Mon-Fri: 12-18; Sat: 12-16; Sun: Closed")
            day_name: Day name (Mon, Tue, Wed, Thu, Fri, Sat, Sun)

        Returns:
            Opening hours string (e.g., "12-18") or None if closed/not found
        """
        if not hours_text:
            return None

        # Handle special cases
        if "Appointment only" in hours_text:
            return None

        # Split by semicolons
        segments = hours_text.split(";")

        for segment in segments:
            segment = segment.strip()
            if not segment or ":" not in segment:
                continue

            days_part, hours_part = segment.split(":", 1)
            days_part = days_part.strip()
            hours_part = hours_part.strip()

            # Handle "Closed"
            if "Closed" in hours_part:
                if self._day_matches(days_part, day_name):
                    return None
                continue

            # Check if this segment applies to our day
            if self._day_matches(days_part, day_name):
                return hours_part

        return None

    @staticmethod
    def _day_matches(days_part: str, target_day: str) -> bool:
        """
        Check if a day specification matches the target day.

        Args:
            days_part: Day specification (e.g., "Mon", "Mon-Fri", "Sat-Sun")
            target_day: Target day name

        Returns:
            True if the specification matches the target day
        """
        # Direct match
        if target_day in days_part:
            return True

        # Range match (e.g., "Mon-Fri")
        if "-" in days_part:
            parts = days_part.split("-")
            if len(parts) == 2:
                start_day = parts[0].strip()
                end_day = parts[1].strip()

                # Find indices
                try:
                    start_idx = DAY_NAMES.index(start_day)
                    end_idx = DAY_NAMES.index(end_day)
                    target_idx = DAY_NAMES.index(target_day)

                    # Handle wrap-around (shouldn't normally happen)
                    if start_idx <= end_idx:
                        return start_idx <= target_idx <= end_idx
                    else:
                        return target_idx >= start_idx or target_idx <= end_idx
                except ValueError:
                    return False

        return False

    @staticmethod
    def _format_shop_list(shops: list[tuple[str, str, str]]) -> str:
        """
        Format list of shops into a readable string grouped by city part.

        Args:
            shops: List of tuples (shop_name, opening_hours, city_part)

        Returns:
            Formatted string with city parts as headers and shops as bullet points
        """
        if not shops:
            return "No shops open"

        lines = []
        current_city_part = None

        for name, hours, city_part in shops:
            # Add city part header when it changes
            if city_part != current_city_part:
                if current_city_part is not None:
                    lines.append("")  # Empty line between city parts
                lines.append(f"{city_part}")
                current_city_part = city_part

            lines.append(f"- {name} {hours}")

        return "\n".join(lines)

    async def _update_callout(
        self,
        block_id: str,
        day_name: str,
        shops: list[tuple[str, str, str]],
        label: str,
    ) -> None:
        """
        Update a callout block with shop information.

        Args:
            block_id: ID of the callout block to update
            day_name: Day name (Mon, Tue, etc.)
            shops: List of shops with opening hours and city parts
            label: Label for logging ("today" or "tomorrow")
        """
        url = get_notion_block_update_url(block_id)
        headers = get_notion_headers(self.config.notion_api_key)

        # Build rich text array with bold formatting
        rich_text = self._build_rich_text_with_formatting(shops, label, day_name)

        data = {"callout": {"rich_text": rich_text}}

        log.debug(f"Updating '{label}' callout with {len(shops)} shops")
        await self._make_notion_request("PATCH", url, headers, data)

    def _build_rich_text_with_formatting(
        self, shops: list[tuple[str, str, str]], label: str, day_name: str
    ) -> list[dict[str, Any]]:
        """
        Build rich text array with bold formatting for headers and simple list.

        Args:
            shops: List of shops with opening hours and city parts
            label: Label ("today" or "tomorrow")
            day_name: Day name (Mon, Tue, etc.)

        Returns:
            List of rich text objects with proper formatting
        """
        rich_text = []

        # Add bold "Open today (Mon):" header
        rich_text.append(
            {
                "type": "text",
                "text": {"content": f"Open {label} ({day_name}):\n\n"},
                "annotations": {"bold": True},
            }
        )

        if not shops:
            rich_text.append({"type": "text", "text": {"content": "No shops open"}})
            return rich_text

        current_city_part = None

        for name, hours, city_part in shops:
            # Add bold city part header when it changes
            if city_part != current_city_part:
                if current_city_part is not None:
                    rich_text.append({"type": "text", "text": {"content": "\n"}})
                rich_text.append(
                    {
                        "type": "text",
                        "text": {"content": f"{city_part}\n"},
                        "annotations": {"bold": True},
                    }
                )
                current_city_part = city_part

            # Add shop line
            rich_text.append(
                {"type": "text", "text": {"content": f"- {name} {hours}\n"}}
            )

        return rich_text
