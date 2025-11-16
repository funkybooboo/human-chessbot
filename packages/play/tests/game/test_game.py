"""Tests for game logic."""

import os
import tempfile
import time

import chess
import pytest

from packages.play.src.game.game import PIECE_VALUES, Game, GameConfig
from packages.play.src.player.random_bot_player import RandomBotPlayer, RandomBotPlayerConfig


class TestPieceValues:
    """Tests for PIECE_VALUES constant."""

    def test_piece_values_exist(self):
        """Test that all piece types have values."""
        assert chess.PAWN in PIECE_VALUES
        assert chess.KNIGHT in PIECE_VALUES
        assert chess.BISHOP in PIECE_VALUES
        assert chess.ROOK in PIECE_VALUES
        assert chess.QUEEN in PIECE_VALUES
        assert chess.KING in PIECE_VALUES

    def test_piece_values_correct(self):
        """Test standard piece values."""
        assert PIECE_VALUES[chess.PAWN] == 1.0
        assert PIECE_VALUES[chess.KNIGHT] == 3.0
        assert PIECE_VALUES[chess.BISHOP] == 3.0
        assert PIECE_VALUES[chess.ROOK] == 5.0
        assert PIECE_VALUES[chess.QUEEN] == 9.0
        assert PIECE_VALUES[chess.KING] == 0.0


