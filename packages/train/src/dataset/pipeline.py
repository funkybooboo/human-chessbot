from packages.train.src.constants import DEFAULT_BATCH_SIZE, DEFAULT_MAX_SIZE_GB
from packages.train.src.dataset.fillers.fill_legal_moves import fill_database_with_legal_moves
from packages.train.src.dataset.fillers.fill_processed_snapshots import fill_processed_snapshots
from packages.train.src.dataset.fillers.fill_snapshots_and_statistics import (
    fill_database_with_snapshots,
)


def pipeline(
    num_indexes: int = DEFAULT_BATCH_SIZE, max_size_gb: float = DEFAULT_MAX_SIZE_GB
) -> None:
    """Fill all dataset tables in the correct order.

    Args:
        database_info: Dictionary containing database configuration including:
            - num_indexes: Target number of snapshots to process
            - max_size_gb: Maximum size in GB for downloaded files
    """
    print("Starting database population process...")

    # Fill snapshots and statistics (snapshots may be referenced by other tables)
    print("Filling game snapshots and statistics...")
    fill_database_with_snapshots(snapshots_threshold=num_indexes, max_size_gb=max_size_gb)

    # Then fill legal moves
    print("Filling legal moves...")
    fill_database_with_legal_moves()

    # Finally, process and fill processed_snapshots
    print("Filling processed snapshots...")
    fill_processed_snapshots(num_indexes)

    print("Database population complete.")
