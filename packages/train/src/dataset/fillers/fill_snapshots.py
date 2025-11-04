from packages.train.src.constants import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_SIZE_GB,
    DEFAULT_PRINT_INTERVAL,
    DEFAULT_SNAPSHOTS_THRESHOLD,
)
from packages.train.src.dataset.processers.game_snapshots import raw_game_to_snapshots
from packages.train.src.dataset.repositories.database import initialize_database
from packages.train.src.dataset.repositories.files_metadata import (
    files_metadata_exist,
    save_files_metadata,
)
from packages.train.src.dataset.repositories.game_snapshots import (
    count_snapshots,
    save_snapshots_batch,
)
from packages.train.src.dataset.repositories.raw_games import (
    fetch_unprocessed_raw_games,
    mark_raw_game_as_processed,
    save_raw_games_batch,
)
from packages.train.src.dataset.requesters.file_metadata import fetch_files_metadata
from packages.train.src.dataset.requesters.raw_games import fetch_new_raw_games


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

    snapshot_batch = []
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
