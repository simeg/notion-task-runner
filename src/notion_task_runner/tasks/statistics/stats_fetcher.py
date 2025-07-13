import concurrent.futures
import re
from dataclasses import dataclass
from enum import Enum
from functools import reduce
from typing import Any

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionDatabase

log = get_logger(__name__)


@dataclass(frozen=True)
class Watch:
    name: str
    cost: int
    purchased_date: str


class CableType(Enum):
    HDMI = "HDMI"
    USB_A = "USB-A"
    USB_C = "USB-C"
    AUDIO = "Audio"
    ETHERNET = "Ethernet"
    DISPLAY_PORT = "DisplayPort"
    OTHER = "Other"


@dataclass(frozen=True)
class Cable:
    type: CableType
    length_cm: int


@dataclass(frozen=True)
class Adapter:
    type: str
    length_cm: int


@dataclass(frozen=True)
class Pryl:
    title: str
    number: int


@dataclass(frozen=True)
class Vinyl:
    artist: str
    title: str
    release_year: int


@dataclass(frozen=True)
class WorkspaceStats:
    watches: list[Watch]
    cables: list[Cable]
    adapters: list[Adapter]
    prylar: list[Pryl]
    vinyls: list[Vinyl]
    total_cable_length_m: float = 0.0


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

    def fetch(self) -> WorkspaceStats:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_watches = executor.submit(self.db.fetch_rows, self.WATCHES_DB_ID)
            future_cables = executor.submit(self.db.fetch_rows, self.CABLES_DB_ID)
            future_prylar = executor.submit(self.db.fetch_rows, self.PRYLAR_DB_ID)
            future_vinyls = executor.submit(self.db.fetch_rows, self.VINYLS_DB_ID)

            watches = self._parse_watches(future_watches.result())
            rows_cables = future_cables.result()
            cables = self._parse_cables(rows_cables)
            adapters = self._parse_adapters(rows_cables)
            prylar = self._parse_prylar(future_prylar.result())
            vinyls = self._parse_vinyls(future_vinyls.result())

        total_cable_length_m = self._total_cable_length(cables)

        return WorkspaceStats(
            watches=watches,
            cables=cables,
            adapters=adapters,
            prylar=prylar,
            vinyls=vinyls,
            total_cable_length_m=total_cable_length_m,
        )

    def _parse_watches(self, rows: list[dict[Any, Any]]) -> list[Watch]:
        watches = []
        for row in rows:
            props = row["properties"]
            name = self._get_plain_text(props, "Name")
            cost = props["Cost (SEK)"]["number"]
            purchased_date = props["Aquired at"]["date"]["start"]
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
                log.warning("Missing type title in row, defaulting to OTHER")
                cable_type = CableType.OTHER
            else:
                cable_type = self._parse_cable_type(raw_type)

            length = props["Length (cm)"]["number"]
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
        log.warning(f"Unknown cable type: {value}, defaulting to OTHER")
        return CableType.OTHER

    def _parse_adapters(self, rows: list[dict[Any, Any]]) -> list[Adapter]:
        adapters = []
        for row in rows:
            props = row["properties"]
            if not props["is_adapter"]["checkbox"]:
                continue
            type = self._get_plain_text(props, "Type")
            length = props["Length (cm)"]["number"]
            adapters.append(Adapter(type=type, length_cm=length))
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
            title = self._get_plain_text(props, "Title")
            year_str = int(self._get_plain_text(props, "Year"))

            vinyls.append(Vinyl(artist=artist, title=title, release_year=year_str))
        return vinyls

    @staticmethod
    def _total_cable_length(cables: list[Cable]) -> float:
        total_cm = reduce(lambda acc, cable: acc + (cable.length_cm or 0), cables, 0)
        return round(total_cm / 100, 2)
