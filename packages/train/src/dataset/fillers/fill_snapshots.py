from collections.abc import Iterator
from urllib.parse import urljoin

import requests
import zstandard as zstd

from packages.train.src.constants import (
    CHUNK_SIZE,
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_SIZE_GB,
    DEFAULT_PRINT_INTERVAL,
    DEFAULT_SNAPSHOTS_THRESHOLD,
    LICHESS_BASE_URL,
)
from packages.train.src.dataset.models.file_metadata import FileMetadata
from packages.train.src.dataset.models.game_snapshot import GameSnapshot
from packages.train.src.dataset.models.raw_game import RawGame
from packages.train.src.dataset.processers.game_snapshots import raw_game_to_snapshots
from packages.train.src.dataset.repositories.database import initialize_database
from packages.train.src.dataset.repositories.files_metadata import (
    fetch_all_files_metadata,
    files_metadata_exist,
    mark_file_as_processed,
    save_file_metadata,
    save_files_metadata,
)
from packages.train.src.dataset.repositories.game_snapshots import (
    count_snapshots,
    save_snapshots_batch,
)
from packages.train.src.dataset.repositories.raw_games import (
    fetch_unprocessed_raw_games,
    mark_raw_game_as_processed,
    save_raw_game,
    save_raw_games_batch,
)
from packages.train.src.dataset.requesters.file_metadata import fetch_files_metadata
from packages.train.src.dataset.requesters.raw_games import fetch_new_raw_games


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


def download_and_process_lichess_file(
    filename: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
    print_interval: int = DEFAULT_PRINT_INTERVAL,
) -> int:
    """
    Download and process a specific lichess file into the database.

    Args:
        filename: Name of the lichess file (e.g., "lichess_db_standard_rated_2024-01.pgn.zst")
        batch_size: Number of snapshots to batch before writing to DB
        print_interval: Print progress every N snapshots

    Returns:
        Number of snapshots created from this file, or 0 if file was already processed

    Process:
        1. Initialize database if needed
        2. Check if file already exists in database
        3. If already processed, return 0 (noop)
        4. If exists but not processed, process existing raw games
        5. If doesn't exist, download and process the file
    """
    initialize_database()

    # Construct the full URL for the file
    file_url = urljoin(LICHESS_BASE_URL, filename)

    # Check if this file already exists in the database
    existing_file = None
    for file_meta in fetch_all_files_metadata():
        if file_meta.url == file_url or file_meta.filename == filename:
            existing_file = file_meta
            break

    # If file already processed, noop
    if existing_file and existing_file.processed:
        print(f"File '{filename}' already processed. Skipping.")
        return 0

    # If file exists but not processed, we'll process the raw games that are already downloaded
    if existing_file and not existing_file.processed:
        print(f"File '{filename}' found in database but not processed. Processing existing raw games...")
        return _process_file_snapshots(
            existing_file, batch_size=batch_size, print_interval=print_interval
        )

    # File doesn't exist - download it
    print(f"Downloading file: {filename}...")

    # Get file metadata from lichess
    response = requests.head(file_url)
    if response.status_code != 200:
        raise ValueError(f"File '{filename}' not found at {file_url} (status {response.status_code})")

    size_gb = int(response.headers.get("Content-Length", 0)) / (1024**3)

    # Try to get game count from counts.txt
    counts_url = urljoin(LICHESS_BASE_URL, "counts.txt")
    counts_resp = requests.get(counts_url)
    game_count = 0
    if counts_resp.status_code == 200:
        for line in counts_resp.text.strip().splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[0] == filename:
                game_count = int(parts[1].replace(",", ""))
                break

    # Create and save file metadata
    file_meta = FileMetadata(
        url=file_url,
        filename=filename,
        games=game_count,
        size_gb=round(size_gb, 2),
        processed=False,
    )
    save_file_metadata(file_meta)
    print(f"File metadata saved: {file_meta.filename} ({file_meta.size_gb} GB, ~{file_meta.games} games)")

    # Download and decompress the file
    print(f"Downloading and decompressing {filename}...")
    response = requests.get(file_url, stream=True)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to download {filename} (status {response.status_code})")

    decompressor = zstd.ZstdDecompressor()
    with decompressor.stream_reader(response.raw) as reader:
        buffer = bytearray()
        while True:
            chunk = reader.read(CHUNK_SIZE)
            if not chunk:
                break
            buffer.extend(chunk)

        decompressed_text = buffer.decode("utf-8")

    print(f"Download complete. Saving raw games to database...")

    # Save all raw games to DB
    raw_games_count = 0
    for pgn in _split_pgn_text_into_games(decompressed_text):
        raw_game = RawGame(file_id=file_meta.id, pgn=pgn, processed=False)
        save_raw_game(raw_game)
        raw_games_count += 1

    print(f"Saved {raw_games_count} raw games. Processing into snapshots...")

    # Process the raw games into snapshots
    snapshots_created = _process_file_snapshots(
        file_meta, batch_size=batch_size, print_interval=print_interval
    )

    # Mark file as processed
    mark_file_as_processed(file_meta)
    print(f"File '{filename}' fully processed. Created {snapshots_created} snapshots.")

    return snapshots_created


