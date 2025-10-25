import re
from collections.abc import Iterator
from urllib.parse import urljoin

import requests

from packages.train.src.data.models.file_metadata import FileMetadata

_BASE_URL = "https://database.lichess.org/standard/"
_COUNTS_URL = urljoin(_BASE_URL, "counts.txt")


def fetch_files_metadata() -> Iterator[FileMetadata]:
    """
    Fetch metadata about all standard Lichess files.

    Yields:
        FileMetadata: Metadata for each .pgn.zst file.
    """
    # --- Fetch counts.txt to get game counts ---
    counts_resp = requests.get(_COUNTS_URL)
    counts_resp.raise_for_status()

    counts: dict[str, int] = {}
    for line in counts_resp.text.strip().splitlines():
        parts = line.split()
        if len(parts) == 2:
            filename, games = parts
            counts[filename] = int(games.replace(",", ""))

    # --- Fetch standard directory page ---
    resp = requests.get(_BASE_URL)
    resp.raise_for_status()
    html = resp.text

    # --- Extract .pgn.zst files ---
    file_names = re.findall(r'href="(lichess_db_standard_rated_[^"]+\.pgn\.zst)"', html)

    for filename in file_names:
        file_url = urljoin(_BASE_URL, filename)

        # Get file size from HEAD request
        head_resp = requests.head(file_url)
        size_gb = int(head_resp.headers.get("Content-Length", 0)) / (1024**3)

        yield FileMetadata(
            url=file_url,
            filename=filename,
            games=counts.get(filename, 0),
            size_gb=round(size_gb, 2),
        )


if __name__ == "__main__":
    files_metadata_iter = fetch_files_metadata()
    files_preview = list(next(files_metadata_iter) for _ in range(10))  # preview first 10

    print("Found at least 10 standard files.\n")
    for file in files_preview:
        print(file)
