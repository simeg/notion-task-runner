from pathlib import Path

from notion_task_runner.logger import get_logger
from notion_task_runner.notion import NotionClient

log = get_logger(__name__)


class ExportFileDownloader:
    """
    Handles downloading and verifying Notion export files.

    This class uses the NotionClient to download a file from a given URL and save it to a specified path.
    It includes basic verification to ensure the file was successfully downloaded and exists on disk.
    """

    def __init__(self, client: NotionClient) -> None:
        self.client = client

    def download_and_verify(self, url: str, path: Path) -> Path | None:
        log.info(f"Downloading file to: {path}")
        downloaded = self._download_file(url, path)

        if not downloaded or not downloaded.is_file():
            log.info("Could not download file")
            return None

        return downloaded

    def _download_file(self, url: str, download_path: Path) -> Path | None:
        try:
            response = self.client.get(url, stream=True)

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return download_path
        except Exception as e:
            log.warning("Exception during file download", exc_info=e)
            return None
