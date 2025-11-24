"""Processor for encoding game snapshots into tensors."""

import chess
import numpy as np
import torch

from packages.train.src.dataset.loaders.legal_moves import LegalMovesDataset


class ProcessedSnapshotsProcessor:
    """Processes raw game snapshot data into encoded tensors for storage."""

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

    def __init__(self):
        self.legal_moves = LegalMovesDataset()

    @staticmethod
    def fen_to_tensor(fen: str) -> torch.Tensor:
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
        tensor = np.zeros((12, 8, 8), dtype=np.float32)

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                rank = chess.square_rank(square)
                file = chess.square_file(square)

                # Get piece type index (0-5)
                piece_idx = ProcessedSnapshotsProcessor.PIECE_TYPES[piece.piece_type]

                # Add 6 for black pieces
                if not piece.color:  # Black
                    piece_idx += 6

                tensor[piece_idx, rank, file] = 1.0

        return torch.from_numpy(tensor)

    @staticmethod
    def encode_result(result: str, turn: str) -> torch.Tensor:
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

    @staticmethod
    def encode_turn(turn: str) -> torch.Tensor:
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

    @staticmethod
    def normalize_elo(white_elo: int, black_elo: int) -> torch.Tensor:
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

    def _encode_move(self, fen: str, move_san: str) -> int:
        """Encode move as indexes of start and end positions and promotion index.

        Args:
            fen: FEN string of the position before the move
            move_san: Move in SAN notation

        Returns:
            - move: int index of move in legal_moves dataset
        """
        try:
            board = chess.Board(fen)

            # Parse SAN move to get UCI move to determine promotion
            move = board.parse_san(move_san)
            move_index = self.legal_moves.get_index_from_move(board.uci(move))

            if move_index == -1:
                return 0
            return move_index

        except (ValueError, AssertionError):
            # If move parsing fails, return zeros
            return 0

    def _encode_valid_moves(self, fen: str) -> torch.Tensor:
        """Encode all legal moves for a given position."""
        board = chess.Board(fen)

        valid_moves = list(board.legal_moves)

        moves_tensor = torch.zeros(len(self.legal_moves), dtype=torch.float32)

        for move in valid_moves:
            idx = self.legal_moves.get_index_from_move(board.uci(move))
            if idx >= 0:
                moves_tensor[idx] = 1.0

        return moves_tensor

    def process_snapshot_row(
        self, data: dict
    ) -> tuple[torch.Tensor, torch.Tensor, int, torch.Tensor]:
        """Encode a single row of data into tensors.

        Args:
            data: Dict with keys: fen, move, turn, white_elo, black_elo, result

        Returns:
            Tuple of (board, metadata, chosen_move, valid_moves)
        """
        chosen_move = self._encode_move(data["fen"], data["move"])
        valid_moves = self._encode_valid_moves(data["fen"])
        turn = self.encode_turn(data["turn"])
        elos = self.normalize_elo(data["white_elo"], data["black_elo"])
        board = self.fen_to_tensor(data["fen"])
        metadata = torch.cat((elos, turn), 0)

        return board, metadata, chosen_move, valid_moves
