from unittest.mock import MagicMock

import pytest

from notion_task_runner.utils import fail


def test_fail_logs_error_and_exits():
    logger = MagicMock()

    with pytest.raises(SystemExit) as exc_info:
        fail(logger, "Something went wrong")

    logger.error.assert_called_once_with("Something went wrong")
    assert exc_info.type is SystemExit
    assert exc_info.value.code == 1
