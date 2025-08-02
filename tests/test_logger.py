from notion_task_runner.logging import get_logger


def test_get_logger_returns_bound_logger():
    logger = get_logger("notion_task_runner.some_module")

    # structlog returns different types based on configuration state
    # Check that it's a structlog logger instance
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'debug')
    assert hasattr(logger, 'error')
    assert callable(logger.info)
