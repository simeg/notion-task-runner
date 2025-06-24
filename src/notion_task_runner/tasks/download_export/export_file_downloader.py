from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_fixed

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient

log = get_logger(__name__)


class ExportFileDownloader:
    """
    Handles downloading and verifying Notion export files.

    This class uses the NotionClient to download a file from a given URL and save it to a specified path.
    It includes basic verification to ensure the file was successfully downloaded and exists on disk.
    """

    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_WAIT_SECONDS = 2

    def __init__(
        self,
        client: NotionClient,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_wait_seconds: int = DEFAULT_RETRY_WAIT_SECONDS,
    ) -> None:
        self.client = client
        self.max_retries = max_retries
        self.retry_wait_seconds = retry_wait_seconds

    def download_and_verify(self, url: str, path: Path) -> Path | None:
        log.info(f"Downloading file to: {path}")
        downloaded = self._download_file(url, path)

        if not downloaded or not downloaded.is_file():
            log.info("Could not download file")
            return None

        return downloaded

    def _download_file(self, url: str, download_path: Path) -> Path | None:
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_fixed(self.retry_wait_seconds),
        )
        def _do_download() -> Path:
            response = self.client.get(url, stream=True)

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return download_path

        try:
            return _do_download()
        except Exception as e:
            log.warning("Download failed after retries: %s", e)
            return None
