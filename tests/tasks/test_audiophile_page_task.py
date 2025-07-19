import pytest
from unittest.mock import MagicMock

from notion_task_runner.tasks.audiophile.audiophile_page_task import AudiophilePageTask
from notion_task_runner.tasks.pas.sum_calculator import SumCalculator


@pytest.fixture
def mock_db_costs():
    db = MagicMock()
    db.fetch_rows.return_value = [
        {"properties": {"Kostnad": {"number": 10}}},
        {"properties": {"Kostnad": {"number": 20}}},
    ]
    return db


@pytest.fixture
def mock_db_empty_costs():
    db = MagicMock()
    db.fetch_rows.return_value = []
    return db


def test_audiophile_page_task_happy_path(
    caplog,
    mock_notion_client_200,
    mock_db_costs,
    mock_config,
    mock_calculator_30,
):
    sut = AudiophilePageTask(
        client=mock_notion_client_200,
        db=mock_db_costs,
        config=mock_config,
        calculator=mock_calculator_30,
        block_id="dummy-block",
    )

    with caplog.at_level("INFO"):
        sut.run()

    mock_db_costs.fetch_rows.assert_called_once_with(sut.DATABASE_ID)
    mock_calculator_30.calculate_total_for_column.assert_called_once_with(
        mock_db_costs.fetch_rows.return_value, "Kostnad"
    )
    mock_notion_client_200.patch.assert_called_once()

    args, kwargs = mock_notion_client_200.patch.call_args
    assert args[0] == "https://api.notion.com/v1/blocks/dummy-block"
    assert (
        kwargs["json"]["callout"]["rich_text"][1]["text"]["content"] == "30kr"
    )
    assert "✅ Updated Audiophile page!" in caplog.text


def test_audiophile_page_task_with_empty_database(
    mock_notion_client_200,
    mock_config,
    calculator,
    mock_db_empty_costs,
):
    sut = AudiophilePageTask(
        client=mock_notion_client_200,
        db=mock_db_empty_costs,
        config=mock_config,
        calculator=calculator,
        block_id="dummy-block",
    )

    sut.run()

    mock_db_empty_costs.fetch_rows.assert_called_once_with(sut.DATABASE_ID)
    calculator.calculate_total_for_column.assert_called_once_with([], "Kostnad")
    mock_notion_client_200.patch.assert_called_once()

    args, kwargs = mock_notion_client_200.patch.call_args
    assert kwargs["json"]["callout"]["rich_text"][1]["text"]["content"] == "0kr"


def test_audiophile_page_task_handles_client_error(
    caplog,
    mock_notion_client_400,
    mock_db_costs,
    mock_config,
    mock_calculator_30,
):
    sut = AudiophilePageTask(
        client=mock_notion_client_400,
        db=mock_db_costs,
        config=mock_config,
        calculator=mock_calculator_30,
        block_id="dummy-block",
    )

    with caplog.at_level("INFO"):
        sut.run()

    mock_notion_client_400.patch.assert_called_once()
    assert "❌ Failed to update Audiophile." in caplog.text
