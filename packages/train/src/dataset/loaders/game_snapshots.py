"""PyTorch Dataset for game snapshots."""

from pathlib import Path

from torch.utils.data import Dataset

from packages.train.src.constants import DB_FILE
from packages.train.src.dataset.repositories.database import initialize_database
from packages.train.src.dataset.repositories.processed_snapshots import (
    count_processed_snapshots,
    get_processed_snapshots_batch,
)


class GameSnapshotsDataset(Dataset):
    """PyTorch Dataset for loading pre-processed game snapshots from SQLite database.

    Loads pre-encoded board positions, metadata, chosen moves, and valid moves from the processed_snapshots table.
    Assumes the table is fully populated by the filler script.

    Args:
        start_index: Starting index for dataset slice
        num_indexes: Number of indexes to include in dataset
        db_path: Path to SQLite database (defaults to DB_FILE from constants)

    Returns:
        Tuple of ((board, metadata), (chosen_move, valid_moves)) where:
            - board: Tensor of shape (12, 8, 8) - one-hot encoded pieces
            - metadata: Tensor of shape (4,) - [white_elo_norm, black_elo_norm, turn_white, turn_black]
            - chosen_move: Integer index of the chosen move in legal_moves
            - valid_moves: Tensor of shape (num_legal_moves,) - binary mask of legal moves
    """

    def __init__(self, start_index: int, num_indexes: int, db_path: str | Path | None = None):
        # check if num indexes is possible with size of current dataset if not throw an error
        if count_processed_snapshots() < start_index + num_indexes:
            raise ValueError(
                "num_indexes is larger than the size of the database\nIncrease the size of the database through the config file or decrease num_indexes"
            )
        self.start_index = start_index
        self.num_indexes = num_indexes

        self.db_path = str(db_path) if db_path else DB_FILE

        initialize_database()

    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        return self.num_indexes

    def __getitem__(self, idx: int):
        """Get a single sample from the dataset.

        Args:
            idx: Index of sample to retrieve

        Returns:
            Tuple of ((board, metadata), chosen_move)
        """
        return self.__getitems__([idx])[0]

    def __getitems__(self, idxs: list[int]):
        """Get multiple samples from the dataset by reading pre-processed data.

        Assumes processed_snapshots table is fully populated by the filler.
        """
        # Convert dataset indices to game_snapshots.id values (1-indexed)
        db_idxs = [idx + self.start_index + 1 for idx in idxs]

        # Query processed_snapshots for all requested IDs in one go
        cached = get_processed_snapshots_batch(db_idxs)

        # Build results in original order
        results = []
        for db_idx in db_idxs:
            if db_idx not in cached:
                raise IndexError(
                    f"No processed data for snapshot ID {db_idx}. Run the filler first."
                )

            snapshot = cached[db_idx]
            results.append(
                ((snapshot.board, snapshot.metadata), (snapshot.chosen_move, snapshot.valid_moves))
            )

        return results
