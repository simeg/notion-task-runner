import time
from pathlib import Path
import pytest
from unittest.mock import patch

from notion_task_runner.tasks.backup.export_file_watcher import \
  ExportFileWatcher



def test_wait_for_file_finds_file_immediately(tmp_path: Path):
    file = tmp_path / "notion-export-test.zip"
    file.write_text("dummy content")

    result = ExportFileWatcher.wait_for_file(
        directory=tmp_path,
        prefix="notion-export",
        timeout=10,
        interval=1,
    )

    assert result == file


def test_wait_for_file_finds_file_after_delay(tmp_path: Path):
    target_file = tmp_path / "notion-export-delayed.zip"

    # Keep reference to the real time.sleep
    original_sleep = time.sleep

    def delayed_file_creation():
        # Wait, then create the file
        original_sleep(1)
        target_file.write_text("delayed content")

    with patch("time.sleep", side_effect=lambda x: delayed_file_creation() if x == 1 else original_sleep(x)):
        result = ExportFileWatcher.wait_for_file(
            directory=tmp_path,
            prefix="notion-export",
            timeout=5,
            interval=1,
        )

    assert result.exists()
    assert result.name.startswith("notion-export")

def test_wait_for_file_times_out(tmp_path: Path):
    with pytest.raises(SystemExit) as excinfo:
        ExportFileWatcher.wait_for_file(
            directory=tmp_path,
            prefix="nonexistent",
            timeout=2,
            interval=1,
        )

    assert "No file starting with 'nonexistent'" in str(excinfo.value)