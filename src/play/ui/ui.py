from abc import ABC, abstractmethod
from src.play.game.game import Game

class Ui(ABC):
    """Abstract UI interface that any user interface (CLI, GUI, TUI) should implement."""

    game: Game

    def __init__(self, game: Game) -> None:
        """Initialize the UI with a game instance."""
        self.game = game

    @abstractmethod
    def run(self) -> None:
        """Start the game loop."""
        pass

    @abstractmethod
    def display_board(self) -> None:
        """Render the current board state."""
        pass

    @abstractmethod
    def show_message(self, message: str) -> None:
        """Show a message to the user (game over, invalid move, etc.)."""
        pass

    @abstractmethod
    def update_scores(self, white_score: int, black_score: int) -> None:
        """Update player scores."""
        pass

    @abstractmethod
    def update_move_list(self, move_san: str) -> None:
        """Update the move history display."""
        pass

    @abstractmethod
    def reset_ui(self) -> None:
        """Reset UI elements like move history or highlights."""
        pass
