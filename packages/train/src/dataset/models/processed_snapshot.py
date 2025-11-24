from dataclasses import dataclass

import numpy as np
import torch


@dataclass
class ProcessedSnapshot:
    """Model for a processed game snapshot with deserialized tensors."""

    snapshot_id: int
    board: torch.Tensor  # Shape: (12, 8, 8)
    metadata: torch.Tensor  # Shape: (4,) - [white_elo_norm, black_elo_norm, turn_white, turn_black]
    chosen_move: int
    valid_moves: torch.Tensor  # Shape: (num_legal_moves,)

    @classmethod
    def from_bytes(
        cls,
        snapshot_id: int,
        board_bytes: bytes,
        metadata_bytes: bytes,
        chosen_move: int,
        valid_moves_bytes: bytes,
    ) -> "ProcessedSnapshot":
        """Create a ProcessedSnapshot from stored bytes."""
        board = torch.from_numpy(
            np.frombuffer(board_bytes, dtype=np.float32).reshape(12, 8, 8).copy()
        )
        metadata = torch.from_numpy(np.frombuffer(metadata_bytes, dtype=np.float32).copy())
        valid_moves = torch.from_numpy(np.frombuffer(valid_moves_bytes, dtype=np.float32).copy())

        return cls(
            snapshot_id=snapshot_id,
            board=board,
            metadata=metadata,
            chosen_move=chosen_move,
            valid_moves=valid_moves,
        )
