from packages.train.src.constants import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_SIZE_GB,
    DEFAULT_PRINT_INTERVAL,
    DEFAULT_SNAPSHOTS_THRESHOLD,
)
from packages.train.src.dataset.processers.game_snapshots import SnapshotBatchProcessor
from packages.train.src.dataset.repositories.database import initialize_database
from packages.train.src.dataset.repositories.files_metadata import (
    ensure_metadata_exists,
    fetch_file_metadata_by_filename,
    mark_file_as_processed,
)
from packages.train.src.dataset.repositories.raw_games import fetch_unprocessed_raw_games
from packages.train.src.dataset.requesters.raw_games import (
    fetch_new_raw_games,
    fetch_raw_games_from_file,
)


def fill_database_with_snapshots(
    snapshots_threshold: int = DEFAULT_SNAPSHOTS_THRESHOLD,
    max_size_gb: float = DEFAULT_MAX_SIZE_GB,
    print_interval: int = DEFAULT_PRINT_INTERVAL,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> None:
    """Download and process Lichess files until reaching snapshot threshold.

    Downloads files under max_size_gb, processes games, and saves snapshots and statistics.
    Stops when snapshots_threshold is reached or no more files are available.

    Note: This automatically populates both game_snapshots and game_statistics tables.
    """
    initialize_database()
    ensure_metadata_exists()

    processor = SnapshotBatchProcessor(batch_size=batch_size, print_interval=print_interval)

    while True:
        if processor.get_snapshot_count() >= snapshots_threshold:
            print(f"Reached {processor.get_snapshot_count()} snapshots. Done.")
            break

        games_processed = processor.process_games(
            games=fetch_unprocessed_raw_games(),
            should_stop=lambda: processor.get_snapshot_count() >= snapshots_threshold,
        )

        if games_processed == 0:
            print("No unprocessed games left. Fetching a new file...")
            new_games_batch = list(fetch_new_raw_games(max_files=1, max_size_gb=max_size_gb))

            if not new_games_batch:
                print("WARNING: No new files or games available. Stopping.")
                break

            print(f"New {len(new_games_batch)} raw games saved. Continuing processing...")

    print(f"Completed. Total snapshots: {processor.get_snapshot_count()}")


def fill_database_with_snapshots_from_lichess_filename(
    filename: str,
    print_interval: int = DEFAULT_PRINT_INTERVAL,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> None:
    """Download and process a specific Lichess file by filename.

    Note: This automatically populates both game_snapshots and game_statistics tables.
    """
    initialize_database()
    ensure_metadata_exists()

    file_meta = fetch_file_metadata_by_filename(filename)
    if file_meta is None:
        print(f"ERROR: File '{filename}' not found in metadata.")
        print("Make sure the file metadata has been fetched from Lichess.")
        return

    print(f"Found file: {file_meta.filename} ({file_meta.size_gb} GB, {file_meta.games} games)")

    if not file_meta.processed:
        games_downloaded = 0
        for _ in fetch_raw_games_from_file(file_meta):
            games_downloaded += 1
        print(f"Downloaded and saved {games_downloaded} raw games from {file_meta.filename}.")
    else:
        print(f"File already downloaded: {file_meta.filename}")

    print(f"Processing games from {file_meta.filename}...")
    processor = SnapshotBatchProcessor(batch_size=batch_size, print_interval=print_interval)
    games_processed = processor.process_games(
        games=fetch_unprocessed_raw_games(file_id=file_meta.id),
    )
    print(f"Processed {games_processed} games from {file_meta.filename}.")

    if not file_meta.processed:
        mark_file_as_processed(file_meta)
        print(f"Marked {file_meta.filename} as processed.")

    print(f"Completed. Total snapshots in database: {processor.get_snapshot_count()}")


if __name__ == "__main__":
    fill_database_with_snapshots(
        snapshots_threshold=10_000,
        max_size_gb=10,
        print_interval=1_000,
        batch_size=1_000,
    )
