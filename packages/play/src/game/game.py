"""Chess game logic and state management."""

from __future__ import annotations

import datetime
import os
import time
from typing import TYPE_CHECKING

import chess
import chess.pgn
from pydantic import BaseModel, Field

from packages.play.src.constants import GAME_SAVE_DIR, GAME_TIME_LIMIT

if TYPE_CHECKING:
    from packages.play.src.player.player import Player
    from packages.play.src.ui.ui import Ui

# Standard piece values for material counting
PIECE_VALUES: dict[int, float] = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 3.0,
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
    chess.KING: 0.0,
}


class GameConfig(BaseModel):
    """Configuration for chess games.

    Attributes:
        save_dir: Directory where game PGN files will be saved
        time_limit: Total time per player in seconds (0 = unlimited)
    """

    save_dir: str = Field(default=GAME_SAVE_DIR, description="Directory for saving PGN files")
    time_limit: float = Field(
        default=GAME_TIME_LIMIT, ge=0, description="Time limit per player in seconds"
    )


class Game:
    """Represents a chess game with two players and time controls.

    Manages the chess board, player turns, move history, time controls,
    and game state (check, checkmate, stalemate, etc.).
    """

    def __init__(
        self, white_player: Player, black_player: Player, config: GameConfig, ui: Ui | None = None
    ) -> None:
        """Initialize a new chess game.

        Args:
            white_player: Player controlling white pieces
            black_player: Player controlling black pieces
            config: Game configuration (time limits, save directory, etc.)
            ui: Optional UI for displaying the game
        """
        self.board: chess.Board = chess.Board()
        self.white_player: Player = white_player
        self.black_player: Player = black_player
        self.current_player: Player = self.white_player
        self.last_move: chess.Move | None = None
        self.capture_square: int | None = None
        self.config: GameConfig = config

        # Time control
        self.time_limit: float = config.time_limit
        self.white_time_left: float = self.time_limit
        self.black_time_left: float = self.time_limit
        self._last_time_update: float = time.time()

        self.ui: Ui | None = ui
        self.save_dir: str = config.save_dir

        print(
            f"Game initialized: {white_player.config.name} (White) vs "
            f"{black_player.config.name} (Black), Time: {self.time_limit}s"
        )

    def update_timer(self) -> Player | None:
        """Update game timers and check for timeout.

        Deducts elapsed time from the current player's clock.
        Should be called once per game loop iteration.

        Returns:
            The player who won on time, or None if no timeout occurred.
        """
        now: float = time.time()
        elapsed: float = now - self._last_time_update
        self._last_time_update = now

        # Deduct time from current player
        if self.board.turn:  # White's turn
            self.white_time_left -= elapsed
        else:  # Black's turn
            self.black_time_left -= elapsed

        # Check for timeout
        if self.white_time_left <= 0:
            print(f"White ({self.white_player.config.name}) ran out of time")
            return self.black_player
        elif self.black_time_left <= 0:
            print(f"Black ({self.black_player.config.name}) ran out of time")
            return self.white_player

        return None

    def apply_move(self, move: chess.Move) -> str:
        """Apply a move to the board and update game state.

        Args:
            move: The chess move to apply.

        Returns:
            The move in Standard Algebraic Notation (SAN).
        """
        # Convert to SAN before applying (requires pre-move board state)
        move_san: str = self.board.san(move)

        # Apply the move
        is_capture = self.board.is_capture(move)
        self.board.push(move)

        # Update game state
        self.last_move = move
        self.capture_square = move.to_square if is_capture else None
        self.current_player = self.white_player if self.board.turn else self.black_player

        return move_san

    def reset(self) -> None:
        """Reset the game to initial state.

        Resets board, timers, and clears move history.
        """
        self.board.reset()
        self.last_move = None
        self.capture_square = None
        self.current_player = self.white_player
        self.white_time_left = self.time_limit
        self.black_time_left = self.time_limit
        self._last_time_update = time.time()
        print("Game reset")

    def get_scores(self) -> tuple[float, float]:
        """Calculate material scores for both players.

        Counts piece values using standard valuations:
        Pawn=1, Knight=3, Bishop=3, Rook=5, Queen=9, King=0

        Returns:
            Tuple of (white_score, black_score).
        """
        white_score: float = 0.0
        black_score: float = 0.0

        for square in chess.SQUARES:
            piece: chess.Piece | None = self.board.piece_at(square)
            if piece:
                value: float = PIECE_VALUES[piece.piece_type]
                if piece.color == chess.WHITE:
                    white_score += value
                else:
                    black_score += value

        return white_score, black_score

    def is_over(self) -> bool:
        """Check if the game is over.

        A game is over if:
        - Checkmate, stalemate, or other chess rule ending
        - Either player has run out of time

        Returns:
            True if game is over, False otherwise.
        """
        return self.board.is_game_over() or self.white_time_left <= 0 or self.black_time_left <= 0

    def result(self) -> str:
        """Get the game result.

        Returns:
            Game result in PGN format:
            - "1-0": White wins
            - "0-1": Black wins
            - "1/2-1/2": Draw
            - "*": Game in progress
        """
        if self.white_time_left <= 0:
            return "0-1"  # Black wins on time
        if self.black_time_left <= 0:
            return "1-0"  # White wins on time
        return self.board.result() if self.board.is_game_over() else "*"

    def save_game(self) -> str:
        """Save the game to a PGN file.

        Creates the save directory if it doesn't exist.
        Filename format: {white}_vs_{black}_{timestamp}.pgn

        Returns:
            The full path to the saved PGN file.
        """
        os.makedirs(self.save_dir, exist_ok=True)

        # Create PGN game object
        game_pgn: chess.pgn.Game = chess.pgn.Game()
        game_pgn.headers["Event"] = "Friendly Match"
        game_pgn.headers["White"] = self.white_player.config.name
        game_pgn.headers["Black"] = self.black_player.config.name
        game_pgn.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        game_pgn.headers["Result"] = self.result()

        # Add all moves to PGN
        node: chess.pgn.GameNode = game_pgn
        for move in self.board.move_stack:
            node = node.add_variation(move)

        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename: str = os.path.join(
            self.save_dir,
            f"{self.white_player.config.name}_vs_{self.black_player.config.name}_{timestamp}.pgn",
        )

        # Write to file
        with open(filename, "w", encoding="utf-8") as f:
            print(game_pgn, file=f)

        print(f"Game saved to {filename}")
        return filename
