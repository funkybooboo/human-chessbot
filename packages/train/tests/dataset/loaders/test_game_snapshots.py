from unittest.mock import patch

import pytest

from packages.train.src.dataset.loaders.game_snapshots import GameSnapshotsDataset


class TestGameSnapshotsDataset:
    """Tests for the GameSnapshotsDataset class."""

    @patch("packages.train.src.dataset.loaders.game_snapshots.count_snapshots")
    def test_num_indexes_exceeds_database_count(self, mock_count_snapshots):
        """Test ValueError raised when num_indexes exceeds database snapshot count."""
        mock_count_snapshots.return_value = 100  # Mock snapshot count
        with pytest.raises(ValueError, match="num_indexes is larger than the size of the database"):
            GameSnapshotsDataset(start_index=50, num_indexes=60, db_path=":memory:")

    def test_fen_to_tensor(self):
        """Test conversion of FEN string to tensor."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"  # Starting position
        tensor = dataset.fen_to_tensor(fen)
        assert tensor.shape.numel() == (8 * 8 * 12)
        assert tensor.sum().item() == 32  # 32 pieces on the board

    def test_encode_result(self):
        """Test encoding of game results based on the player's perspective."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        result_win = dataset.encode_result("1-0", "w")
        result_draw = dataset.encode_result("1/2-1/2", "b")
        result_loss = dataset.encode_result("0-1", "w")
        assert result_win.item() == 1.0
        assert result_draw.item() == 0.5
        assert result_loss.item() == 0.0

    def test_encode_turn(self):
        """Test encoding of player turn as one-hot vector."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        turn_white = dataset.encode_turn("w")
        turn_black = dataset.encode_turn("b")
        assert list(turn_white.numpy()) == [1.0, 0.0]
        assert list(turn_black.numpy()) == [0.0, 1.0]

    def test_normalize_elo(self):
        """Test normalization of ELO ratings."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        result = dataset.normalize_elo(2000, 1500)
        assert result.shape == (2,)
        assert pytest.approx(result[0].item(), 0.001) == (2000 - 1638.43153) / 185.80054702756055
        assert pytest.approx(result[1].item(), 0.001) == (1500 - 1638.43153) / 185.80054702756055

    def test_encode_move_valid(self):
        """Test encoding of valid chess move."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move_san = "e4"
        move = dataset._encode_move(fen, move_san)
        assert isinstance(move, int)

    def test_encode_move_invalid(self):
        """Test encoding of invalid chess move."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        move_san = "invalid_move"
        move = dataset._encode_move(fen, move_san)
        assert move == 0

    def test_len_method(self):
        """Test the __len__ method for dataset size."""
        dataset = GameSnapshotsDataset(start_index=0, num_indexes=10, db_path=":memory:")
        assert len(dataset) == 10

    def test_fen_to_tensor_empty_board(self):
        """Test tensor for empty board with just kings."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        # Just kings on board: white king e1, black king e8
        fen = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"
        tensor = dataset.fen_to_tensor(fen)
        assert tensor.sum().item() == 2  # Only 2 pieces

    def test_fen_to_tensor_piece_positions(self):
        """Test that specific pieces are correctly encoded in tensor."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        # Position with white pawn on e4
        fen = "4k3/8/8/8/4P3/8/8/4K3 w - - 0 1"
        tensor = dataset.fen_to_tensor(fen)
        # Tensor shape is (12, 8, 8) - channel 0 is white pawns
        # e4 is file 4 (e), rank 3 (0-indexed from a1)
        assert tensor[0, 3, 4].item() == 1.0  # White pawn at e4

    def test_encode_result_black_perspective(self):
        """Test result encoding from black's perspective."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        # Black wins (0-1) from black's perspective = win (1.0)
        assert dataset.encode_result("0-1", "b").item() == 1.0
        # White wins (1-0) from black's perspective = loss (0.0)
        assert dataset.encode_result("1-0", "b").item() == 0.0

    def test_normalize_elo_typical_rating(self):
        """Test that typical Elo ratings normalize to values near 0."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        # 1600 is close to mean (1638), should normalize close to 0
        result = dataset.normalize_elo(1600, 1600)
        assert abs(result[0].item()) < 0.5
        assert abs(result[1].item()) < 0.5

    def test_normalize_elo_extreme_ratings(self):
        """Test normalization of extreme Elo ratings."""
        dataset = GameSnapshotsDataset(0, 1, db_path=":memory:")
        result = dataset.normalize_elo(2800, 800)
        # 2800 should be positive (above mean), 800 should be negative (below mean)
        assert result[0].item() > 0
        assert result[1].item() < 0
