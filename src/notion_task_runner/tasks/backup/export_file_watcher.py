import time
from pathlib import Path

from notion_task_runner.logging import get_logger

log = get_logger(__name__)


class ExportFileWatcher:
    """
    Utility class for monitoring a directory for the appearance of an exported file.

    This class provides a static method that repeatedly checks a given directory for a file matching a prefix,
    allowing for timed waiting logic during asynchronous export workflows.
    """

    @staticmethod
    def wait_for_file(
        directory: Path, prefix: str, timeout_seconds: int = 600, interval: int = 5
    ) -> Path:
        """
        Waits for a file with the given prefix to appear in the specified directory.
        Checks every `interval` seconds until `timeout` seconds have passed.

        :param directory: Path to the directory to watch.
        :param prefix: File prefix to match.
        :param timeout_seconds: Maximum time in seconds to wait.
        :param interval: Time in seconds between checks.
        :return: The matching Path object.
        :raises SystemExit: If no matching file is found before the timeout.
        """
        log.info("Waiting for file starting with '%s' in %s ...", prefix, directory)
        elapsed = 0

        while elapsed < timeout_seconds:
            matching_files = list(directory.glob(f"{prefix}*"))
            if matching_files:
                log.info("Found file: %s", matching_files[0])
                return matching_files[0]

            time.sleep(interval)
            elapsed += interval
            log.debug("Still waiting...")

        raise SystemExit(
            f"No file starting with '{prefix}' found in {directory} after {timeout_seconds} seconds."
        )
