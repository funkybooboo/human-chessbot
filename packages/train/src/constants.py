"""Constants and configuration values for the train package."""

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


# Database configuration
DB_FILE = os.getenv("DB_FILE", "database.sqlite3")
if not os.path.isabs(DB_FILE):
    DB_FILE = str(Path(__file__).parent.parent / DB_FILE)

# Default thresholds for data fetching
DEFAULT_SNAPSHOTS_THRESHOLD = int(os.getenv("DEFAULT_SNAPSHOTS_THRESHOLD", "10000"))
DEFAULT_MAX_SIZE_GB = float(os.getenv("DEFAULT_MAX_SIZE_GB", "10.0"))
DEFAULT_PRINT_INTERVAL = int(os.getenv("DEFAULT_PRINT_INTERVAL", "1000"))
DEFAULT_MAX_FILES = int(os.getenv("DEFAULT_MAX_FILES", "5"))
DEFAULT_BATCH_SIZE = int(os.getenv("DEFAULT_BATCH_SIZE", "1000"))  # Batch size for database writes

# ELO rating ranges for filtering
MIN_ELO = int(os.getenv("MIN_ELO", "600"))
MAX_ELO = int(os.getenv("MAX_ELO", "1900"))

# Network settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "16384"))  # 16 KB for decompression buffer

# Lichess API URLs
LICHESS_BASE_URL = os.getenv("LICHESS_BASE_URL", "https://database.lichess.org/standard/")

# Piece integer mappings (for board representation)
PIECE_TO_INT = {
    "P": 1,
    "N": 2,
    "B": 3,
    "R": 4,
    "Q": 5,
    "K": 6,  # white pieces
    "p": -1,
    "n": -2,
    "b": -3,
    "r": -4,
    "q": -5,
    "k": -6,  # black pieces
    None: 0,  # empty square
}

# Board representation
BOARD_SIZE = 64

# Model Saving Data
FINAL_SAVES_DIR = os.getenv("FINAL_SAVES_DIR", "trained_models")
CHECK_POINT_DIR = os.getenv("CHECK_POINT_DIR", "check_points")
CHECK_POINT_INFO_FILE_NAME = os.getenv("CHECK_POINT_INFO_FILE_NAME", "saves.csv")
EPOCH_INFO_FILE_NAME = os.getenv("EPOCH_INFO_FILE_NAME", "epochs.csv")
