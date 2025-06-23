import logging
from notion_task_runner.logger import get_logger


def test_get_logger_returns_logger_with_correct_name():
    logger = get_logger("notion_task_runner.some_module")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "some_module"
    assert logger.level == logging.INFO or logger.level == 0  # 0 = NOTSET if inherited