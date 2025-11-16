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
    
    Automatically JOINs game_snapshots with game_statistics to retrieve ELO ratings and results.

    Args:
        start_index: Starting index for dataset slice
        num_indexes: Number of indexes to include in dataset
        db_path: Path to SQLite database (defaults to DB_FILE from constants)

    Returns:
        Tuple of (labels, (move_index, promotion_index)) where:
            - labels: Combined tensor with [white_elo, black_elo, turn_white, turn_black, board_state]
            - move_index: Integer encoding of move (start_col + 8*start_row + 64*end_col + 512*end_row)
            - promotion_index: Integer encoding of promotion piece (0=none, 1=N, 2=B, 3=R, 4=Q)
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
        tensor = tensor.reshape(8 * 8 * 12)  # type: ignore[assignment]

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

            # get the rows and columns for the start and end positions
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

        # retrieve index from the database slice with JOIN to game_statistics
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT 
                    gs.fen, 
                    gs.move, 
                    gs.turn,
                    gst.white_elo, 
                    gst.black_elo, 
                    gst.result
                FROM game_snapshots gs
                JOIN game_statistics gst ON gs.raw_game_id = gst.raw_game_id
                WHERE gs.id=?
            """
            cur = conn.cursor()
            row = cur.execute(query, (idx,)).fetchone()
            if row is None:
                raise IndexError(f"No row at offset {self.start_index + idx}.")
            # convert query to dict
            data = {
                "fen": row[0],
                "move": row[1],
                "turn": row[2],
                "white_elo": row[3] if row[3] is not None else 0,
                "black_elo": row[4] if row[4] is not None else 0,
                "result": row[5],
            }

        # Encode all features

        # _encode_move
        chosen_move, promo = self._encode_move(data["fen"], data["move"])
        turn = self._encode_turn(data["turn"])

        # elos
        elos = self._normalize_elo(data["white_elo"], data["black_elo"])

        # board
        board = self._fen_to_tensor(data["fen"])

        # combine to 1d tensor
        labels = torch.cat((elos, turn, board), 0)

        return labels, (chosen_move, promo)
