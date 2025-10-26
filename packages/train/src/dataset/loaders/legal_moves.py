"""PyTorch Dataset for legal chess moves."""

import sqlite3
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import Dataset

from packages.train.src.constants import DB_FILE


class LegalMovesDataset(Dataset):
    """PyTorch Dataset for legal chess moves.

    Loads legal moves and their associated piece types from the database.
    Each sample represents a unique legal move with its piece type encoding.

    Args:
        db_path: Path to SQLite database (defaults to DB_FILE from constants)
        transform: Optional transform to apply to move encodings
        vocab: Optional move vocabulary for encoding. If None, builds from data.

    Returns:
        Dictionary with keys:
            - move: Move string in UCI notation (e.g., 'e2e4', 'e7e8q')
            - move_encoding: Tensor encoding of the move
            - piece_types: List of piece types that can make this move
            - piece_encoding: One-hot tensor of piece types (size 6: pawn, knight, bishop, rook, queen, king)
    """

    PIECE_NAMES = ["pawn", "knight", "bishop", "rook", "queen", "king"]
    PIECE_TO_IDX = {name: idx for idx, name in enumerate(PIECE_NAMES)}

    # Files and ranks for move encoding
    FILES = "abcdefgh"
    RANKS = "12345678"

    def __init__(
        self,
        db_path: str | Path | None = None,
        transform: Any = None,
        vocab: dict[str, int] | None = None,
    ):
        self.db_path = str(db_path) if db_path else DB_FILE
        self.transform = transform
        self.data = self._load_data()

        # Build or use provided vocabulary
        if vocab is None:
            self.vocab = self._build_vocab()
        else:
            self.vocab = vocab

        self.idx_to_move = {idx: move for move, idx in self.vocab.items()}

    def _load_data(self) -> list[dict]:
        """Load all legal moves from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT move, types FROM legal_moves")
        rows = cursor.fetchall()
        conn.close()

        data = []
        for row in rows:
            move, types_str = row
            piece_types = types_str.split(",")
            data.append({"move": move, "piece_types": piece_types})

        return data

    def _build_vocab(self) -> dict[str, int]:
        """Build vocabulary mapping moves to indices."""
        vocab: dict[str, int] = {}
        for _idx, sample in enumerate(self.data):
            move = sample["move"]
            if move not in vocab:
                vocab[move] = len(vocab)
        return vocab

    def _encode_move(self, move: str) -> torch.Tensor:
        """Encode move as a tensor.

        For standard moves (e.g., 'e2e4'):
        - Creates a vector of [from_file, from_rank, to_file, to_rank]
        - Each coordinate is normalized to [0, 1]

        For promotions (e.g., 'e7e8q'):
        - Adds promotion piece type as 5th element

        Args:
            move: Move string in UCI notation

        Returns:
            Tensor of shape (4,) or (5,) for promotions
        """
        # Normalize move to lowercase for consistent parsing
        move = move.lower()

        # Extract from/to squares
        from_square = move[:2]
        to_square = move[2:4]

        # Parse coordinates
        from_file = self.FILES.index(from_square[0]) / 7.0
        from_rank = self.RANKS.index(from_square[1]) / 7.0
        to_file = self.FILES.index(to_square[0]) / 7.0
        to_rank = self.RANKS.index(to_square[1]) / 7.0

        encoding = [from_file, from_rank, to_file, to_rank]

        # Handle promotions
        if len(move) == 5:
            promotion_piece = move[4]
            # q=4, r=3, b=2, n=1 (matching chess piece values)
            promotion_map = {"q": 4, "r": 3, "b": 2, "n": 1}
            encoding.append(promotion_map.get(promotion_piece, 0) / 4.0)

        return torch.tensor(encoding, dtype=torch.float32)

    def _encode_piece_types(self, piece_types: list[str]) -> torch.Tensor:
        """Encode piece types as one-hot tensor.

        Args:
            piece_types: List of piece type names (e.g., ['pawn', 'queen'])

        Returns:
            Tensor of shape (6,) with 1s at indices of piece types
        """
        encoding = torch.zeros(6, dtype=torch.float32)
        for piece_type in piece_types:
            if piece_type in self.PIECE_TO_IDX:
                idx = self.PIECE_TO_IDX[piece_type]
                encoding[idx] = 1.0
        return encoding

    def get_move_from_index(self, idx: int) -> str:
        """Get move string from vocabulary index.

        Args:
            idx: Vocabulary index

        Returns:
            Move string in UCI notation
        """
        return self.idx_to_move.get(idx, "")

    def get_index_from_move(self, move: str) -> int:
        """Get vocabulary index from move string.

        Args:
            move: Move string in UCI notation

        Returns:
            Vocabulary index, or -1 if move not in vocabulary
        """
        return self.vocab.get(move, -1)

    def __len__(self) -> int:
        """Return the number of legal moves in the dataset."""
        return len(self.data)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        """Get a single legal move sample.

        Args:
            idx: Index of sample to retrieve

        Returns:
            Dictionary containing move encodings and metadata
        """
        sample = self.data[idx]
        move = sample["move"]
        piece_types = sample["piece_types"]

        move_encoding = self._encode_move(move)
        piece_encoding = self._encode_piece_types(piece_types)

        if self.transform:
            move_encoding = self.transform(move_encoding)

        return {
            "move": move,
            "move_encoding": move_encoding,
            "move_index": self.vocab[move],
            "piece_types": piece_types,
            "piece_encoding": piece_encoding,
        }


def collate_legal_moves(batch: list[dict]) -> dict[str, Any]:
    """Custom collate function for LegalMovesDataset.

    Handles variable-length move encodings (4 for normal moves, 5 for promotions)
    by padding all encodings to length 5.

    Args:
        batch: List of sample dictionaries from the dataset

    Returns:
        Dictionary with batched tensors
    """
    # Pad move encodings to uniform length (5)
    max_len = 5
    move_encodings = []
    for sample in batch:
        encoding = sample["move_encoding"]
        if len(encoding) < max_len:
            # Pad with zeros
            padding = torch.zeros(max_len - len(encoding))
            encoding = torch.cat([encoding, padding])
        move_encodings.append(encoding)

    return {
        "move": [sample["move"] for sample in batch],
        "move_encoding": torch.stack(move_encodings),
        "move_index": torch.tensor([sample["move_index"] for sample in batch]),
        "piece_types": [sample["piece_types"] for sample in batch],
        "piece_encoding": torch.stack([sample["piece_encoding"] for sample in batch]),
    }


if __name__ == "__main__":
    # Example usage of LegalMovesDataset
    print("Creating LegalMovesDataset...")
    dataset = LegalMovesDataset()

    print(f"\nDataset size: {len(dataset)} legal moves")
    print(f"Vocabulary size: {len(dataset.vocab)} unique moves")

    # Get a sample
    if len(dataset) > 0:
        sample = dataset[0]
        print("\nFirst sample:")
        print(f"  Move: {sample['move']}")
        print(f"  Move encoding shape: {sample['move_encoding'].shape}")
        print(f"  Move encoding: {sample['move_encoding']}")
        print(f"  Move index: {sample['move_index']}")
        print(f"  Piece types: {sample['piece_types']}")
        print(f"  Piece encoding: {sample['piece_encoding']}")

        # Demonstrate vocabulary lookup
        move_str = sample["move"]
        move_idx = dataset.get_index_from_move(move_str)
        reconstructed = dataset.get_move_from_index(move_idx)
        print("\nVocabulary lookup test:")
        print(f"  Original move: {move_str}")
        print(f"  Index: {move_idx}")
        print(f"  Reconstructed: {reconstructed}")

    # Use with DataLoader
    if len(dataset) > 0:
        from torch.utils.data import DataLoader

        print("\nCreating DataLoader...")
        dataloader = DataLoader(
            dataset, batch_size=32, shuffle=True, collate_fn=collate_legal_moves
        )

        # Get one batch
        batch = next(iter(dataloader))
        print("\nFirst batch:")
        print(f"  Batch size: {len(batch['move'])}")
        print(f"  Move encodings shape: {batch['move_encoding'].shape}")
        print(f"  Piece encodings shape: {batch['piece_encoding'].shape}")
        print(f"  Sample moves: {batch['move'][:5]}")
    else:
        print("\nDataset is empty. Cannot create DataLoader.")
        print("Run the dataset generation pipeline first to populate the database.")