def _process_file_snapshots(
    file_meta: FileMetadata,
    batch_size: int = DEFAULT_BATCH_SIZE,
    print_interval: int = DEFAULT_PRINT_INTERVAL,
) -> int:
    """
    Process all unprocessed raw games from a specific file into snapshots.

    Args:
        file_meta: The file metadata object
        batch_size: Number of snapshots to batch before writing
        print_interval: Print progress every N snapshots

    Returns:
        Number of snapshots created
    """
    snapshot_batch: list[GameSnapshot] = []
    snapshots_created = 0
    last_print_count = 0

    for game in fetch_unprocessed_raw_games(file_id=file_meta.id):
        # Collect snapshots from the game
        for snapshot in raw_game_to_snapshots(game):
            snapshot_batch.append(snapshot)

            # Flush batch if it reaches the batch size
            if len(snapshot_batch) >= batch_size:
                save_snapshots_batch(snapshot_batch)
                snapshots_created += len(snapshot_batch)
                snapshot_batch = []

                # Print progress
                if snapshots_created // print_interval > last_print_count // print_interval:
                    print(f"{snapshots_created} snapshots created from {file_meta.filename}...")
                    last_print_count = snapshots_created

        # Mark game as processed
        mark_raw_game_as_processed(game)

    # Flush remaining snapshots
    if snapshot_batch:
        save_snapshots_batch(snapshot_batch)
        snapshots_created += len(snapshot_batch)

    return snapshots_created


def fill_database_with_snapshots(
    snapshots_threshold: int = DEFAULT_SNAPSHOTS_THRESHOLD,
    max_size_gb: float = DEFAULT_MAX_SIZE_GB,
    print_interval: int = DEFAULT_PRINT_INTERVAL,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> None:
    """
    Fill the database with game snapshots until reaching `snapshots_threshold`.
    Always finish a full game and file before checking thresholds.
    Uses batch writing for improved performance.
    """
    initialize_database()

    # --- Ensure file metadata exists ---
    if not files_metadata_exist():
        print("Fetching file metadata from Lichess...")
        save_files_metadata(fetch_files_metadata())
        print("Metadata saved.")
    else:
        print("File metadata already exists.")

    snapshot_batch: list[GameSnapshot] = []
    snapshot_count = count_snapshots()
    last_print_count = snapshot_count

    def flush_batch():
        """Helper function to flush the current batch to the database."""
        nonlocal snapshot_batch, snapshot_count, last_print_count
        if snapshot_batch:
            save_snapshots_batch(snapshot_batch)
            snapshot_count = count_snapshots()
            snapshot_batch = []

            # Print progress if we've crossed print_interval thresholds
            if snapshot_count // print_interval > last_print_count // print_interval:
                print(f"{snapshot_count} snapshots saved...")
                last_print_count = snapshot_count

    while True:
        # Stop if we've reached the target
        if snapshot_count >= snapshots_threshold:
            flush_batch()  # Ensure any remaining snapshots are saved
            print(f"Reached {snapshot_count} snapshots. Done.")
            break

        # --- Process all unprocessed games ---
        processed_any = False
        for game in fetch_unprocessed_raw_games():
            processed_any = True

            # Collect snapshots from the game
            for snapshot in raw_game_to_snapshots(game):
                snapshot_batch.append(snapshot)

                # Flush batch if it reaches the batch size
                if len(snapshot_batch) >= batch_size:
                    flush_batch()

            # Flush after each game to ensure game completion
            flush_batch()

            mark_raw_game_as_processed(game)

            if snapshot_count >= snapshots_threshold:
                print(f"Reached {snapshot_count} snapshots. Done.")
                break

        # --- If no unprocessed games, fetch a new file ---
        if not processed_any:
            print("No unprocessed games left. Fetching a new file...")

            # Collect new games in a batch
            new_games_batch = []
            for game in fetch_new_raw_games(max_files=1, max_size_gb=max_size_gb):
                if game is not None:
                    new_games_batch.append(game)

            if not new_games_batch:
                flush_batch()  # Ensure any remaining snapshots are saved
                print("WARNING: No new files or games available. Stopping.")
                break

            # Save all new games in a single batch
            save_raw_games_batch(new_games_batch)

            # After fetching, next loop iteration will process them
            print(f"New {len(new_games_batch)} raw games saved. Continuing processing...")

    print(f"Completed. Total snapshots: {snapshot_count}")


if __name__ == "__main__":
    fill_database_with_snapshots(
        snapshots_threshold=10_000,
        max_size_gb=10,
        print_interval=1_000,
        batch_size=1_000,
    )
