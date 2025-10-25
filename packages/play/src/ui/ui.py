"""Base user interface abstract class."""

from abc import ABC, abstractmethod

from packages.play.src.game.game import Game


class Ui(ABC):
    """Abstract base class for all user interfaces.

    Any UI implementation (CLI, GUI, TUI, web, etc.) must inherit
    from this class and implement all abstract methods.
    """

    def __init__(self, game: Game) -> None:
        """Initialize the UI with a game instance.

        Args:
            game: The chess game to display and interact with.
        """
        self.game: Game = game

    @abstractmethod
    def run(self) -> None:
        """Start the UI and game loop.

        This method should not return until the game is over or
        the user quits.
        """
        pass

    @abstractmethod
    def display_board(self) -> None:
        """Render the current board state.

        Should display pieces, highlights, and other visual elements.
        """
        pass

    @abstractmethod
    def show_message(self, message: str) -> None:
        """Display a message to the user.

        Args:
            message: Message to display (e.g., "Game Over", "Invalid move", etc.)
        """
        pass

    @abstractmethod
    def update_scores(self, white_score: float, black_score: float) -> None:
        """Update the material score display.

        Args:
            white_score: White's material score
            black_score: Black's material score
        """
        pass

    @abstractmethod
    def update_move_list(self, move_san: str) -> None:
        """Add a move to the move history display.

        Args:
            move_san: Move in Standard Algebraic Notation (e.g., "Nf3", "e4")
        """
        pass

    @abstractmethod
    def reset_ui(self) -> None:
        """Reset UI elements to initial state.

        Clears move history, highlights, and other transient UI elements.
        """
        pass
