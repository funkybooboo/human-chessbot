import random
from typing import Optional

import chess

from src.play.player.player import Player


class RandomBotPlayer(Player):
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Return a random legal move"""
        moves = list(board.legal_moves)
        return random.choice(moves) if moves else None
