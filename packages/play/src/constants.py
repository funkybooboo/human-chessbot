"""Constants and configuration values for the play package."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def _get_bool(key: str, default: bool) -> bool:
    """Get boolean value from environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes")


def _expand_path(path: str) -> str:
    """Expand ~ and environment variables in path."""
    return str(Path(os.path.expanduser(os.path.expandvars(path))).resolve())


# Game configuration
GAME_SAVE_DIR = _expand_path(os.getenv("GAME_SAVE_DIR", "~/chess_games/pgn"))
GAME_TIME_LIMIT = float(os.getenv("GAME_TIME_LIMIT", "600.0"))

# GUI configuration
GUI_WINDOW_WIDTH = int(os.getenv("GUI_WINDOW_WIDTH", "1300"))
GUI_WINDOW_HEIGHT = int(os.getenv("GUI_WINDOW_HEIGHT", "1000"))
GUI_TILE_SIZE = int(os.getenv("GUI_TILE_SIZE", "64"))
GUI_IMAGE_DIR = os.getenv("GUI_IMAGE_DIR", "images")
GUI_BASE_URL = os.getenv(
    "GUI_BASE_URL", "https://images.chesscomfiles.com/chess-themes/pieces/neo/150/"
)

# GUI highlight settings
GUI_HIGHLIGHT_LEGAL_MOVES = _get_bool("GUI_HIGHLIGHT_LEGAL_MOVES", True)
GUI_HIGHLIGHT_LAST_MOVE = _get_bool("GUI_HIGHLIGHT_LAST_MOVE", True)
GUI_HIGHLIGHT_SELECTED = _get_bool("GUI_HIGHLIGHT_SELECTED", True)
GUI_HIGHLIGHT_ILLEGAL_MOVE = _get_bool("GUI_HIGHLIGHT_ILLEGAL_MOVE", True)
GUI_HIGHLIGHT_CAPTURE_SQUARE = _get_bool("GUI_HIGHLIGHT_CAPTURE_SQUARE", True)

# Board colors
COLOR_BOARD_LIGHT = os.getenv("COLOR_BOARD_LIGHT", "#F0D9B5")
COLOR_BOARD_DARK = os.getenv("COLOR_BOARD_DARK", "#B58863")
COLOR_HIGHLIGHT_LEGAL = os.getenv("COLOR_HIGHLIGHT_LEGAL", "#A9D18E")
COLOR_HIGHLIGHT_ILLEGAL = os.getenv("COLOR_HIGHLIGHT_ILLEGAL", "#FF6666")
COLOR_HIGHLIGHT_LAST_MOVE = os.getenv("COLOR_HIGHLIGHT_LAST_MOVE", "#FBFFB8")
COLOR_HIGHLIGHT_SELECTED = os.getenv("COLOR_HIGHLIGHT_SELECTED", "#FFFF00")
COLOR_HIGHLIGHT_CAPTURE_SQUARE = os.getenv("COLOR_HIGHLIGHT_CAPTURE_SQUARE", "#FFD700")

# Player configuration
STOCKFISH_SKILL_LEVEL = int(os.getenv("STOCKFISH_SKILL_LEVEL", "10"))
STOCKFISH_TIME_LIMIT = float(os.getenv("STOCKFISH_TIME_LIMIT", "0.5"))
LC0_TIME_LIMIT = float(os.getenv("LC0_TIME_LIMIT", "1.0"))

# CLI configuration
CLI_LOOP_INTERVAL = float(os.getenv("CLI_LOOP_INTERVAL", "0.1"))