class TestGameConfig:
    """Tests for GameConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        from packages.play.src.constants import GAME_SAVE_DIR, GAME_TIME_LIMIT

        config = GameConfig()
        assert config.save_dir == GAME_SAVE_DIR
        assert config.time_limit == GAME_TIME_LIMIT

    def test_custom_values(self):
        """Test custom configuration values."""
        config = GameConfig(save_dir="/tmp/chess", time_limit=300.0)
        assert config.save_dir == "/tmp/chess"
        assert config.time_limit == 300.0

    def test_negative_time_limit_rejected(self):
        """Test that negative time limit is rejected."""
        with pytest.raises(ValueError):
            GameConfig(time_limit=-1.0)

    def test_zero_time_limit_allowed(self):
        """Test that zero time limit is allowed (unlimited)."""
        config = GameConfig(time_limit=0.0)
        assert config.time_limit == 0.0


class TestGame:
    """Tests for Game class."""

    @pytest.fixture
    def white_player(self):
        """Create a white player."""
        return RandomBotPlayer(RandomBotPlayerConfig(name="White", color=True))

    @pytest.fixture
    def black_player(self):
        """Create a black player."""
        return RandomBotPlayer(RandomBotPlayerConfig(name="Black", color=False))

    @pytest.fixture
    def temp_save_dir(self):
        """Create a temporary save directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def game(self, white_player, black_player, temp_save_dir):
        """Create a game instance."""
        config = GameConfig(save_dir=temp_save_dir, time_limit=60.0)
        return Game(white_player, black_player, config)

    def test_initialization(self, game, white_player, black_player):
        """Test game initialization."""
        assert game.white_player == white_player
        assert game.black_player == black_player
        assert game.current_player == white_player
        assert game.board.turn == chess.WHITE
        assert game.last_move is None
        assert game.capture_square is None
        assert game.time_limit == 60.0
        assert game.white_time_left == 60.0
        assert game.black_time_left == 60.0

    def test_initial_board_state(self, game):
        """Test that board starts in initial position."""
        assert game.board.fen() == chess.STARTING_FEN

    def test_apply_move(self, game):
        """Test applying a move."""
        move = chess.Move.from_uci("e2e4")
        san = game.apply_move(move)

        assert san == "e4"
        assert game.last_move == move
        assert game.board.turn == chess.BLACK
        assert game.current_player == game.black_player

    def test_apply_capture_move(self, game):
        """Test applying a capture move."""
        # Set up a position with a capture available
        game.board.push(chess.Move.from_uci("e2e4"))
        game.board.push(chess.Move.from_uci("d7d5"))

        capture_move = chess.Move.from_uci("e4d5")
        san = game.apply_move(capture_move)

        assert "x" in san  # Capture notation
        assert game.capture_square == chess.D5

    def test_apply_non_capture_move(self, game):
        """Test that non-capture moves don't set capture_square."""
        move = chess.Move.from_uci("e2e4")
        game.apply_move(move)

        assert game.capture_square is None

    def test_reset(self, game):
        """Test game reset."""
        # Make some moves
        game.apply_move(chess.Move.from_uci("e2e4"))
        game.apply_move(chess.Move.from_uci("e7e5"))

        # Simulate time passing
        time.sleep(0.1)
        game.update_timer()

        # Reset the game
        game.reset()

        assert game.board.fen() == chess.STARTING_FEN
        assert game.last_move is None
        assert game.capture_square is None
        assert game.current_player == game.white_player
        assert game.white_time_left == game.time_limit
        assert game.black_time_left == game.time_limit

    def test_get_scores_initial(self, game):
        """Test material scores at start."""
        white_score, black_score = game.get_scores()
        assert white_score == 39.0  # 8 pawns + 2 knights + 2 bishops + 2 rooks + 1 queen
        assert black_score == 39.0

    def test_get_scores_after_capture(self, game):
        """Test material scores after a capture."""
        # Scholar's mate setup leading to capture
        game.apply_move(chess.Move.from_uci("e2e4"))
        game.apply_move(chess.Move.from_uci("e7e5"))
        game.apply_move(chess.Move.from_uci("d1h5"))
        game.apply_move(chess.Move.from_uci("b8c6"))
        game.apply_move(chess.Move.from_uci("f1c4"))
        game.apply_move(chess.Move.from_uci("g8f6"))
        game.apply_move(chess.Move.from_uci("h5f7"))  # Capture pawn

        white_score, black_score = game.get_scores()
        assert white_score == 39.0
        assert black_score == 38.0  # Lost a pawn

    def test_is_over_initial(self, game):
        """Test game is not over at start."""
        assert not game.is_over()

    def test_is_over_checkmate(self, game):
        """Test game is over on checkmate."""
        # Fool's mate
        game.apply_move(chess.Move.from_uci("f2f3"))
        game.apply_move(chess.Move.from_uci("e7e5"))
        game.apply_move(chess.Move.from_uci("g2g4"))
        game.apply_move(chess.Move.from_uci("d8h4"))  # Checkmate

        assert game.is_over()

    def test_is_over_timeout(self, game):
        """Test game is over on timeout."""
        # Simulate white running out of time
        game.white_time_left = 0.0

        assert game.is_over()

    def test_result_in_progress(self, game):
        """Test result when game is in progress."""
        assert game.result() == "*"

    def test_result_white_wins_checkmate(self, game):
        """Test result when white wins by checkmate."""
        # Scholar's mate
        game.apply_move(chess.Move.from_uci("e2e4"))
        game.apply_move(chess.Move.from_uci("e7e5"))
        game.apply_move(chess.Move.from_uci("d1h5"))
        game.apply_move(chess.Move.from_uci("b8c6"))
        game.apply_move(chess.Move.from_uci("f1c4"))
        game.apply_move(chess.Move.from_uci("g8f6"))
        game.apply_move(chess.Move.from_uci("h5f7"))  # Checkmate

        assert game.result() == "1-0"

    def test_result_black_wins_checkmate(self, game):
        """Test result when black wins by checkmate."""
        # Fool's mate
        game.apply_move(chess.Move.from_uci("f2f3"))
        game.apply_move(chess.Move.from_uci("e7e5"))
        game.apply_move(chess.Move.from_uci("g2g4"))
        game.apply_move(chess.Move.from_uci("d8h4"))  # Checkmate

        assert game.result() == "0-1"

    def test_result_white_wins_timeout(self, game):
        """Test result when black times out."""
        game.black_time_left = 0.0
        assert game.result() == "1-0"

    def test_result_black_wins_timeout(self, game):
        """Test result when white times out."""
        game.white_time_left = 0.0
        assert game.result() == "0-1"

    def test_update_timer_white_turn(self, game):
        """Test timer update on white's turn."""
        initial_time = game.white_time_left
        time.sleep(0.1)
        winner = game.update_timer()

        assert winner is None
        assert game.white_time_left < initial_time
        assert game.black_time_left == game.time_limit

    def test_update_timer_black_turn(self, game):
        """Test timer update on black's turn."""
        # Make white's move
        game.apply_move(chess.Move.from_uci("e2e4"))

        initial_time = game.black_time_left
        time.sleep(0.1)
        winner = game.update_timer()

        assert winner is None
        assert game.black_time_left < initial_time

    def test_update_timer_white_timeout(self, game):
        """Test timeout detection for white."""
        game.white_time_left = 0.01
        time.sleep(0.02)
        winner = game.update_timer()

        assert winner == game.black_player

    def test_update_timer_black_timeout(self, game):
        """Test timeout detection for black."""
        game.apply_move(chess.Move.from_uci("e2e4"))
        game.black_time_left = 0.01
        time.sleep(0.02)
        winner = game.update_timer()

        assert winner == game.white_player

    def test_save_game(self, game, temp_save_dir):  # noqa: ARG002
        """Test saving game to PGN."""
        # Make a few moves
        game.apply_move(chess.Move.from_uci("e2e4"))
        game.apply_move(chess.Move.from_uci("e7e5"))

        filename = game.save_game()

        assert os.path.exists(filename)
        assert filename.endswith(".pgn")
        assert "White_vs_Black" in filename

        # Check file contents
        with open(filename) as f:
            content = f.read()
            assert '[White "White"]' in content
            assert '[Black "Black"]' in content
            assert "e4" in content
            assert "e5" in content

    def test_save_game_creates_directory(self, white_player, black_player):
        """Test that save_game creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_dir = os.path.join(tmpdir, "new_dir", "games")
            config = GameConfig(save_dir=save_dir, time_limit=60.0)
            game = Game(white_player, black_player, config)

            filename = game.save_game()

            assert os.path.exists(save_dir)
            assert os.path.exists(filename)

    def test_save_game_with_result(self, game):
        """Test saving game with a result."""
        # Play fool's mate
        game.apply_move(chess.Move.from_uci("f2f3"))
        game.apply_move(chess.Move.from_uci("e7e5"))
        game.apply_move(chess.Move.from_uci("g2g4"))
        game.apply_move(chess.Move.from_uci("d8h4"))  # Checkmate

        filename = game.save_game()

        with open(filename) as f:
            content = f.read()
            assert '[Result "0-1"]' in content
