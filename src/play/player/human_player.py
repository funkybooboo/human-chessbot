from typing import Optional

import chess

from src.play.player.player import Player, PlayerConfig


class HumanPlayer(Player):
    def __init__(self, config: PlayerConfig) -> None:
        super().__init__(config)
        self.pending_move: Optional[chess.Move] = None  # GUI sets this when user makes a move

    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Wait for the GUI to set pending_move."""
        if self.pending_move:
            move = self.pending_move
            self.pending_move = None
            return move
        return None
