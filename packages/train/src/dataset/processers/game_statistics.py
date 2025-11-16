from collections.abc import Iterator
from io import StringIO

import chess.pgn

from packages.train.src.dataset.models.game_statistics import GameStatistics
from packages.train.src.dataset.models.raw_game import RawGame


def extract_statistics_from_raw_game(raw_game: RawGame) -> GameStatistics | None:
    """Extract statistics from a RawGame's PGN string.

    Args:
        raw_game: RawGame object containing PGN string

    Returns:
        GameStatistics object with extracted data, or None if parsing fails
    """
    if not raw_game.id:
        return None

    pgn_io = StringIO(raw_game.pgn)
    game = chess.pgn.read_game(pgn_io)

    if game is None:
        print(f"Warning: Failed to parse PGN for raw_game_id={raw_game.id}")
        return None

    headers = game.headers

    # Helper to safely get integer values
    def safe_int(val: str | None) -> int | None:
        if val is None:
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    # Count total moves
    total_moves = 0
    for _ in game.mainline_moves():
        total_moves += 1

    # Extract all available headers
    stats = GameStatistics(
        raw_game_id=raw_game.id,
        # Standard Seven Tag Roster
        event=headers.get("Event"),
        site=headers.get("Site"),
        date=headers.get("Date"),
        round=headers.get("Round"),
        white=headers.get("White"),
        black=headers.get("Black"),
        result=headers.get("Result"),
        # Player ratings
        white_elo=safe_int(headers.get("WhiteElo")),
        black_elo=safe_int(headers.get("BlackElo")),
        white_rating_diff=safe_int(headers.get("WhiteRatingDiff")),
        black_rating_diff=safe_int(headers.get("BlackRatingDiff")),
        # Time control
        time_control=headers.get("TimeControl"),
        # Opening
        eco=headers.get("ECO"),
        opening=headers.get("Opening"),
        # Termination
        termination=headers.get("Termination"),
        # Timestamps
        utc_date=headers.get("UTCDate"),
        utc_time=headers.get("UTCTime"),
        # Variant
        variant=headers.get("Variant"),
        # Lichess URL (may be in Site field)
        lichess_url=(
            headers.get("Site")
            if headers.get("Site") and "lichess.org" in headers.get("Site")
            else None
        ),
        # Calculated
        total_moves=total_moves if total_moves > 0 else None,
    )

    return stats


def extract_statistics_from_raw_games(raw_games: Iterator[RawGame]) -> Iterator[GameStatistics]:
    """Extract statistics from multiple raw games.

    Args:
        raw_games: Iterator of RawGame objects

    Yields:
        GameStatistics objects (skips games that fail to parse)
    """
    for raw_game in raw_games:
        stats = extract_statistics_from_raw_game(raw_game)
        if stats:
            yield stats
