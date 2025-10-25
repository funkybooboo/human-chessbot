"""Tests for CLI interface."""

from unittest.mock import patch

import chess
import pytest

from packages.play.src.game.game import Game, GameConfig
from packages.play.src.player.human_player import HumanPlayer, HumanPlayerConfig
from packages.play.src.player.random_bot_player import RandomBotPlayer, RandomBotPlayerConfig
from packages.play.src.ui.cli import Cli, CliConfig


class TestCliConfig:
    """Tests for CliConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CliConfig()
        assert config.loop_interval == 0.1

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CliConfig(loop_interval=0.5)
        assert config.loop_interval == 0.5

    def test_negative_interval_rejected(self):
        """Test that negative interval is rejected."""
        with pytest.raises(ValueError):
            CliConfig(loop_interval=-1)

    def test_zero_interval_rejected(self):
        """Test that zero interval is rejected."""
        with pytest.raises(ValueError):
            CliConfig(loop_interval=0)


class TestCli:
    """Tests for CLI interface."""

    @pytest.fixture
    def game(self):
        """Create a game instance."""
        white = RandomBotPlayer(RandomBotPlayerConfig(name="White", color=True))
        black = RandomBotPlayer(RandomBotPlayerConfig(name="Black", color=False))
        return Game(white, black, GameConfig())

    @pytest.fixture
    def cli(self, game):
        """Create a CLI instance."""
        return Cli(game, CliConfig(loop_interval=0.01))

    def test_initialization(self, cli, game):
        """Test CLI initialization."""
        assert cli.game == game
        assert cli.config.loop_interval == 0.01
        assert cli.move_history == []

    def test_display_board(self, cli, capsys):
        """Test board display."""
        cli.display_board()
        captured = capsys.readouterr()
        assert "♜" in captured.out or "r" in captured.out  # Rook symbol

    def test_show_message(self, cli, capsys):
        """Test message display."""
        cli.show_message("Test message")
        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_update_scores(self, cli, capsys):
        """Test score display."""
        cli.update_scores(39.0, 38.0)
        captured = capsys.readouterr()
        assert "39" in captured.out
        assert "38" in captured.out

    def test_update_move_list(self, cli, capsys):
        """Test move list update."""
        cli.update_move_list("e4")
        assert "e4" in cli.move_history

        captured = capsys.readouterr()
        assert "e4" in captured.out

    def test_update_move_list_multiple(self, cli):
        """Test multiple moves in history."""
        cli.update_move_list("e4")
        cli.update_move_list("e5")
        cli.update_move_list("Nf3")

        assert cli.move_history == ["e4", "e5", "Nf3"]

    def test_reset_ui(self, cli, capsys):
        """Test UI reset."""
        cli.update_move_list("e4")
        cli.update_move_list("e5")

        cli.reset_ui()

        assert cli.move_history == []
        captured = capsys.readouterr()
        assert "RESET" in captured.out

    def test_prompt_move_valid(self, cli):
        """Test prompting for a valid move."""
        human = HumanPlayer(HumanPlayerConfig(name="Human", color=True))

        with patch("builtins.input", return_value="e2e4"):
            move = cli._prompt_move(human)
            assert move == chess.Move.from_uci("e2e4")

    def test_prompt_move_invalid_then_valid(self, cli):
        """Test prompting with invalid move then valid."""
        human = HumanPlayer(HumanPlayerConfig(name="Human", color=True))

        # First return invalid, then valid
        with patch("builtins.input", side_effect=["e2e5", "e2e4"]):
            move = cli._prompt_move(human)
            assert move == chess.Move.from_uci("e2e4")

    def test_prompt_move_malformed_then_valid(self, cli):
        """Test prompting with malformed input then valid."""
        human = HumanPlayer(HumanPlayerConfig(name="Human", color=True))

        with patch("builtins.input", side_effect=["garbage", "e2e4"]):
            move = cli._prompt_move(human)
            assert move == chess.Move.from_uci("e2e4")

    def test_prompt_move_empty_then_valid(self, cli):
        """Test prompting with empty input then valid."""
        human = HumanPlayer(HumanPlayerConfig(name="Human", color=True))

        with patch("builtins.input", side_effect=["", "e2e4"]):
            move = cli._prompt_move(human)
            assert move == chess.Move.from_uci("e2e4")
