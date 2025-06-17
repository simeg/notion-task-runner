from notion_task_runner.tasks.pas_page_task import PASPageTask


def test_pas_page_task_happy_path(caplog, mock_notion_client_200, mock_db_w_props, mock_calculator_30):
    sut = PASPageTask(
        client=mock_notion_client_200,
        db=mock_db_w_props,
        calculator=mock_calculator_30,
        block_id="dummy-page-id"
    )

    with caplog.at_level("INFO"):
        sut.run()

    mock_db_w_props.get_entries.assert_called_once()

    mock_db_w_props.get_entries.assert_called_once()
    mock_calculator_30.calculate.assert_called_once()
    mock_notion_client_200.patch.assert_called_once()

    args, kwargs = mock_notion_client_200.patch.call_args
    assert "https://api.notion.com/v1/blocks/dummy-page-id" in args
    assert kwargs["json"]["callout"]["rich_text"][1]["text"]["content"] == "30kr"
    assert "✅ Updated Prylar Att Sälja page!" in caplog.text

def test_pas_page_task_with_empty_database(mock_notion_client_200, calculator, mock_db_empty_list):
    sut = PASPageTask(
        client=mock_notion_client_200,
        db=mock_db_empty_list,
        calculator=calculator,
        block_id="dummy-page-id"
    )

    sut.run()

    mock_db_empty_list.get_entries.assert_called_once()
    calculator.calculate.assert_called_once_with([])
    mock_notion_client_200.patch.assert_called_once()

    args, kwargs = mock_notion_client_200.patch.call_args
    assert "https://api.notion.com/v1/blocks/dummy-page-id" in args
    assert kwargs["json"]["callout"]["rich_text"][1]["text"]["content"] == "0kr"

def test_pas_page_task_handles_client_error(caplog, mock_notion_client_400, mock_db_w_props, mock_calculator_30):
    sut = PASPageTask(
        client=mock_notion_client_400,
        db=mock_db_w_props,
        calculator=mock_calculator_30,
        block_id="test-page"
    )

    with caplog.at_level("INFO"):
        sut.run()

    mock_db_w_props.get_entries.assert_called_once()
    mock_calculator_30.calculate.assert_called_once_with([{'properties': {'Slutpris': {'number': 10}}}, {'properties': {'Slutpris': {'number': 20}}}])
    mock_notion_client_400.patch.assert_called_once()

    assert "❌ Failed to update Prylar Att Sälja." in caplog.text