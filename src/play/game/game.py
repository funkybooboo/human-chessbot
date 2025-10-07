from __future__ import annotations

import datetime
import os
import chess
import chess.pgn
import time
from pydantic import BaseModel, Field
from typing import Optional, Tuple, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.play.player.player import Player
    from src.play.ui.ui import Ui


PIECE_VALUES: Dict[int, float] = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

class GameConfig(BaseModel):
    save_dir: str = Field(default="games", title="Save Directory")
    time_limit: float = Field(default=600.0, ge=0, title="Time Limit (in seconds)")


class Game:
    def __init__(self,
                 white_player: 'Player',
                 black_player: 'Player',
                 config: GameConfig,
                 ui: Optional['Ui'] = None) -> None:
        self.board: chess.Board = chess.Board()
        self.white_player: 'Player' = white_player
        self.black_player: 'Player' = black_player
        self.current_player: 'Player' = self.white_player if self.board.turn else self.black_player
        self.last_move: Optional[chess.Move] = None
        self.capture_square: Optional[int] = None
        self.config: GameConfig = config  # Configuration passed from GameConfig

        # Timer in seconds
        self.time_limit: float = self.config.time_limit
        self.white_time_left: float = self.time_limit
        self.black_time_left: float = self.time_limit
        self._last_time_update: float = time.time()

        self.ui: Optional['Ui'] = ui
        self.save_dir: str = self.config.save_dir

    def update_timer(self) -> Optional['Player']:
        """
        Update timers for both players, returns the player who wins on timeout, or None.
        Call this once per game loop iteration.
        """
        now: float = time.time()
        elapsed: float = now - self._last_time_update
        self._last_time_update = now

        if self.board.turn:  # White's turn
            self.white_time_left -= elapsed
        else:  # Black's turn
            self.black_time_left -= elapsed

        if self.white_time_left <= 0:
            return self.black_player
        elif self.black_time_left <= 0:
            return self.white_player
        return None

    def apply_move(self, move: chess.Move) -> str:
        """
        Apply a move to the board and update game state.
        """
        move_san: str = self.board.san(move)
        self.board.push(move)
        self.last_move = move
        self.capture_square = move.to_square if self.board.is_capture(move) else None
        self.current_player = self.white_player if self.board.turn else self.black_player
        return move_san

    def reset(self) -> None:
        self.board.reset()
        self.last_move = None
        self.capture_square = None
        self.current_player = self.white_player if self.board.turn else self.black_player
        self.white_time_left = self.time_limit
        self.black_time_left = self.time_limit
        self._last_time_update = time.time()

    def get_scores(self) -> Tuple[float, float]:
        white_score: float = 0
        black_score: float = 0
        for sq in chess.SQUARES:
            piece: Optional[chess.Piece] = self.board.piece_at(sq)
            if piece:
                value: float = PIECE_VALUES[piece.piece_type]
                if piece.color == chess.WHITE:
                    white_score += value
                else:
                    black_score += value
        return white_score, black_score

    def is_over(self) -> bool:
        return self.board.is_game_over() or self.white_time_left <= 0 or self.black_time_left <= 0

    def result(self) -> str:
        if self.white_time_left <= 0:
            return "0-1"  # White flag
        if self.black_time_left <= 0:
            return "1-0"  # Black flag
        return self.board.result() if self.board.is_game_over() else "*"

    def save_game(self) -> str:
        os.makedirs(self.save_dir, exist_ok=True)
        game_pgn: chess.pgn.Game = chess.pgn.Game()
        game_pgn.headers["Event"] = "Friendly Match"
        game_pgn.headers["White"] = self.white_player.config.name
        game_pgn.headers["Black"] = self.black_player.config.name
        game_pgn.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        game_pgn.headers["Result"] = self.result()

        node: chess.pgn.GameNode = game_pgn
        for move in self.board.move_stack:
            node = node.add_variation(move)

        filename: str = os.path.join(
            self.save_dir,
            f"{self.white_player.config.name}_vs_{self.black_player.config.name}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pgn"
        )
        with open(filename, "w", encoding="utf-8") as f:
            print(game_pgn, file=f)
        return filename
