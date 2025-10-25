"""Tests for base UI class."""

import pytest

from packages.play.src.game.game import Game, GameConfig
from packages.play.src.player.random_bot_player import RandomBotPlayer, RandomBotPlayerConfig
from packages.play.src.ui.ui import Ui


class MockUi(Ui):
    """Mock UI implementation for testing."""

    def __init__(self, game: Game):
        super().__init__(game)
        self.run_called = False
        self.display_board_called = False
        self.messages: list[str] = []
        self.score_updates: list[tuple[float, float]] = []
        self.move_list: list[str] = []
        self.reset_count = 0

    def run(self):
        self.run_called = True

    def display_board(self):
        self.display_board_called = True

    def show_message(self, message: str):
        self.messages.append(message)

    def update_scores(self, white_score: float, black_score: float):
        self.score_updates.append((white_score, black_score))

    def update_move_list(self, move_san: str):
        self.move_list.append(move_san)

    def reset_ui(self):
        self.reset_count += 1


class TestUi:
    """Tests for UI base class."""

    @pytest.fixture
    def game(self):
        """Create a game instance."""
        white = RandomBotPlayer(RandomBotPlayerConfig(name="White", color=True))
        black = RandomBotPlayer(RandomBotPlayerConfig(name="Black", color=False))
        return Game(white, black, GameConfig())

    @pytest.fixture
    def ui(self, game):
        """Create a mock UI instance."""
        return MockUi(game)

    def test_initialization(self, ui, game):
        """Test UI initialization."""
        assert ui.game == game

    def test_run_is_abstract(self):
        """Test that run must be implemented."""
        # This is verified by the fact that MockUi must implement run

    def test_display_board_is_abstract(self):
        """Test that display_board must be implemented."""
        # This is verified by the fact that MockUi must implement display_board

    def test_show_message(self, ui):
        """Test show_message recording."""
        ui.show_message("Test message")
        assert "Test message" in ui.messages

    def test_update_scores(self, ui):
        """Test update_scores recording."""
        ui.update_scores(39.0, 39.0)
        assert (39.0, 39.0) in ui.score_updates

    def test_update_move_list(self, ui):
        """Test update_move_list recording."""
        ui.update_move_list("e4")
        assert "e4" in ui.move_list

    def test_reset_ui(self, ui):
        """Test reset_ui tracking."""
        ui.reset_ui()
        assert ui.reset_count == 1
        ui.reset_ui()
        assert ui.reset_count == 2
