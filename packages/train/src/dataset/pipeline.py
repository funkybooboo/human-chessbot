from packages.train.src.dataset.fillers.fill_legal_moves import fill_database_with_legal_moves
from packages.train.src.dataset.fillers.fill_processed_snapshots import fill_processed_snapshots
from packages.train.src.dataset.fillers.fill_snapshots_and_statistics import (
    fill_database_with_snapshots,
)


def pipeline():
    """Fill all dataset tables in the correct order."""
    print("Starting database population process...")

    # Fill snapshots and statistics (snapshots may be referenced by other tables)
    print("Filling game snapshots and statistics...")
    fill_database_with_snapshots()

    # Then fill legal moves
    print("Filling legal moves...")
    fill_database_with_legal_moves()

    # Finally, process and fill processed_snapshots
    print("Filling processed snapshots...")
    fill_processed_snapshots()

    print("Database population complete.")
