from collections.abc import Iterator

import requests
import zstandard as zstd

from packages.train.src.constants import CHUNK_SIZE, DEFAULT_MAX_FILES
from packages.train.src.dataset.models.raw_game import RawGame
from packages.train.src.dataset.repositories.files_metadata import (
    fetch_files_metadata_under_size,
    mark_file_as_processed,
)
from packages.train.src.dataset.repositories.raw_games import save_raw_game


def fetch_new_raw_games(
    max_files: int = DEFAULT_MAX_FILES, max_size_gb: float = 1
) -> Iterator[RawGame]:
    """
    Generator that yields new RawGame objects from Lichess PGN files one by one.
    Prefers smaller files first to avoid memory spikes.

    Each RawGame is saved to the database immediately, with processed=False.
    Duplicates (by PGN hash) are skipped.
    """
    candidate_files = fetch_files_metadata_under_size(max_gb=max_size_gb)

    # Filter out files already processed or already fully downloaded
    unprocessed_files = [f for f in candidate_files if not f.processed]

    # Sort by size (ascending) so smaller files are downloaded first
    unprocessed_files.sort(key=lambda f: f.size_gb)

    # Limit to max_files
    files_to_download = unprocessed_files[:max_files]

    for file_meta in files_to_download:
        print(
            f"Downloading and decompressing PGN file: {file_meta.filename} ({file_meta.size_gb} GB)..."
        )
        response = requests.get(file_meta.url, stream=True)
        if response.status_code != 200:
            print(f"ERROR: Failed to download {file_meta.filename} (status {response.status_code})")
            continue

        decompressor = zstd.ZstdDecompressor()
        with decompressor.stream_reader(response.raw) as reader:
            buffer = bytearray()
            while True:
                chunk = reader.read(CHUNK_SIZE)
                if not chunk:
                    break
                buffer.extend(chunk)

            decompressed_text = buffer.decode("utf-8")

        # Save all raw games to DB
        for pgn in _split_pgn_text_into_games(decompressed_text):
            raw_game = RawGame(file_id=file_meta.id, pgn=pgn, processed=False)
            save_raw_game(raw_game)
            yield raw_game

        mark_file_as_processed(file_meta)


def _split_pgn_text_into_games(pgn_text: str) -> Iterator[str]:
    """
    Split a PGN file into individual games.
    Each game starts with '[Event '.
    Yields games one by one.
    """
    raw_games = pgn_text.strip().split("\n\n[Event ")
    for i, raw in enumerate(raw_games):
        if i > 0:
            raw = "[Event " + raw
        yield raw.strip()
