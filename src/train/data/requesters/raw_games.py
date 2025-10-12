import requests
import zstandard as zstd
from src.train.data.database.files_metadata import fetch_files_metadata_under_size
from src.train.data.database.games import fetch_file_ids_in_db
from src.train.data.models.game import RawGame
from typing import Iterator


def fetch_new_games(max_files: int = 5, max_size_gb: float = 1) -> Iterator[RawGame]:
    """
    Generator that yields new games from Lichess PGN files one by one.
    This avoids loading all games into memory at once.
    """
    candidate_files = fetch_files_metadata_under_size(max_gb=max_size_gb)
    existing_file_ids = fetch_file_ids_in_db()
    files_to_download = [f for f in candidate_files if f.id not in existing_file_ids][:max_files]

    for file_meta in files_to_download:
        print(f"Downloading and decompressing PGN file: {file_meta.filename}...")
        response = requests.get(file_meta.url, stream=True)
        if response.status_code != 200:
            print(f"Failed to download {file_meta.filename} (status {response.status_code})")
            continue

        decompressor = zstd.ZstdDecompressor()
        with decompressor.stream_reader(response.raw) as reader:
            buffer = b""
            while True:
                chunk = reader.read(16384)  # read in 16 KB chunks
                if not chunk:
                    break
                buffer += chunk

            decompressed_text = buffer.decode("utf-8")

        for pgn in _split_pgn_text_into_games(decompressed_text):
            yield RawGame(file_id=file_meta.id, pgn=pgn)


def _split_pgn_text_into_games(pgn_text: str) -> Iterator[str]:
    """
    Split a single PGN file into individual games.
    Each game starts with '[Event '.
    Yields games one by one.
    """
    raw_games = pgn_text.strip().split("\n\n[Event ")
    for i, raw in enumerate(raw_games):
        if i > 0:
            raw = "[Event " + raw
        yield raw.strip()
