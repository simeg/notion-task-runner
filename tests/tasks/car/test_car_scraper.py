import pytest
from unittest.mock import MagicMock
from pathlib import Path
from notion_task_runner.tasks.car.car_scraper import CarScraper
from notion_task_runner.tasks.task_config import TaskConfig
from notion_task_runner.notion import NotionClient

@pytest.mark.only
class TestCarScraper:
    @pytest.fixture
    def html_fixture(self):
        fixture_path = Path("tests/fixtures/html/car_scraper_fixture.html")
        return fixture_path.read_text(encoding="utf-8")

    @pytest.fixture
    def mock_config(self):
        mock_config = MagicMock(spec=TaskConfig)
        mock_config.is_prod = True
        return mock_config

    def test_parse_html_returns_correct_car(self, html_fixture, mock_config):
        scraper = CarScraper(MagicMock(spec=NotionClient), mock_config)
        car = scraper._parse_html(html_fixture, "ABC123")

        assert car.reg_number == "ABC123"
        assert car.model.lower() == "volvo v90"
        assert car.model_year == 2020
        assert car.color.lower() == "blå"
        assert car.inspected_at == "2024-03-15"
        assert car.next_inspection_latest_at == "2025-03-15"
        assert car.tax_yearly_sek == 5500
        assert car.registered_at == "2020-06-10"
        assert car.mileage_km == 12345
        assert car.horsepower == 250

    def test_parse_html_raise_when_cannot_parse(self, mock_config):
        scraper = CarScraper(MagicMock(spec=NotionClient), mock_config)

        with pytest.raises(ValueError, match="Invalid HTML structure for registration number: ABC123"):
            scraper._parse_html("", "ABC123")

    def test_scrape_in_production_mode(self, html_fixture, mock_config):
        mock_client = MagicMock(spec=NotionClient)
        mock_response = MagicMock()
        mock_response.text = html_fixture
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response

        scraper = CarScraper(mock_client, mock_config)
        scraper.retry_attempts = 1
        scraper.retry_wait_seconds = 0

        car = scraper.scrape("abc123")

        assert car.model.lower() == "volvo v90"

    def test_scrape_retry_failure_raises(self, mock_config):
        mock_client = MagicMock(spec=NotionClient)
        mock_client.get.side_effect = Exception("Simulated failure")

        scraper = CarScraper(mock_client, mock_config)
        scraper.retry_attempts = 2
        scraper.retry_wait_seconds = 0

        with pytest.raises(Exception, match="Simulated failure"):
            scraper.scrape("abc123")

    def test_retry_attempts_limit(monkeypatch, mock_config):
        attempt_counter = {"count": 0}

        def failing_get(*args, **kwargs):
            attempt_counter["count"] += 1
            raise Exception("Simulated failure")

        mock_client = MagicMock(spec=NotionClient)
        mock_client.get.side_effect = failing_get

        retry_attempts = 3
        scraper = CarScraper(mock_client, mock_config, retry_attempts=retry_attempts, retry_wait_seconds=0)

        with pytest.raises(Exception, match="Simulated failure"):
            scraper.scrape("abc123")

        assert attempt_counter["count"] == retry_attempts


    def test_retry_succeeds_before_limit(monkeypatch, html_fixture, mock_config):
        attempt_counter = {"count": 0}

        def flaky_get(*args, **kwargs):
            if attempt_counter["count"] < 2:
                attempt_counter["count"] += 1
                raise Exception("Temporary error")
            mock_response = MagicMock()
            mock_response.text = html_fixture
            mock_response.raise_for_status.return_value = None
            return mock_response

        mock_client = MagicMock(spec=NotionClient)
        mock_client.get.side_effect = flaky_get

        scraper = CarScraper(mock_client, mock_config, retry_attempts=5, retry_wait_seconds=0)
        car = scraper.scrape("abc123")

        assert attempt_counter["count"] == 2
        assert car.model.lower() == "volvo v90"