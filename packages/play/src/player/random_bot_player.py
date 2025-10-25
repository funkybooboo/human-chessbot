"""Random move chess bot player implementation."""

import random

import chess

from packages.play.src.player.player import Player, PlayerConfig


class RandomBotPlayerConfig(PlayerConfig):
    """Configuration for random bot player.

    Attributes:
        name: Player name
        color: True for white, False for black
        wins: Number of wins (tracked automatically)
        losses: Number of losses (tracked automatically)
    """

    name: str = "RandomBot"
    color: bool = True


class RandomBotPlayer(Player):
    """Chess bot that plays random legal moves.

    Useful for testing and baseline comparison.
    """

    def __init__(self, config: RandomBotPlayerConfig) -> None:
        """Initialize random bot player.

        Args:
            config: Configuration for the random bot.
        """
        super().__init__(config)

    def get_move(self, board: chess.Board) -> chess.Move | None:
        """Return a random legal move.

        Args:
            board: Current board state.

        Returns:
            A random legal move, or None if no legal moves are available.
        """
        moves = list(board.legal_moves)
        return random.choice(moves) if moves else None
