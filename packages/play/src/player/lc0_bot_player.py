"""LCZero (Leela Chess Zero) chess engine player implementation."""

import shutil

import chess
import chess.engine

from packages.play.src.constants import LC0_TIME_LIMIT
from packages.play.src.player.player import Player, PlayerConfig


class Lc0BotPlayerConfig(PlayerConfig):
    """Configuration for LCZero chess bot.

    Attributes:
        name: Player name
        color: True for white, False for black
        time_limit: Time per move in seconds
        wins: Number of wins (tracked automatically)
        losses: Number of losses (tracked automatically)
    """

    name: str = "Lc0"
    color: bool = True
    time_limit: float = LC0_TIME_LIMIT


class Lc0BotPlayer(Player):
    """Chess bot powered by the LCZero engine.

    Setup Instructions:
        1. Download lc0 binary from https://lczero.org/play/download/
        2. Make it executable and add to PATH:
           chmod +x lc0 && mv lc0 ~/bin/
        3. Download a neural network from https://lczero.org/play/networks/
        4. Place network in ~/.local/share/lc0/networks/
           mkdir -p ~/.local/share/lc0/networks
           cp latest.pb.gz ~/.local/share/lc0/networks/
    """

    def __init__(self, config: Lc0BotPlayerConfig) -> None:
        """Initialize LCZero player.

        Args:
            config: Configuration parameters for the LCZero bot.

        Raises:
            FileNotFoundError: If lc0 binary is not found in PATH.
        """
        super().__init__(config)
        self.time_limit: float = config.time_limit
        self.engine: chess.engine.SimpleEngine | None = None

        # Locate lc0 binary
        engine_path = shutil.which("lc0")
        if engine_path is None:
            raise FileNotFoundError(
                "lc0 executable not found in PATH. "
                "Download from https://lczero.org/play/download/ and add to PATH."
            )

        # Start LCZero engine
        self.engine = chess.engine.SimpleEngine.popen_uci([engine_path])
        print(f"Initialized LCZero player '{config.name}'")

    def get_move(self, board: chess.Board) -> chess.Move | None:
        """Generate a move using LCZero engine.

        Args:
            board: Current board state.

        Returns:
            A chess move, or None if it's not this player's turn or an error occurs.
        """
        if board.turn != self.config.color:
            return None

        if self.engine is None:
            print("ERROR: Engine not initialized")
            return None

        try:
            result = self.engine.play(board, chess.engine.Limit(time=self.time_limit))
            return result.move
        except Exception as e:
            print(f"ERROR: LCZero error: {e}")
            return None

    def close(self) -> None:
        """Safely terminate the LCZero engine."""
        if self.engine is not None:
            try:
                self.engine.quit()
                print(f"Closed LCZero engine for player '{self.config.name}'")
            except Exception as e:
                print(f"WARNING: Error closing LCZero engine: {e}")
            finally:
                self.engine = None

    def __del__(self) -> None:
        """Destructor to ensure the engine is closed when the player is deleted."""
        self.close()
