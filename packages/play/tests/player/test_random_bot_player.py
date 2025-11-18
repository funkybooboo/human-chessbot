"""Tests for random bot player."""

import chess

from packages.play.src.player.random_bot_player import RandomBotPlayer, RandomBotPlayerConfig


class TestRandomBotPlayerConfig:
    """Tests for RandomBotPlayerConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RandomBotPlayerConfig(name="RandomBot", color=True)
        assert config.name == "RandomBot"
        assert config.color is True


class TestRandomBotPlayer:
    """Tests for RandomBotPlayer."""

    def test_initialization(self):
        """Test random bot initialization."""
        config = RandomBotPlayerConfig(name="Randy", color=False)
        player = RandomBotPlayer(config)

        assert player.config.name == "Randy"
        assert player.config.color is False

    def test_get_move_returns_legal_move(self):
        """Test that random bot returns a legal move."""
        config = RandomBotPlayerConfig(name="Randy", color=True)
        player = RandomBotPlayer(config)
        board = chess.Board()

        move = player.get_move(board)
        assert move is not None
        assert move in board.legal_moves

    def test_get_move_from_various_positions(self):
        """Test random bot on various board positions."""
        config = RandomBotPlayerConfig(name="Randy", color=True)
        player = RandomBotPlayer(config)

        # Test on starting position
        board = chess.Board()
        move = player.get_move(board)
        assert move is not None
        assert move in board.legal_moves

        # Test after a few moves
        board.push(chess.Move.from_uci("e2e4"))
        board.push(chess.Move.from_uci("e7e5"))
        move = player.get_move(board)
        assert move is not None
        assert move in board.legal_moves

    def test_get_move_randomness(self):
        """Test that random bot makes different moves across multiple games."""
        config = RandomBotPlayerConfig(name="Randy", color=True)
        player = RandomBotPlayer(config)

        # Collect 20 moves from starting position
        moves = []
        for _ in range(20):
            board = chess.Board()
            move = player.get_move(board)
            moves.append(move)

        # Should have at least 2 different moves (very likely with 20 samples)
        unique_moves = set(moves)
        assert len(unique_moves) >= 2

    def test_get_move_on_stalemate(self):
        """Test get_move when no legal moves available."""
        config = RandomBotPlayerConfig(name="Randy", color=False)
        player = RandomBotPlayer(config)

        # Stalemate position for black
        board = chess.Board("7k/8/6Q1/8/8/5K2/8/8 b - - 0 1")

        move = player.get_move(board)
        assert move is None

    def test_get_move_in_check(self):
        """Test random bot can handle check positions."""
        config = RandomBotPlayerConfig(name="Randy", color=False)
        player = RandomBotPlayer(config)

        # Black is in check
        board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPPQPPP/RNB1KBNR b KQkq - 0 1")

        move = player.get_move(board)
        assert move is not None
        assert move in board.legal_moves

        # Move should resolve the check
        board.push(move)
        assert not board.is_check()
