"""Tests for game statistics extraction and storage."""

import pytest

from packages.train.src.dataset.models.game_statistics import GameStatistics
from packages.train.src.dataset.models.raw_game import RawGame
from packages.train.src.dataset.processers.game_statistics import extract_statistics_from_raw_game
from packages.train.src.dataset.repositories.game_statistics import (
    count_game_statistics,
    create_game_statistics_table,
    fetch_game_statistics_by_raw_game_id,
    save_game_statistics,
    save_game_statistics_batch,
)


@pytest.fixture
def sample_pgn():
    """Sample PGN game data from Lichess."""
    return """[Event "Rated Blitz game"]
[Site "https://lichess.org/abc123"]
[Date "2024.01.15"]
[Round "?"]
[White "PlayerOne"]
[Black "PlayerTwo"]
[Result "1-0"]
[WhiteElo "1500"]
[BlackElo "1450"]
[WhiteRatingDiff "+8"]
[BlackRatingDiff "-7"]
[TimeControl "180+2"]
[ECO "C50"]
[Opening "Italian Game"]
[Termination "Normal"]
[UTCDate "2024.01.15"]
[UTCTime "14:30:45"]
[Variant "Standard"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6 5. d3 d6 1-0"""


@pytest.fixture
def sample_raw_game(sample_pgn):
    """Create a RawGame object with sample PGN."""
    return RawGame(id=1, file_id=1, pgn=sample_pgn, processed=False)


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Create a temporary database for testing using tmp_path and monkeypatch."""
    db_path = tmp_path / "test.db"
    import packages.train.src.dataset.repositories.game_statistics as stats_repo

    monkeypatch.setattr(stats_repo, "DB_FILE", str(db_path))
    create_game_statistics_table()
    yield str(db_path)


def test_extract_statistics_from_raw_game(sample_raw_game):
    """Test extracting statistics from a raw game."""
    stats = extract_statistics_from_raw_game(sample_raw_game)

    assert stats is not None
    assert stats.raw_game_id == 1
    assert stats.event == "Rated Blitz game"
    assert stats.site == "https://lichess.org/abc123"
    assert stats.date == "2024.01.15"
    assert stats.white == "PlayerOne"
    assert stats.black == "PlayerTwo"
    assert stats.result == "1-0"
    assert stats.white_elo == 1500
    assert stats.black_elo == 1450
    assert stats.white_rating_diff == 8
    assert stats.black_rating_diff == -7
    assert stats.time_control == "180+2"
    assert stats.eco == "C50"
    assert stats.opening == "Italian Game"
    assert stats.termination == "Normal"
    assert stats.utc_date == "2024.01.15"
    assert stats.utc_time == "14:30:45"
    assert stats.variant == "Standard"
    assert stats.lichess_url == "https://lichess.org/abc123"
    assert stats.total_moves == 10  # 5 moves for each side


def test_extract_statistics_handles_missing_fields():
    """Test that extraction handles missing PGN headers gracefully."""
    minimal_pgn = """[Event "Test"]
[Site "?"]
[Date "????.??.??"]
[Round "?"]
[White "?"]
[Black "?"]
[Result "*"]

1. e4 e5 *"""

    raw_game = RawGame(id=2, file_id=1, pgn=minimal_pgn)
    stats = extract_statistics_from_raw_game(raw_game)

    assert stats is not None
    assert stats.event == "Test"
    assert stats.white_elo is None
    assert stats.black_elo is None
    assert stats.eco is None
    assert stats.opening is None
    assert stats.total_moves == 2


def test_save_game_statistics(temp_db, sample_raw_game):  # noqa: ARG001
    """Test saving a single game statistics record."""
    stats = extract_statistics_from_raw_game(sample_raw_game)
    assert stats is not None
    save_game_statistics(stats)

    # Verify it was saved
    assert stats.id is not None
    assert count_game_statistics() == 1

    # Fetch it back
    fetched = fetch_game_statistics_by_raw_game_id(1)
    assert fetched is not None
    assert fetched.white == "PlayerOne"
    assert fetched.black == "PlayerTwo"
    assert fetched.white_elo == 1500


def test_save_game_statistics_batch(temp_db):  # noqa: ARG001
    """Test batch saving of game statistics."""
    stats_list = [
        GameStatistics(
            raw_game_id=i,
            event=f"Game {i}",
            white="White",
            black="Black",
            result="1-0",
            total_moves=20,
        )
        for i in range(1, 6)
    ]

    save_game_statistics_batch(stats_list)

    assert count_game_statistics() == 5


def test_save_duplicate_statistics(temp_db, sample_raw_game):  # noqa: ARG001
    """Test that duplicate statistics are ignored."""
    stats = extract_statistics_from_raw_game(sample_raw_game)
    assert stats is not None

    save_game_statistics(stats)
    initial_count = count_game_statistics()

    # Try to save again - should be ignored
    save_game_statistics(stats)

    assert count_game_statistics() == initial_count


def test_invalid_pgn_returns_none():
    """Test that completely empty/invalid PGN returns None."""
    # Empty string causes chess.pgn.read_game to return None
    invalid_pgn = ""
    raw_game = RawGame(id=99, file_id=1, pgn=invalid_pgn)

    stats = extract_statistics_from_raw_game(raw_game)
    assert stats is None


def test_raw_game_without_id_returns_none():
    """Test that raw game without ID returns None."""
    raw_game = RawGame(id=None, file_id=1, pgn='[Event "Test"]\n\n1. e4 e5 *')

    stats = extract_statistics_from_raw_game(raw_game)
    assert stats is None
