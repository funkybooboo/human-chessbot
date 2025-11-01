"""PyTorch Dataset for game snapshots."""

import sqlite3
from pathlib import Path

import chess
import numpy as np
import torch
from torch.utils.data import Dataset

from packages.train.src.constants import DB_FILE
from packages.train.src.dataset.repositories.game_snapshots import count_snapshots


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

    def __init__(self, start_index: int, num_indexes: int, db_path: str | Path | None = None):
        # check if num indexes is possible with size of current dataset if not throw an error
        if count_snapshots() < start_index + num_indexes:
            raise ValueError(
                "num_indexes is larger than the size of the database\nIncrease the size of the database through the config file or decrease num_indexes"
            )
        self.start_index = start_index
        self.num_indexes = num_indexes

        self.db_path = str(db_path) if db_path else DB_FILE

    def _fen_to_tensor(self, fen: str) -> torch.Tensor:
        """Convert FEN string to tensor representation.

        Creates a 1d flattened tensor of a chess board where each tile represents
        a piece type/color:
        - Channels 0-5: White pieces (pawn, knight, bishop, rook, queen, king)
        - Channels 6-11: Black pieces (pawn, knight, bishop, rook, queen, king)

        Args:
            fen: FEN string representation of board

        Returns:
            Tensor of shape (8*8*12,)
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

        # flatten tensor
        tensor = tensor.reshape(8 * 8 * 12)

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
        """Normalize ELO ratings through z normalization based on values precomputed from all
        of the data from 2013

        Args:
            white_elo: White player's ELO
            black_elo: Black player's ELO

        Returns:
            Normalized tensor (2,) [white_elo, black_elo]
        """

        standard_deviation = 185.80054702756055
        mean = 1638.43153

        black_z_norm = (black_elo - mean) / standard_deviation
        white_z_norm = (white_elo - mean) / standard_deviation

        return torch.tensor([white_z_norm, black_z_norm], dtype=torch.float32)

    def _encode_move(self, fen: str, move_san: str) -> tuple[int, int]:
        """Encode move as indexes of start and end postions and promotion index.

        Args:
            fen: FEN string of the position before the move
            move_san: Move in SAN notation

        Returns:
            Tuple of (from_square, to_square, promotion) tensors
            - move: int index stores both start and end positions
            - promotion: int one-hot tensor for [none, N, B, R, Q]
        """
        try:
            board = chess.Board(fen)
            # Parse SAN move to get UCI move
            move = board.parse_san(move_san)

            # get the rows and columsn for the start and end positions
            start_col = move.from_square % 8
            start_row = move.from_square // 8

            end_col = move.to_square % 8
            end_row = move.to_square // 8

            # encode the values by using base 8 numering giving each id a digit place (stored in base 10)
            move_index = start_col
            move_index += 8 * start_row
            move_index += 8**2 * end_col
            move_index += 8**3 * end_row

            promotion_idx = self.PROMOTION_PIECES.get(move.promotion, 0)

            return move_index, promotion_idx

        except (ValueError, AssertionError):
            # If move parsing fails, return zeros
            return 0, 0

    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        return self.num_indexes

    def __getitem__(self, idx: int):
        """Get a single sample from the dataset.

        Args:
            idx: Index of sample to retrieve

        Returns:
            Dictionary containing encoded tensors ready for training
        """
        # to avoid the off by one error caused by the database starting at 1
        idx += self.start_index + 1

        # # retrieve index from the database slice
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT fen, move, white_elo, black_elo, result, turn FROM game_snapshots WHERE id=?"
            cur = conn.cursor()
            row = cur.execute(query, (idx,)).fetchone()
            if row is None:
                raise IndexError(f"No row at offset {self.start_index + idx}.")
            # convert query to dict
            data = {
                "fen": row[0],
                "move": row[1],
                "white_elo": row[2] if row[2] is not None else 0,
                "black_elo": row[3] if row[3] is not None else 0,
                "result": row[4],
                "turn": row[5],
            }

        # # convert to tensorwhite_elo

        # Encode all features

        # _encode_move
        chosen_move, promo = self._encode_move(data["fen"], data["move"])
        turn = self._encode_turn(data["turn"])

        # elos
        elos = self._normalize_elo(data["white_elo"], data["black_elo"])

        # board
        board = self._fen_to_tensor(data["fen"])

        # combine to 1d tensor and output
        labels = torch.cat((elos, turn, board), 0)

        return labels, (chosen_move, promo)


if __name__ == "__main__":
    # Example 1: Basic dataset
    print("\n1. Creating basic dataset...")
    dataset = GameSnapshotsDataset(start_index=0, num_indexes=100)
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
    dataset_filtered = GameSnapshotsDataset(start_index=0, num_indexes=50)
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
