"""Tests for human player."""

import chess

from packages.play.src.player.human_player import HumanPlayer, HumanPlayerConfig


class TestHumanPlayerConfig:
    """Tests for HumanPlayerConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = HumanPlayerConfig(name="Alice", color=True)
        assert config.name == "Alice"
        assert config.color is True
        assert config.wins == 0
        assert config.losses == 0


class TestHumanPlayer:
    """Tests for HumanPlayer."""

    def test_initialization(self):
        """Test human player initialization."""
        config = HumanPlayerConfig(name="Human", color=True)
        player = HumanPlayer(config)

        assert player.config.name == "Human"
        assert player.config.color is True
        assert player.pending_move is None

    def test_get_move_without_pending(self):
        """Test get_move returns None when no pending move."""
        config = HumanPlayerConfig(name="Human", color=True)
        player = HumanPlayer(config)
        board = chess.Board()

        move = player.get_move(board)
        assert move is None

    def test_get_move_with_pending(self):
        """Test get_move returns and clears pending move."""
        config = HumanPlayerConfig(name="Human", color=True)
        player = HumanPlayer(config)
        board = chess.Board()

        # Set a pending move
        expected_move = chess.Move.from_uci("e2e4")
        player.pending_move = expected_move

        # Get the move
        move = player.get_move(board)
        assert move == expected_move

        # Verify pending move is cleared
        assert player.pending_move is None

    def test_multiple_get_moves(self):
        """Test that pending move is only returned once."""
        config = HumanPlayerConfig(name="Human", color=True)
        player = HumanPlayer(config)
        board = chess.Board()

        # Set a pending move
        player.pending_move = chess.Move.from_uci("e2e4")

        # First call returns the move
        move1 = player.get_move(board)
        assert move1 is not None

        # Second call returns None
        move2 = player.get_move(board)
        assert move2 is None

    def test_overwrite_pending_move(self):
        """Test that pending move can be overwritten."""
        config = HumanPlayerConfig(name="Human", color=True)
        player = HumanPlayer(config)
        board = chess.Board()

        # Set first pending move
        player.pending_move = chess.Move.from_uci("e2e4")

        # Overwrite with second move
        expected_move = chess.Move.from_uci("d2d4")
        player.pending_move = expected_move

        # Should get the second move
        move = player.get_move(board)
        assert move == expected_move
