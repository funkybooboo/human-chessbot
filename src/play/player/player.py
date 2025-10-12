from typing import Optional

import chess
from abc import ABC, abstractmethod

from pydantic import BaseModel


class PlayerConfig(BaseModel):
    name: str
    color: bool  # True = White, False = Black
    wins: int = 0
    losses: int = 0


class Player(ABC):
    def __init__(self, config: PlayerConfig) -> None:
        self.config = config

    def record_win(self) -> None:
        """Increment wins"""
        self.config.wins += 1

    def record_loss(self) -> None:
        """Increment losses"""
        self.config.losses += 1

    @abstractmethod
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Return a move to play on the given board."""
        pass
