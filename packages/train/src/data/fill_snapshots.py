from packages.train.src.data.database.database import initialize_database
from packages.train.src.data.database.files_metadata import (
    files_metadata_exist,
    save_files_metadata,
)
from packages.train.src.data.database.game_snapshots import count_snapshots, save_snapshot
from packages.train.src.data.database.raw_games import (
    fetch_unprocessed_raw_games,
    mark_raw_game_as_processed,
    save_raw_game,
)
from packages.train.src.data.processers.game_snapshots import raw_game_to_snapshots
from packages.train.src.data.requesters.file_metadata import fetch_files_metadata
from packages.train.src.data.requesters.raw_games import fetch_new_raw_games


def fill_database_with_snapshots(
    snapshots_threshold: int = 10_000,
    max_size_gb: float = 10,
    print_interval: int = 1_000,
) -> None:
    """
    Fill the database with game snapshots until reaching `snapshots_threshold`.
    Always finish a full game and file before checking thresholds.
    """
    initialize_database()

    # --- Ensure file metadata exists ---
    if not files_metadata_exist():
        print("Fetching file metadata from Lichess...")
        save_files_metadata(fetch_files_metadata())
        print("Metadata saved.\n")
    else:
        print("File metadata already exists.\n")

    while True:
        # Stop if we've reached the target
        snapshot_count = count_snapshots()
        if snapshot_count >= snapshots_threshold:
            print(f"Reached {snapshot_count} snapshots. Done.")
            break

        # --- Process all unprocessed games ---
        processed_any = False
        for game in fetch_unprocessed_raw_games():
            processed_any = True

            for snapshot in raw_game_to_snapshots(game):
                save_snapshot(snapshot)

                snapshot_count = count_snapshots()
                if snapshot_count % print_interval == 0:
                    print(f"{snapshot_count} snapshots saved...")

            mark_raw_game_as_processed(game)

            snapshot_count = count_snapshots()
            if snapshot_count >= snapshots_threshold:
                print(f"Reached {snapshot_count} snapshots. Done.")
                break

        # --- If no unprocessed games, fetch a new file ---
        if not processed_any:
            print("No unprocessed games left. Fetching a new file...")

            fetched_any = False
            for game in fetch_new_raw_games(max_files=1, max_size_gb=max_size_gb):
                if game is not None:
                    save_raw_game(game)
                    fetched_any = True

            if not fetched_any:
                print("No new files or games available. Stopping.")
                break

            # After fetching, next loop iteration will process them
            print("New raw games saved. Continuing processing...")

    print(f"Completed. Total snapshots: {snapshot_count}")


if __name__ == "__main__":
    fill_database_with_snapshots(
        snapshots_threshold=10_000,
        max_size_gb=10,
        print_interval=1_000,
    )
