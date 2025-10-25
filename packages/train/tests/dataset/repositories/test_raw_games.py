"""Tests for raw_games repository."""

import sqlite3
from unittest.mock import patch

import pytest

from packages.train.src.dataset.models.raw_game import RawGame
from packages.train.src.dataset.repositories import database, raw_games


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    with (
        patch("packages.train.src.dataset.repositories.db_utils.DB_FILE", str(db_path)),
        patch("packages.train.src.dataset.repositories.database.DB_FILE", str(db_path)),
        patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", str(db_path)),
        patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", str(db_path)),
    ):
        database.initialize_database()
        yield str(db_path)


class TestRawGamesTable:
    """Tests for raw_games table operations."""

    def test_create_table(self, temp_db):
        """Test creating the raw_games table."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            raw_games.create_raw_games_table()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='raw_games'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_table_exists(self, temp_db):
        """Test checking if table exists."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            assert raw_games.raw_games_table_exists() is True

    def test_save_raw_game(self, temp_db):
        """Test saving a single raw game."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            game = RawGame(file_id=1, pgn="1. e4 e5", processed=False)
            raw_games.save_raw_game(game)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM raw_games WHERE pgn_hash = ?", (game.pgn_hash,))
            row = cursor.fetchone()
            conn.close()

            assert row is not None
            assert row[2] == "1. e4 e5"  # pgn

    def test_save_raw_game_duplicate(self, temp_db):
        """Test that duplicate PGN hashes are not inserted."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            game1 = RawGame(file_id=1, pgn="1. e4 e5", processed=False)
            game2 = RawGame(file_id=1, pgn="1. e4 e5", processed=False)

            raw_games.save_raw_game(game1)
            raw_games.save_raw_game(game2)  # Should be skipped

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM raw_games")
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 1

    def test_save_multiple_raw_games(self, temp_db):
        """Test saving multiple raw games."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            games = [RawGame(file_id=1, pgn=f"1. e4 e5 {i}", processed=False) for i in range(5)]
            raw_games.save_raw_games(games)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM raw_games")
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 5

    def test_mark_raw_game_as_processed(self, temp_db):
        """Test marking a game as processed."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            game = RawGame(file_id=1, pgn="1. e4 e5", processed=False)
            raw_games.save_raw_game(game)

            # Get the game with ID
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM raw_games WHERE pgn_hash = ?", (game.pgn_hash,))
            game_id = cursor.fetchone()[0]
            conn.close()

            game.id = game_id
            raw_games.mark_raw_game_as_processed(game)

            assert game.processed is True

            # Verify in database
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT processed FROM raw_games WHERE id = ?", (game_id,))
            processed = cursor.fetchone()[0]
            conn.close()

            assert processed == 1

    def test_fetch_raw_games_all(self, temp_db):
        """Test fetching all raw games."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            games = [RawGame(file_id=1, pgn=f"1. e4 e5 {i}", processed=False) for i in range(3)]
            raw_games.save_raw_games(games)

            fetched = raw_games.fetch_raw_games()
            assert len(fetched) == 3
            assert all(isinstance(g, RawGame) for g in fetched)

    def test_fetch_raw_games_by_file_id(self, temp_db):
        """Test fetching raw games filtered by file_id."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            games_file1 = [
                RawGame(file_id=1, pgn=f"1. e4 e5 {i}", processed=False) for i in range(2)
            ]
            games_file2 = [
                RawGame(file_id=2, pgn=f"1. d4 d5 {i}", processed=False) for i in range(3)
            ]
            raw_games.save_raw_games(games_file1 + games_file2)

            fetched = raw_games.fetch_raw_games(file_id=1)
            assert len(fetched) == 2
            assert all(g.file_id == 1 for g in fetched)

    def test_fetch_unprocessed_raw_games(self, temp_db):
        """Test fetching only unprocessed games."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            game1 = RawGame(file_id=1, pgn="1. e4 e5", processed=False)
            game2 = RawGame(file_id=1, pgn="1. d4 d5", processed=False)

            raw_games.save_raw_game(game1)
            raw_games.save_raw_game(game2)

            # Mark one as processed
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE raw_games SET processed = 1 WHERE pgn_hash = ?", (game1.pgn_hash,)
            )
            conn.commit()
            conn.close()

            unprocessed = list(raw_games.fetch_unprocessed_raw_games())
            assert len(unprocessed) == 1
            assert unprocessed[0].pgn == "1. d4 d5"

    def test_raw_game_exists(self, temp_db):
        """Test checking if a game exists by hash."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            game = RawGame(file_id=1, pgn="1. e4 e5", processed=False)
            raw_games.save_raw_game(game)

            assert raw_games.raw_game_exists(game.pgn_hash) is True
            assert raw_games.raw_game_exists("nonexistent_hash") is False

    def test_empty_pgn(self, temp_db):
        """Test saving a game with empty PGN."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            game = RawGame(file_id=1, pgn="", processed=False)
            raw_games.save_raw_game(game)

            fetched = raw_games.fetch_raw_games()
            assert len(fetched) == 1
            assert fetched[0].pgn == ""

    def test_complex_pgn(self, temp_db):
        """Test saving a game with complex PGN."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            pgn = """[Event "Rated Blitz game"]
[Site "https://lichess.org/abcd1234"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0"""
            game = RawGame(file_id=1, pgn=pgn, processed=False)
            raw_games.save_raw_game(game)

            fetched = raw_games.fetch_raw_games()
            assert len(fetched) == 1
            assert fetched[0].pgn == pgn

    def test_fetch_unprocessed_by_file_id(self, temp_db):
        """Test fetching unprocessed games filtered by file_id."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            game1 = RawGame(file_id=1, pgn="1. e4 e5", processed=False)
            game2 = RawGame(file_id=2, pgn="1. d4 d5", processed=False)

            raw_games.save_raw_game(game1)
            raw_games.save_raw_game(game2)

            unprocessed = list(raw_games.fetch_unprocessed_raw_games(file_id=1))
            assert len(unprocessed) == 1
            assert unprocessed[0].file_id == 1

    def test_unicode_in_pgn(self, temp_db):
        """Test saving PGN with unicode characters."""
        with patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", temp_db):
            pgn = "1. e4 e5 # ♔♕♖♗♘♙"
            game = RawGame(file_id=1, pgn=pgn, processed=False)
            raw_games.save_raw_game(game)

            fetched = raw_games.fetch_raw_games()
            assert len(fetched) == 1
            assert fetched[0].pgn == pgn
