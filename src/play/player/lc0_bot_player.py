import shutil
import chess
import chess.engine
from typing import Optional

from src.play.player.player import Player, PlayerConfig


# ================================================================
# Lc0BotPlayer
# A chess bot that uses the LCZero engine (https://lczero.org).
# ================================================================

# ----------------------------
# Setup Instructions:
# ----------------------------
# 1. Install LCZero:
#    - Download the lc0 binary for your platform from https://lczero.org/play/download/.
#    - Ensure the binary is executable and available in your PATH.
#      Example (Linux/macOS):
#        chmod +x lc0
#        mv lc0 ~/bin/    # Add ~/bin to your PATH if not already
#
# 2. Download a neural network:
#    - LCZero requires a neural network file to play.
#    - Place your network file(s) in:
#        ~/.local/share/lc0/networks/
#      Example:
#        mkdir -p ~/.local/share/lc0/networks
#        cp latest.pb.gz ~/.local/share/lc0/networks/
#    - You can download networks from https://lczero.org/play/networks/
#
# 3. Install Python dependencies:
#    pip install chess
#
# 4. Integrate with your code:
#    - Import Lc0BotPlayer and pass it to your game framework.
#    - Optionally, set time_limit to control thinking time per move.


class Lc0BotPlayerConfig(PlayerConfig):
    name: str = "Lc0"
    color: bool = True  # True for white, False for black
    time_limit: float = 1.0  # Time per move in seconds


class Lc0BotPlayer(Player):
    def __init__(self, config: Lc0BotPlayerConfig) -> None:
        """
        Initialize the LCZero chess bot using the LCZero engine.

        Args:
            config: Configuration parameters for the LCZero bot.
        """
        super().__init__(config)
        self.time_limit = config.time_limit
        self.pending_move: Optional[chess.Move] = None

        # Locate lc0 binary
        self.engine_path = shutil.which("lc0")
        if not self.engine_path:
            raise FileNotFoundError(
                "lc0 executable not found in PATH. Make sure lc0 is installed and added to PATH."
            )

        # Start LCZero engine
        self.engine = chess.engine.SimpleEngine.popen_uci([self.engine_path])

    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Generate a move using LCZero engine based on the current board state."""
        # Only make a move if it's this player's turn
        if board.turn != self.config.color:
            return None
        try:
            result = self.engine.play(board, chess.engine.Limit(time=self.time_limit))
            return result.move
        except Exception as e:
            print("Lc0 error:", e)
            return None

    def close(self) -> None:
        """Safely terminate the LCZero engine."""
        try:
            self.engine.quit()
        except:
            pass

    def __del__(self) -> None:
        """Destructor to ensure the engine is closed when the player is deleted."""
        self.close()
