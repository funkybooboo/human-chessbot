"""Tests for base player class."""

import chess
import pytest

from packages.play.src.player.player import Player, PlayerConfig


class MockPlayer(Player):
    """Mock player for testing abstract base class."""

    def get_move(self, board: chess.Board):
        """Return first legal move."""
        moves = list(board.legal_moves)
        return moves[0] if moves else None


class TestPlayerConfig:
    """Tests for PlayerConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = PlayerConfig(name="Test", color=True)
        assert config.name == "Test"
        assert config.color is True
        assert config.wins == 0
        assert config.losses == 0

    def test_custom_values(self):
        """Test custom configuration values."""
        config = PlayerConfig(name="Custom", color=False, wins=5, losses=3)
        assert config.name == "Custom"
        assert config.color is False
        assert config.wins == 5
        assert config.losses == 3

    def test_negative_wins_rejected(self):
        """Test that negative wins are rejected."""
        with pytest.raises(ValueError):
            PlayerConfig(name="Test", color=True, wins=-1)

    def test_negative_losses_rejected(self):
        """Test that negative losses are rejected."""
        with pytest.raises(ValueError):
            PlayerConfig(name="Test", color=True, losses=-1)


class TestPlayer:
    """Tests for Player base class."""

    def test_initialization(self):
        """Test player initialization."""
        config = PlayerConfig(name="TestPlayer", color=True)
        player = MockPlayer(config)
        assert player.config == config
        assert player.config.name == "TestPlayer"
        assert player.config.color is True

    def test_record_win(self):
        """Test recording wins."""
        config = PlayerConfig(name="Test", color=True)
        player = MockPlayer(config)

        assert player.config.wins == 0
        player.record_win()
        assert player.config.wins == 1
        player.record_win()
        assert player.config.wins == 2

    def test_record_loss(self):
        """Test recording losses."""
        config = PlayerConfig(name="Test", color=True)
        player = MockPlayer(config)

        assert player.config.losses == 0
        player.record_loss()
        assert player.config.losses == 1
        player.record_loss()
        assert player.config.losses == 2

    def test_get_move_returns_legal_move(self):
        """Test that get_move returns a legal move."""
        config = PlayerConfig(name="Test", color=True)
        player = MockPlayer(config)
        board = chess.Board()

        move = player.get_move(board)
        assert move is not None
        assert move in board.legal_moves

    def test_get_move_on_empty_board(self):
        """Test get_move when no legal moves available."""
        config = PlayerConfig(name="Test", color=True)
        player = MockPlayer(config)

        # Create a board with no legal moves (stalemate position)
        board = chess.Board("7k/8/8/8/8/8/8/K7 w - - 0 1")
        board.push(chess.Move.from_uci("a1a2"))  # White king moves
        board = chess.Board("7k/8/6Q1/8/8/5K2/8/8 b - - 0 1")  # Stalemate

        move = player.get_move(board)
        assert move is None
