import chess
import chess.engine
import shutil
from typing import Optional

from src.play.player.player import Player, PlayerConfig


# ================================================================
# StockfishPlayer
# A chess bot that uses the Stockfish engine.
# ================================================================

# ----------------------------
# Setup Instructions:
# ----------------------------
# 1. Install Stockfish:
#    - On Linux (Debian/Ubuntu):
#        sudo apt install stockfish
#    - On macOS using Homebrew:
#        brew install stockfish
#    - On Windows:
#        Download from https://stockfishchess.org/download/ and place the executable in a folder added to PATH.
#
# 2. Install Python dependencies:
#    pip install chess
#
# 3. Integrate with your game framework:
#    - Import StockfishPlayer and pass it to your game loop.
#    - You can adjust `skill_level` (0–20) for difficulty.
#    - You can adjust `time_limit` to control thinking time per move.

class StockfishPlayerConfig(PlayerConfig):
    name: str = "Stockfish"
    color: bool = True  # True for white, False for black
    skill_level: int = 10  # Skill level (0–20)
    time_limit: float = 0.5  # Time per move in seconds


class StockfishPlayer(Player):
    def __init__(self, config: StockfishPlayerConfig) -> None:
        """
        Initialize a Stockfish chess bot using the Stockfish engine.

        Args:
            config: Configuration parameters for the Stockfish bot.
        """
        super().__init__(config)
        self.time_limit = config.time_limit
        self.skill_level = config.skill_level
        self.pending_move: Optional[chess.Move] = None

        # Locate Stockfish binary
        self.engine_path = shutil.which("stockfish")
        if self.engine_path is None:
            raise FileNotFoundError(
                "Stockfish binary not found in PATH. Try installing it with `sudo apt install stockfish`."
            )

        # Initialize Stockfish engine
        self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        self.engine.configure({"Skill Level": self.skill_level})

    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Generate a move using Stockfish engine based on the current board state."""
        # Only make a move if it's this player's turn
        if board.turn != self.config.color:
            return None

        try:
            result = self.engine.play(board, chess.engine.Limit(time=self.time_limit))
            return result.move
        except Exception as e:
            print(f"Stockfish error: {e}")
            return None

    def close(self) -> None:
        """Safely terminate the Stockfish engine."""
        try:
            self.engine.quit()
        except:
            pass  # Engine may already be closed

    def __del__(self) -> None:
        """Destructor to ensure the engine is closed when the player is deleted."""
        self.close()
