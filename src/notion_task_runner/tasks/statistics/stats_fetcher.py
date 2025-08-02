import asyncio
import re
from dataclasses import dataclass
from functools import reduce
from typing import Any

from notion_task_runner.logging import get_logger
from notion_task_runner.notion import NotionDatabase
from notion_task_runner.tasks.statistics.models import (
    Adapter,
    Cable,
    CableType,
    Pryl,
    Vinyl,
    Watch,
    WorkspaceStats,
)


@dataclass(frozen=True)
class DetailedWorkspaceStats:
    """Detailed workspace statistics with individual item collections."""

    watches: list[Watch]
    cables: list[Cable]
    adapters: list[Adapter]
    prylar: list[Pryl]
    vinyls: list[Vinyl]
    total_cable_length_m: float = 0.0


log = get_logger(__name__)


class StatsFetcher:
    WATCHES_DB_ID = "1f7aa18d-640d-80f8-afa4-cf6f82149afa"
    CABLES_DB_ID = "1f4aa18d-640d-8037-b164-db4f407ccb88"
    PRYLAR_DB_ID = "1fdaa18d-640d-80e5-ae53-c80e2dc41474"
    VINYLS_DB_ID = "1f3aa18d-640d-8180-8395-d7e6ea5e45e1"

    def __init__(self, db: NotionDatabase) -> None:
        self.db = db

    @staticmethod
    def _get_plain_text(props: dict[str, Any], key: str, fallback: str = "") -> Any:
        field = props.get(key, {})
        if field.get("title"):
            return field["title"][0]["plain_text"]
        elif field.get("rich_text"):
            return field["rich_text"][0]["plain_text"]
        return fallback

    async def fetch(self) -> DetailedWorkspaceStats:
        # Fetch all data concurrently using asyncio
        rows_watches, rows_cables, rows_prylar, rows_vinyls = await asyncio.gather(
            self.db.fetch_rows(self.WATCHES_DB_ID),
            self.db.fetch_rows(self.CABLES_DB_ID),
            self.db.fetch_rows(self.PRYLAR_DB_ID),
            self.db.fetch_rows(self.VINYLS_DB_ID),
        )

        watches = self._parse_watches(rows_watches)
        cables = self._parse_cables(rows_cables)
        adapters = self._parse_adapters(rows_cables)
        prylar = self._parse_prylar(rows_prylar)
        vinyls = self._parse_vinyls(rows_vinyls)

        total_cable_length_m = self._total_cable_length(cables)

        return DetailedWorkspaceStats(
            watches=watches,
            cables=cables,
            adapters=adapters,
            prylar=prylar,
            vinyls=vinyls,
            total_cable_length_m=total_cable_length_m,
        )

    async def fetch_summary_stats(self) -> WorkspaceStats:
        """Fetch aggregated workspace statistics."""
        detailed_stats = await self.fetch()

        total_watch_cost = sum(watch.cost for watch in detailed_stats.watches)
        total_vinyl_cost = sum(vinyl.cost or 0 for vinyl in detailed_stats.vinyls)

        return WorkspaceStats(
            total_watches=len(detailed_stats.watches),
            total_watch_cost=total_watch_cost,
            total_cables=len(detailed_stats.cables),
            total_adapters=len(detailed_stats.adapters),
            total_prylar=len(detailed_stats.prylar),
            total_vinyl_records=len(detailed_stats.vinyls),
            total_vinyl_cost=total_vinyl_cost,
        )

    def _parse_watches(self, rows: list[dict[Any, Any]]) -> list[Watch]:
        watches = []
        for row in rows:
            props = row["properties"]
            name = self._get_plain_text(props, "Name")
            if not name or not name.strip():
                log.warning(
                    f"Skipping watch with empty name in row {row.get('id', 'unknown')}"
                )
                continue

            cost = props["Kostnad (SEK)"]["number"]
            if cost is None:
                log.warning(f"Skipping watch '{name}' with missing cost")
                continue

            purchased_date = props["Köpt den"]["date"]["start"]
            if not purchased_date:
                log.warning(f"Skipping watch '{name}' with missing purchase date")
                continue

            watches.append(Watch(name=name, cost=cost, purchased_date=purchased_date))
        return watches

    def _parse_cables(self, rows: list[dict[Any, Any]]) -> list[Cable]:
        cables = []
        for row in rows:
            props = row["properties"]
            if props["is_adapter"]["checkbox"]:
                continue

            raw_type = self._get_plain_text(props, "Type")
            if not raw_type:
                log.debug(
                    f"Missing cable type in row {row.get('id', 'unknown')}, defaulting to OTHER"
                )
                cable_type = CableType.OTHER
            else:
                cable_type = self._parse_cable_type(raw_type)

            length = props["Length (cm)"]["number"]
            if length is None or length <= 0:
                log.debug(
                    f"Skipping cable with invalid length: {length} in row {row.get('id', 'unknown')}"
                )
                continue

            cables.append(Cable(type=cable_type, length_cm=length))
        return cables

    @staticmethod
    def _parse_cable_type(value: str) -> CableType:
        value = value.lower()
        if "3.5mm" in value:
            return CableType.AUDIO
        for ct in CableType:
            if ct.value.lower() in value:
                return ct
        log.debug(f"Unknown cable type: {value}, defaulting to OTHER")
        return CableType.OTHER

    def _parse_adapters(self, rows: list[dict[Any, Any]]) -> list[Adapter]:
        adapters = []
        for row in rows:
            props = row["properties"]
            if not props["is_adapter"]["checkbox"]:
                continue

            adapter_type = self._get_plain_text(props, "Type")
            if not adapter_type or not adapter_type.strip():
                log.warning(
                    f"Skipping adapter with empty type in row {row.get('id', 'unknown')}"
                )
                continue

            length = props["Length (cm)"]["number"]
            if length is None or length < 0:
                log.warning(
                    f"Skipping adapter '{adapter_type}' with invalid length: {length}"
                )
                continue

            adapters.append(Adapter(type=adapter_type, length_cm=length))
        return adapters

    def _parse_prylar(self, rows: list[dict[Any, Any]]) -> list[Pryl]:
        prylar = []
        for row in rows:
            props = row["properties"]
            raw_title = self._get_plain_text(props, "Pryl")
            if not raw_title:
                raise ValueError("Missing title in pryl row")

            (number, title) = self._parse_pryl_string(raw_title)
            prylar.append(Pryl(number=number, title=title))
        return prylar

    @staticmethod
    def _parse_pryl_string(pryl: str) -> tuple[int, str]:
        match = re.match(r"#(\d+)\s+(.*)", pryl)
        if not match:
            raise ValueError(f"Invalid format: {pryl}")
        number = int(match.group(1))
        text = match.group(2).strip()
        return number, text

    def _parse_vinyls(self, rows: list[dict[Any, Any]]) -> list[Vinyl]:
        vinyls = []
        for row in rows:
            props = row["properties"]

            artist = self._get_plain_text(props, "Artist")
            if not artist or not artist.strip():
                log.warning(
                    f"Skipping vinyl with empty artist in row {row.get('id', 'unknown')}"
                )
                continue

            title = self._get_plain_text(props, "Titel")
            if not title or not title.strip():
                log.warning(
                    f"Skipping vinyl with empty title in row {row.get('id', 'unknown')}"
                )
                continue

            year_raw = self._get_plain_text(props, "År")
            try:
                year_str = int(year_raw) if year_raw else None
            except (ValueError, TypeError):
                log.warning(
                    f"Skipping vinyl '{artist} - {title}' with invalid year: {year_raw}"
                )
                continue

            cost = props.get("Kostnad (SEK)", {}).get("number")
            vinyls.append(Vinyl(artist=artist, title=title, year=year_str, cost=cost))
        return vinyls

    @staticmethod
    def _total_cable_length(cables: list[Cable]) -> float:
        total_cm = reduce(lambda acc, cable: acc + (cable.length_cm or 0), cables, 0)
        return round(total_cm / 100, 2)
