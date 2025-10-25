"""Constants and configuration values for the dataset module."""

# Default thresholds for data fetching
DEFAULT_SNAPSHOTS_THRESHOLD = 10_000
DEFAULT_MAX_SIZE_GB = 10.0
DEFAULT_PRINT_INTERVAL = 1_000
DEFAULT_MAX_FILES = 5

# ELO rating ranges for filtering
MIN_ELO = 600
MAX_ELO = 1900

# Network settings
CHUNK_SIZE = 16384  # 16 KB for decompression buffer

# Lichess API URLs
LICHESS_BASE_URL = "https://database.lichess.org/standard/"

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
