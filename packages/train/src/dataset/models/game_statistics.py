from dataclasses import dataclass


@dataclass
class GameStatistics:
    """Statistics extracted from a chess game's PGN headers.

    All fields are optional and will be None if not present in the PGN.
    """

    raw_game_id: int
    id: int | None = None  # DB primary key

    # Standard PGN headers (Seven Tag Roster)
    event: str | None = None
    site: str | None = None
    date: str | None = None
    round: str | None = None
    white: str | None = None
    black: str | None = None
    result: str | None = None

    # Player ratings
    white_elo: int | None = None
    black_elo: int | None = None
    white_rating_diff: int | None = None
    black_rating_diff: int | None = None

    # Time control
    time_control: str | None = None

    # Opening information
    eco: str | None = None
    opening: str | None = None

    # Game termination
    termination: str | None = None

    # Timestamp information
    utc_date: str | None = None
    utc_time: str | None = None

    # Variant
    variant: str | None = None

    # Lichess-specific
    lichess_url: str | None = None

    # Calculated fields
    total_moves: int | None = None
