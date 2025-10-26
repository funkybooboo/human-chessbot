"""PyTorch Dataset for game snapshots."""

import sqlite3
from pathlib import Path
from typing import Any

import chess
import numpy as np
import torch
from torch.utils.data import Dataset

from packages.train.src.constants import DB_FILE


class GameSnapshotsDataset(Dataset):
    """PyTorch Dataset for loading game snapshots from SQLite database.

    Loads board positions from FEN strings and converts them to tensor representations.
    Each sample includes the board state and associated metadata (ELO, result, move).

    Args:
        db_path: Path to SQLite database (defaults to DB_FILE from constants)
        elo_filter: Tuple of (min_elo, max_elo) to filter games. If None, includes all games.
        result_filter: List of results to include (e.g., ['1-0', '0-1']). If None, includes all.
        transform: Optional transform to apply to board tensors
        limit: Maximum number of samples to load. If None, loads all matching records.

    Returns:
        Dictionary with keys:
            - board: Tensor of shape (8, 8, 12) representing piece positions (one-hot encoded)
            - fen: Original FEN string
            - move: Move in UCI notation
            - white_elo: White player's ELO (or 0 if None)
            - black_elo: Black player's ELO (or 0 if None)
            - result: Game result (0=loss, 0.5=draw, 1=win for current player)
            - turn: 0 for white, 1 for black
    """

    # Piece type indices for one-hot encoding
    PIECE_TYPES = {
        chess.PAWN: 0,
        chess.KNIGHT: 1,
        chess.BISHOP: 2,
        chess.ROOK: 3,
        chess.QUEEN: 4,
        chess.KING: 5,
    }

    def __init__(
        self,
        db_path: str | Path | None = None,
        elo_filter: tuple[int, int] | None = None,
        result_filter: list[str] | None = None,
        transform: Any = None,
        limit: int | None = None,
    ):
        self.db_path = str(db_path) if db_path else DB_FILE
        self.transform = transform
        self.data = self._load_data(elo_filter, result_filter, limit)

    def _load_data(
        self,
        elo_filter: tuple[int, int] | None,
        result_filter: list[str] | None,
        limit: int | None,
    ) -> list[dict]:
        """Load data from database with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build query with filters
        query = """
            SELECT fen, move, white_elo, black_elo, result, turn
            FROM game_snapshots
            WHERE 1=1
        """
        params: list[int | str] = []

        if elo_filter:
            min_elo, max_elo = elo_filter
            query += """
                AND white_elo IS NOT NULL
                AND black_elo IS NOT NULL
                AND white_elo >= ?
                AND white_elo <= ?
                AND black_elo >= ?
                AND black_elo <= ?
            """
            params.extend([min_elo, max_elo, min_elo, max_elo])

        if result_filter:
            placeholders = ",".join("?" * len(result_filter))
            query += f" AND result IN ({placeholders})"
            params.extend(result_filter)

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Convert rows to dictionaries
        data = []
        for row in rows:
            data.append(
                {
                    "fen": row[0],
                    "move": row[1],
                    "white_elo": row[2] if row[2] is not None else 0,
                    "black_elo": row[3] if row[3] is not None else 0,
                    "result": row[4],
                    "turn": row[5],
                }
            )

        return data

    def _fen_to_tensor(self, fen: str) -> torch.Tensor:
        """Convert FEN string to tensor representation.

        Creates a 8x8x12 tensor where each channel represents a piece type/color:
        - Channels 0-5: White pieces (pawn, knight, bishop, rook, queen, king)
        - Channels 6-11: Black pieces (pawn, knight, bishop, rook, queen, king)

        Args:
            fen: FEN string representation of board

        Returns:
            Tensor of shape (8, 8, 12)
        """
        board = chess.Board(fen)
        tensor = np.zeros((8, 8, 12), dtype=np.float32)

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                rank = chess.square_rank(square)
                file = chess.square_file(square)

                # Get piece type index (0-5)
                piece_idx = self.PIECE_TYPES[piece.piece_type]

                # Add 6 for black pieces
                if not piece.color:  # Black
                    piece_idx += 6

                tensor[rank, file, piece_idx] = 1.0

        return torch.from_numpy(tensor)

    def _result_to_value(self, result: str, turn: str) -> float:
        """Convert game result to numerical value from current player's perspective.

        Args:
            result: Result string (e.g., '1-0', '0-1', '1/2-1/2')
            turn: 'w' for white or 'b' for black

        Returns:
            0.0 for loss, 0.5 for draw, 1.0 for win
        """
        if result == "1/2-1/2":
            return 0.5

        white_won = result == "1-0"

        if turn == "w":
            return 1.0 if white_won else 0.0
        else:
            return 0.0 if white_won else 1.0

    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        return len(self.data)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        """Get a single sample from the dataset.

        Args:
            idx: Index of sample to retrieve

        Returns:
            Dictionary containing board tensor and metadata
        """
        sample = self.data[idx]

        board = self._fen_to_tensor(sample["fen"])
        if self.transform:
            board = self.transform(board)

        return {
            "board": board,
            "fen": sample["fen"],
            "move": sample["move"],
            "white_elo": sample["white_elo"],
            "black_elo": sample["black_elo"],
            "result": self._result_to_value(sample["result"], sample["turn"]),
            "turn": 0 if sample["turn"] == "w" else 1,
        }


if __name__ == "__main__":
    # Example usage of GameSnapshotsDataset
    print("Creating GameSnapshotsDataset with all data...")
    dataset_all = GameSnapshotsDataset(limit=1000)
    print(f"Dataset size: {len(dataset_all)} positions")

    # Get a sample
    if len(dataset_all) > 0:
        sample = dataset_all[0]
        print("\nFirst sample:")
        print(f"  FEN: {sample['fen']}")
        print(f"  Move: {sample['move']}")
        print(f"  Board shape: {sample['board'].shape}")
        print(f"  White ELO: {sample['white_elo']}")
        print(f"  Black ELO: {sample['black_elo']}")
        print(f"  Result: {sample['result']} (0=loss, 0.5=draw, 1=win)")
        print(f"  Turn: {'White' if sample['turn'] == 0 else 'Black'}")

    # Example with ELO filter (high-rated games only)
    print("\n\nCreating filtered dataset (ELO 2000-2800)...")
    dataset_filtered = GameSnapshotsDataset(elo_filter=(2000, 2800), limit=500)
    print(f"Filtered dataset size: {len(dataset_filtered)} positions")

    if len(dataset_filtered) > 0:
        sample = dataset_filtered[0]
        print("Sample from filtered dataset:")
        print(f"  White ELO: {sample['white_elo']}")
        print(f"  Black ELO: {sample['black_elo']}")

    # Example with result filter (decisive games only)
    print("\n\nCreating dataset with decisive games only...")
    dataset_decisive = GameSnapshotsDataset(result_filter=["1-0", "0-1"], limit=500)
    print(f"Decisive games dataset size: {len(dataset_decisive)} positions")

    # Use with DataLoader
    if len(dataset_all) > 0:
        from torch.utils.data import DataLoader

        print("\n\nCreating DataLoader...")
        dataloader = DataLoader(dataset_all, batch_size=16, shuffle=True)

        # Get one batch
        batch = next(iter(dataloader))
        print("\nFirst batch:")
        print(f"  Batch size: {len(batch['move'])}")
        print(f"  Board tensors shape: {batch['board'].shape}")
        print(f"  White ELOs: {batch['white_elo']}")
        print(f"  Black ELOs: {batch['black_elo']}")
        print(f"  Results: {batch['result']}")
        print(f"  Sample moves: {batch['move'][:5]}")
    else:
        print("\nDataset is empty. Cannot create DataLoader.")
        print("Run the dataset generation pipeline first to populate the database.")
