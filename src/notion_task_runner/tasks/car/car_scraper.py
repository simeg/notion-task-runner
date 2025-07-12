from pathlib import Path
from typing import Any, ClassVar

from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_fixed

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient
from notion_task_runner.tasks.car.car_model import Car
from notion_task_runner.tasks.task_config import TaskConfig

log = get_logger(__name__)


class CarScraper:
    """
    Scrapes car information from biluppgifter.se based on a registration number.

    This class supports both production mode (fetching live HTML via HTTP)
    and development mode (reading static HTML files from the sample_html/ directory).
    It extracts and maps structured car information using DOM selectors.

    Attributes:
        BASE_URL: The base URL for live scraping.
        DEFAULT_UNKNOWN_INT/STR: Fallback values for missing or invalid data.
        FIELD_SELECTORS: DOM selectors and parsers for various car attributes.
    """

    BASE_URL = "https://biluppgifter.se/fordon"
    DEFAULT_UNKNOWN_INT = -1
    DEFAULT_UNKNOWN_STR = "Unknown"
    RETRY_WAIT_SECONDS_DEFAULT = 5
    RETRY_ATTEMPTS_DEFAULT = 3
    IDENTITY = staticmethod(lambda x: x)

    FIELD_SELECTORS: ClassVar[dict[Any, Any]] = {
        "color": (
            "#technical-data div.inner ul:nth-child(5) li:nth-child(1) span.value",
            str,
        ),
        "mileage_km": (
            "#vehicle-data > div.inner > ul:nth-child(3) > li:nth-child(8) > span.value",
            lambda s: (
                int("".join(c for c in s if c.isdigit()))
                if any(c.isdigit() for c in s)
                else CarScraper.DEFAULT_UNKNOWN_INT
            ),
        ),
        "horsepower": (
            "#summary > div.inner > ul > li:nth-child(7) > div > em",
            lambda s: (
                int("".join(c for c in s if c.isdigit()))
                if any(c.isdigit() for c in s)
                else CarScraper.DEFAULT_UNKNOWN_INT
            ),
        ),
    }

    def __init__(
        self,
        client: NotionClient,
        config: TaskConfig,
        retry_attempts: int = RETRY_ATTEMPTS_DEFAULT,
        retry_wait_seconds: int = RETRY_WAIT_SECONDS_DEFAULT,
    ):
        self.config = config
        self.client = client
        self.retry_attempts = retry_attempts
        self.retry_wait_seconds = retry_wait_seconds

    def scrape(self, reg_number: str) -> Car:
        """
        Scrapes and parses car data for a given registration number.

        In production mode, it fetches HTML from biluppgifter.se using an HTTP GET.
        In development mode, it reads the HTML from a local file under sample_html/.

        Args:
            reg_number: The car's registration number (case-insensitive).

        Returns:
            A populated Car object with parsed fields such as model, color, mileage, etc.

        Raises:
            ValueError: If the expected HTML structure is missing or malformed.
        """
        normalized_reg_number = self._normalize_reg_number(reg_number)
        if not self.config.is_prod:
            log.info("Running in development mode, using local HTML file")
            raw_html = self._load_local_html(reg_number)
            return self._parse_html(raw_html, normalized_reg_number)

        url = f"{self.BASE_URL}/{reg_number.lower()}"
        raw_html = self._get_with_retry(url)

        return self._parse_html(raw_html, normalized_reg_number)

    def _load_local_html(self, reg_number: str) -> str:
        html_path = Path(f"sample_html/{reg_number.lower()}.html")
        return html_path.read_text(encoding="utf-8")

    def _get_with_retry(self, url: str) -> str:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        @retry(
            stop=stop_after_attempt(self.retry_attempts),
            wait=wait_fixed(self.retry_wait_seconds),
            reraise=True,
        )
        def _inner() -> str:
            response = self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.text

        return _inner()

    @staticmethod
    def _extract_labeled_data(soup: BeautifulSoup) -> dict[str, str]:
        data = {}
        items = soup.select("#vehicle-data div.inner li")
        for item in items:
            label_elem = item.select_one("span.label")
            value_elem = item.select_one("span.value")
            if label_elem and value_elem:
                label = label_elem.get_text(strip=True).lower().replace(":", "")
                value = value_elem.get_text(strip=True)
                data[label] = value
        return data

    def _extract_mapped_value(
        self,
        car_data: dict[str, str],
        key: str,
        mapper: Any = None,
        default: Any = None,
    ) -> Any:
        value = car_data.get(key)
        if value is None:
            return default
        if mapper is None or mapper is self.IDENTITY or mapper is str:
            return value
        try:
            return mapper(value)
        except Exception as e:
            log.warning(f"Failed to map value for key '{key}': {e}")
            return default

    def _normalize_reg_number(self, reg_number: str) -> str:
        return reg_number.upper()

    def _parse_html(self, html: str, reg_number: str) -> Car:
        soup = BeautifulSoup(html, "html.parser")

        vehicle_data_div = soup.select_one("#vehicle-data div.inner")
        if not vehicle_data_div:
            log.error("⚠️ Could not find #vehicle-data .inner in HTML")
            raise ValueError(
                f"Invalid HTML structure for registration number: {reg_number}"
            )

        car_data = self._extract_labeled_data(soup)

        # Extract fields using FIELD_SELECTORS
        extracted_fields = {}
        for field, (selector, extractor) in self.FIELD_SELECTORS.items():
            elem = soup.select_one(selector)
            if elem:
                try:
                    extracted_fields[field] = extractor(elem.get_text(strip=True))
                except Exception as e:
                    log.warning(f"Failed to extract field '{field}': {e}")
                    extracted_fields[field] = (
                        self.DEFAULT_UNKNOWN_STR
                        if extractor is str
                        else self.DEFAULT_UNKNOWN_INT
                    )
            else:
                extracted_fields[field] = (
                    self.DEFAULT_UNKNOWN_STR
                    if extractor is str
                    else self.DEFAULT_UNKNOWN_INT
                )

        model_year = self._extract_mapped_value(
            car_data,
            "fordonsår / modellår",
            lambda s: int(s.split("/")[0].strip()),
            self.DEFAULT_UNKNOWN_INT,
        )

        tax_yearly_sek = self._extract_mapped_value(
            car_data,
            "årlig skatt",
            lambda s: int(s.split()[0].replace(" ", "")),
            self.DEFAULT_UNKNOWN_INT,
        )

        return Car(
            reg_number=reg_number,
            model=self._extract_mapped_value(
                car_data, "modell", self.IDENTITY, self.DEFAULT_UNKNOWN_STR
            ),
            model_year=model_year,
            color=extracted_fields.get("color", self.DEFAULT_UNKNOWN_STR),
            inspected_at=self._extract_mapped_value(
                car_data, "senast besiktigad", self.IDENTITY, self.DEFAULT_UNKNOWN_STR
            ),
            next_inspection_latest_at=self._extract_mapped_value(
                car_data,
                "nästa besiktning senast",
                self.IDENTITY,
                self.DEFAULT_UNKNOWN_STR,
            ),
            tax_yearly_sek=tax_yearly_sek,
            registered_at=self._extract_mapped_value(
                car_data, "först registrerad", self.IDENTITY, self.DEFAULT_UNKNOWN_STR
            ),
            mileage_km=extracted_fields.get("mileage_km", self.DEFAULT_UNKNOWN_INT),
            horsepower=extracted_fields.get("horsepower", self.DEFAULT_UNKNOWN_INT),
        )
