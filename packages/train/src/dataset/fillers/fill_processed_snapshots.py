"""Filler script to populate the processed_snapshots table with encoded data."""

from packages.train.src.constants import DEFAULT_BATCH_SIZE, DEFAULT_PRINT_INTERVAL
from packages.train.src.dataset.processers.processed_snapshots import ProcessedSnapshotsProcessor
from packages.train.src.dataset.repositories.database import initialize_database
from packages.train.src.dataset.repositories.processed_snapshots import (
    get_raw_snapshots_batch,
    get_total_snapshots,
    save_processed_snapshots,
)


def fill_processed_snapshots(
    batch_size: int = DEFAULT_BATCH_SIZE,
    print_interval: int = DEFAULT_PRINT_INTERVAL,
):
    """Process all raw game snapshots and populate the processed_snapshots table.

    Args:
        batch_size: Number of snapshots to process per batch
        print_interval: Interval for progress printing
    """
    initialize_database()
    processor = ProcessedSnapshotsProcessor()

    print("Starting to fill processed_snapshots table...")

    # Get total count for progress
    total_snapshots = get_total_snapshots()

    print(f"Total snapshots to process: {total_snapshots}")

    processed_count = 0
    last_print = 0

    # Process in batches
    offset = 0
    while offset < total_snapshots:
        rows = get_raw_snapshots_batch(offset, batch_size)

        if not rows:
            break

        to_save = []
        for row in rows:
            snapshot_id = row[0]
            data = {
                "fen": row[1],
                "move": row[2],
                "turn": row[3],
                "white_elo": row[4] if row[4] is not None else 0,
                "black_elo": row[5] if row[5] is not None else 0,
                "result": row[6],
            }

            try:
                board, metadata, chosen_move, valid_moves = processor.process_snapshot_row(data)
                to_save.append(
                    (
                        snapshot_id,
                        board.numpy().tobytes(),
                        metadata.numpy().tobytes(),
                        chosen_move,
                        valid_moves.numpy().tobytes(),
                    )
                )
            except Exception as e:
                print(f"Warning: Failed to process snapshot {snapshot_id}: {e}")
                continue

        # Save batch
        save_processed_snapshots(to_save)

        processed_count += len(to_save)
        offset += batch_size

        # Progress print
        if processed_count // print_interval > last_print // print_interval:
            print(f"{processed_count} snapshots processed...")
            last_print = processed_count

    print(f"Completed. Processed {processed_count} snapshots.")


if __name__ == "__main__":
    fill_processed_snapshots()
