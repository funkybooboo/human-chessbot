"""Stockfish chess engine player implementation."""

import logging
import shutil

import chess
import chess.engine

from packages.play.src.player.player import Player, PlayerConfig

logger = logging.getLogger(__name__)


class StockfishPlayerConfig(PlayerConfig):
    """Configuration for Stockfish chess bot.

    Attributes:
        name: Player name
        color: True for white, False for black
        skill_level: Stockfish skill level (0-20, where 20 is strongest)
        time_limit: Time per move in seconds
        wins: Number of wins (tracked automatically)
        losses: Number of losses (tracked automatically)
    """

    name: str = "Stockfish"
    color: bool = True
    skill_level: int = 10
    time_limit: float = 0.5


class StockfishPlayer(Player):
    """Chess bot powered by the Stockfish engine.

    Setup Instructions:
        1. Install Stockfish:
           - Linux (Debian/Ubuntu): sudo apt install stockfish
           - macOS: brew install stockfish
           - Windows: Download from https://stockfishchess.org/download/
        2. Ensure stockfish is in your PATH
    """

    def __init__(self, config: StockfishPlayerConfig) -> None:
        """Initialize Stockfish player.

        Args:
            config: Configuration parameters for the Stockfish bot.

        Raises:
            FileNotFoundError: If stockfish binary is not found in PATH.
        """
        super().__init__(config)
        self.time_limit: float = config.time_limit
        self.skill_level: int = config.skill_level
        self.engine: chess.engine.SimpleEngine | None = None

        # Locate Stockfish binary
        engine_path = shutil.which("stockfish")
        if engine_path is None:
            raise FileNotFoundError(
                "Stockfish binary not found in PATH. "
                "Install with: sudo apt install stockfish (Linux) or brew install stockfish (macOS)"
            )

        # Initialize Stockfish engine
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.engine.configure({"Skill Level": self.skill_level})
        logger.info(
            f"Initialized Stockfish player '{config.name}' with skill level {self.skill_level}"
        )

    def get_move(self, board: chess.Board) -> chess.Move | None:
        """Generate a move using Stockfish engine.

        Args:
            board: Current board state.

        Returns:
            A chess move, or None if it's not this player's turn or an error occurs.
        """
        if board.turn != self.config.color:
            return None

        if self.engine is None:
            logger.error("Engine not initialized")
            return None

        try:
            result = self.engine.play(board, chess.engine.Limit(time=self.time_limit))
            return result.move
        except Exception as e:
            logger.error(f"Stockfish error: {e}")
            return None

    def close(self) -> None:
        """Safely terminate the Stockfish engine."""
        if self.engine is not None:
            try:
                self.engine.quit()
                logger.info(f"Closed Stockfish engine for player '{self.config.name}'")
            except Exception as e:
                logger.warning(f"Error closing Stockfish engine: {e}")
            finally:
                self.engine = None

    def __del__(self) -> None:
        """Destructor to ensure the engine is closed when the player is deleted."""
        self.close()
