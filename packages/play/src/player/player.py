"""Base player interface for chess players."""

from abc import ABC, abstractmethod

import chess
from pydantic import BaseModel, Field


class PlayerConfig(BaseModel):
    """Base configuration for all chess players.

    Attributes:
        name: Player name displayed in the UI
        color: True for White, False for Black
        wins: Total number of wins (tracked automatically)
        losses: Total number of losses (tracked automatically)
    """

    name: str = Field(..., description="Player name")
    color: bool = Field(..., description="True for White, False for Black")
    wins: int = Field(default=0, ge=0, description="Number of wins")
    losses: int = Field(default=0, ge=0, description="Number of losses")


class Player(ABC):
    """Abstract base class for all chess players.

    All player implementations (human, bot, etc.) must inherit from this class
    and implement the get_move method.
    """

    def __init__(self, config: PlayerConfig) -> None:
        """Initialize player with configuration.

        Args:
            config: Player configuration including name, color, and stats.
        """
        self.config = config

    def record_win(self) -> None:
        """Increment the win counter for this player."""
        self.config.wins += 1

    def record_loss(self) -> None:
        """Increment the loss counter for this player."""
        self.config.losses += 1

    @abstractmethod
    def get_move(self, board: chess.Board) -> chess.Move | None:
        """Return a move to play on the given board.

        Args:
            board: Current chess board state.

        Returns:
            A legal chess move, or None if no move is available.
        """
        pass
