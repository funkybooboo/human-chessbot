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
    Uses fixed encoding: ELO normalized to [0, 1] range, scalar results, move encoding included.

    Args:
        db_path: Path to SQLite database (defaults to DB_FILE from constants)
        elo_filter: Tuple of (min_elo, max_elo) to filter games. If None, includes all games.
        result_filter: List of results to include (e.g., ['1-0', '0-1']). If None, includes all.
        limit: Maximum number of samples to load. If None, loads all matching records.

    Returns:
        Dictionary with keys:
            - board: (8, 8, 12) tensor - piece positions one-hot encoded
            - turn: (2,) tensor - one-hot encoded [white, black]
            - elo: (2,) tensor - normalized [white_elo / 3000, black_elo / 3000]
            - result: (1,) tensor - game outcome (0.0=loss, 0.5=draw, 1.0=win)
            - move_from: (64,) tensor - one-hot encoded source square
            - move_to: (64,) tensor - one-hot encoded target square
            - promotion: (5,) tensor - one-hot encoded promotion piece
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

    # Promotion piece encoding (None, N, B, R, Q)
    PROMOTION_PIECES = {
        None: 0,
        chess.KNIGHT: 1,
        chess.BISHOP: 2,
        chess.ROOK: 3,
        chess.QUEEN: 4,
    }

    def __init__(
        self,
        db_path: str | Path | None = None,
        elo_filter: tuple[int, int] | None = None,
        result_filter: list[str] | None = None,
        limit: int | None = None,
    ):
        self.db_path = str(db_path) if db_path else DB_FILE
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

    def _encode_result(self, result: str, turn: str) -> torch.Tensor:
        """Encode result as scalar value from current player's perspective.

        Args:
            result: Result string (e.g., '1-0', '0-1', '1/2-1/2')
            turn: 'w' for white or 'b' for black

        Returns:
            Scalar tensor (1,) - 0.0 for loss, 0.5 for draw, 1.0 for win
        """
        if result == "1/2-1/2":
            value = 0.5
        else:
            white_won = result == "1-0"
            value = (1.0 if white_won else 0.0) if turn == "w" else 0.0 if white_won else 1.0

        return torch.tensor([value], dtype=torch.float32)

    def _encode_turn(self, turn: str) -> torch.Tensor:
        """Encode turn as one-hot vector.

        Args:
            turn: 'w' for white or 'b' for black

        Returns:
            One-hot tensor (2,) for [white, black]
        """
        onehot = torch.zeros(2, dtype=torch.float32)
        if turn == "w":
            onehot[0] = 1.0
        else:
            onehot[1] = 1.0
        return onehot

    def _normalize_elo(self, white_elo: int, black_elo: int) -> torch.Tensor:
        """Normalize ELO ratings by dividing by 3000.

        Args:
            white_elo: White player's ELO
            black_elo: Black player's ELO

        Returns:
            Normalized tensor (2,) for [white_elo / 3000, black_elo / 3000]
        """
        return torch.tensor([white_elo / 3000.0, black_elo / 3000.0], dtype=torch.float32)

    def _encode_move(
        self, fen: str, move_san: str
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Encode move as one-hot vectors for source, target, and promotion.

        Args:
            fen: FEN string of the position before the move
            move_san: Move in SAN notation

        Returns:
            Tuple of (from_square, to_square, promotion) tensors
            - from_square: (64,) one-hot tensor
            - to_square: (64,) one-hot tensor
            - promotion: (5,) one-hot tensor for [none, N, B, R, Q]
        """
        try:
            board = chess.Board(fen)
            # Parse SAN move to get UCI move
            move = board.parse_san(move_san)

            # Encode from square (0-63)
            from_square = torch.zeros(64, dtype=torch.float32)
            from_square[move.from_square] = 1.0

            # Encode to square (0-63)
            to_square = torch.zeros(64, dtype=torch.float32)
            to_square[move.to_square] = 1.0

            # Encode promotion piece
            promotion = torch.zeros(5, dtype=torch.float32)
            promotion_idx = self.PROMOTION_PIECES.get(move.promotion, 0)
            promotion[promotion_idx] = 1.0

            return from_square, to_square, promotion

        except (ValueError, AssertionError):
            # If move parsing fails, return zeros
            from_square = torch.zeros(64, dtype=torch.float32)
            to_square = torch.zeros(64, dtype=torch.float32)
            promotion = torch.zeros(5, dtype=torch.float32)
            promotion[0] = 1.0  # No promotion
            return from_square, to_square, promotion

    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        return len(self.data)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        """Get a single sample from the dataset.

        Args:
            idx: Index of sample to retrieve

        Returns:
            Dictionary containing encoded tensors ready for training
        """
        sample = self.data[idx]

        # Encode all features
        from_sq, to_sq, promo = self._encode_move(sample["fen"], sample["move"])

        return {
            "board": self._fen_to_tensor(sample["fen"]),
            "turn": self._encode_turn(sample["turn"]),
            "elo": self._normalize_elo(sample["white_elo"], sample["black_elo"]),
            "result": self._encode_result(sample["result"], sample["turn"]),
            "move_from": from_sq,
            "move_to": to_sq,
            "promotion": promo,
        }


if __name__ == "__main__":
    # Example 1: Basic dataset
    print("\n1. Creating basic dataset...")
    dataset = GameSnapshotsDataset(limit=100)
    print(f"   Dataset size: {len(dataset)} positions")

    if len(dataset) > 0:
        sample = dataset[0]
        print("\n   Sample output structure:")
        print(f"   - board: {sample['board'].shape} - One-hot encoded pieces")
        print(
            f"   - turn: {sample['turn'].shape} - One-hot [white, black] = {sample['turn'].numpy()}"
        )
        print(
            f"   - elo: {sample['elo'].shape} - Normalized [white/3000, black/3000] = {sample['elo'].numpy()}"
        )
        print(
            f"   - result: {sample['result'].shape} - Scalar value = {sample['result'].item():.2f}"
        )
        print(f"   - move_from: {sample['move_from'].shape} - One-hot source square")
        print(f"   - move_to: {sample['move_to'].shape} - One-hot target square")
        print(f"   - promotion: {sample['promotion'].shape} - One-hot promotion piece")

    # Example 2: Filtered dataset (high-rated games only)
    print("\n2. Creating filtered dataset (ELO 1000-2000)...")
    dataset_filtered = GameSnapshotsDataset(elo_filter=(1000, 2000), limit=50)
    print(f"   Filtered dataset size: {len(dataset_filtered)} positions")

    # Example 3: Use with PyTorch DataLoader
    if len(dataset) > 0:
        from torch.utils.data import DataLoader

        print("\n3. Creating PyTorch DataLoader for training...")
        dataloader = DataLoader(dataset, batch_size=4, shuffle=True, num_workers=0)

        # Get one batch
        batch = next(iter(dataloader))
        print("   Batch shapes:")
        print(f"   - board: {batch['board'].shape}")
        print(f"   - turn: {batch['turn'].shape}")
        print(f"   - elo: {batch['elo'].shape}")
        print(f"   - result: {batch['result'].shape}")
        print(f"   - move_from: {batch['move_from'].shape}")
        print(f"   - move_to: {batch['move_to'].shape}")
        print(f"   - promotion: {batch['promotion'].shape}")

        print("\n   All tensors are ready for training!")
        print("   Example: loss = criterion(model(batch['board']), batch['result'])")
