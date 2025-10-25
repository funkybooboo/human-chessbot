from packages.train.src.dataset.constants import (
    DEFAULT_MAX_SIZE_GB,
    DEFAULT_PRINT_INTERVAL,
    DEFAULT_SNAPSHOTS_THRESHOLD,
)
from packages.train.src.dataset.logger import get_logger
from packages.train.src.dataset.processers.game_snapshots import raw_game_to_snapshots
from packages.train.src.dataset.repositories.database import initialize_database
from packages.train.src.dataset.repositories.files_metadata import (
    files_metadata_exist,
    save_files_metadata,
)
from packages.train.src.dataset.repositories.game_snapshots import count_snapshots, save_snapshot
from packages.train.src.dataset.repositories.raw_games import (
    fetch_unprocessed_raw_games,
    mark_raw_game_as_processed,
    save_raw_game,
)
from packages.train.src.dataset.requesters.file_metadata import fetch_files_metadata
from packages.train.src.dataset.requesters.raw_games import fetch_new_raw_games

logger = get_logger("fill_snapshots")


def fill_database_with_snapshots(
    snapshots_threshold: int = DEFAULT_SNAPSHOTS_THRESHOLD,
    max_size_gb: float = DEFAULT_MAX_SIZE_GB,
    print_interval: int = DEFAULT_PRINT_INTERVAL,
) -> None:
    """
    Fill the database with game snapshots until reaching `snapshots_threshold`.
    Always finish a full game and file before checking thresholds.
    """
    initialize_database()

    # --- Ensure file metadata exists ---
    if not files_metadata_exist():
        logger.info("Fetching file metadata from Lichess...")
        save_files_metadata(fetch_files_metadata())
        logger.info("Metadata saved.")
    else:
        logger.info("File metadata already exists.")

    while True:
        # Stop if we've reached the target
        snapshot_count = count_snapshots()
        if snapshot_count >= snapshots_threshold:
            logger.info(f"Reached {snapshot_count} snapshots. Done.")
            break

        # --- Process all unprocessed games ---
        processed_any = False
        for game in fetch_unprocessed_raw_games():
            processed_any = True

            for snapshot in raw_game_to_snapshots(game):
                save_snapshot(snapshot)

                snapshot_count = count_snapshots()
                if snapshot_count % print_interval == 0:
                    logger.info(f"{snapshot_count} snapshots saved...")

            mark_raw_game_as_processed(game)

            snapshot_count = count_snapshots()
            if snapshot_count >= snapshots_threshold:
                logger.info(f"Reached {snapshot_count} snapshots. Done.")
                break

        # --- If no unprocessed games, fetch a new file ---
        if not processed_any:
            logger.info("No unprocessed games left. Fetching a new file...")

            fetched_any = False
            for game in fetch_new_raw_games(max_files=1, max_size_gb=max_size_gb):
                if game is not None:
                    save_raw_game(game)
                    fetched_any = True

            if not fetched_any:
                logger.warning("No new files or games available. Stopping.")
                break

            # After fetching, next loop iteration will process them
            logger.info("New raw games saved. Continuing processing...")

    logger.info(f"Completed. Total snapshots: {snapshot_count}")


if __name__ == "__main__":
    fill_database_with_snapshots(
        snapshots_threshold=10_000,
        max_size_gb=10,
        print_interval=1_000,
    )
