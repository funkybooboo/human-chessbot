"""Human player implementation."""

import chess

from packages.play.src.player.player import Player, PlayerConfig


class HumanPlayerConfig(PlayerConfig):
    """Configuration for human player.

    Attributes:
        name: Player name
        color: True for white, False for black
        wins: Number of wins (tracked automatically)
        losses: Number of losses (tracked automatically)
    """

    name: str = "Human"
    color: bool = True


class HumanPlayer(Player):
    """Human player that receives moves from the UI.

    The UI (GUI or CLI) is responsible for setting the pending_move
    attribute when the human makes a move.
    """

    def __init__(self, config: HumanPlayerConfig) -> None:
        """Initialize human player.

        Args:
            config: Configuration for the human player.
        """
        super().__init__(config)
        self.pending_move: chess.Move | None = None

    def get_move(self, board: chess.Board) -> chess.Move | None:
        """Return the pending move if available.

        The UI sets pending_move when the user selects a move.

        Args:
            board: Current board state (not used, but required by interface).

        Returns:
            The pending move if available, otherwise None.
        """
        if self.pending_move:
            move = self.pending_move
            self.pending_move = None
            return move
        return None
