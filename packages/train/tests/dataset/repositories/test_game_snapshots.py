"""Tests for game_snapshots repository."""

import sqlite3
from unittest.mock import patch

import pytest

from packages.train.src.dataset.models.game_snapshot import GameSnapshot
from packages.train.src.dataset.repositories import database, game_snapshots


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    with (
        patch("packages.train.src.dataset.repositories.db_utils.DB_FILE", str(db_path)),
        patch("packages.train.src.dataset.repositories.database.DB_FILE", str(db_path)),
        patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", str(db_path)),
        patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", str(db_path)),
        patch("packages.train.src.dataset.repositories.raw_games.DB_FILE", str(db_path)),
    ):
        database.initialize_database()
        yield str(db_path)


class TestGameSnapshotsTable:
    """Tests for game_snapshots table operations."""

    def test_create_table(self, temp_db):
        """Test creating the game_snapshots table."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            game_snapshots.create_game_snapshots_table()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='game_snapshots'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_table_has_fen_column(self, temp_db):
        """Test that table has fen column instead of 64 square columns."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(game_snapshots)")
        columns = cursor.fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        assert "fen" in column_names
        # Ensure we don't have old square_ columns
        square_columns = [col for col in column_names if col.startswith("square_")]
        assert len(square_columns) == 0

    def test_table_exists(self, temp_db):
        """Test checking if table exists."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            assert game_snapshots.game_snapshots_table_exists() is True

    def test_save_snapshot(self, temp_db):
        """Test saving a single snapshot."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                fen=fen,
                board_hash="hash1",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )
            game_snapshots.save_snapshot(snapshot)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM game_snapshots WHERE board_hash = ?", ("hash1",))
            row = cursor.fetchone()
            conn.close()

            assert row is not None
            assert row[4] == "e4"  # move
            assert row[5] == fen  # fen

    def test_save_snapshot_duplicate(self, temp_db):
        """Test that duplicate board hashes are not inserted."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            snapshot1 = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                fen=fen,
                board_hash="hash1",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )
            snapshot2 = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                fen=fen,
                board_hash="hash1",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )

            game_snapshots.save_snapshot(snapshot1)
            game_snapshots.save_snapshot(snapshot2)  # Should be skipped

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM game_snapshots")
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 1

    def test_save_multiple_snapshots(self, temp_db):
        """Test saving multiple snapshots."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            snapshots = [
                GameSnapshot(
                    raw_game_id=1,
                    move_number=i,
                    turn="w",
                    move=f"move{i}",
                    fen=fen,
                    board_hash=f"hash{i}",
                    white_elo=1500,
                    black_elo=1500,
                    result="1-0",
                )
                for i in range(5)
            ]
            game_snapshots.save_snapshots(snapshots)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM game_snapshots")
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 5

    def test_count_snapshots(self, temp_db):
        """Test counting snapshots in the database."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            snapshots = [
                GameSnapshot(
                    raw_game_id=1,
                    move_number=i,
                    turn="w",
                    move=f"move{i}",
                    fen=fen,
                    board_hash=f"hash{i}",
                    white_elo=1500,
                    black_elo=1500,
                    result="1-0",
                )
                for i in range(10)
            ]
            game_snapshots.save_snapshots(snapshots)

            count = game_snapshots.count_snapshots()
            assert count == 10

    def test_count_snapshots_empty(self, temp_db):
        """Test counting snapshots when table is empty."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            count = game_snapshots.count_snapshots()
            assert count == 0

    def test_save_snapshot_different_fen_positions(self, temp_db):
        """Test saving snapshots with different FEN positions."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            # Starting position after 1. e4
            fen1 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            # After 1. e4 e5
            fen2 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"

            snapshot1 = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                fen=fen1,
                board_hash="hash1",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )
            snapshot2 = GameSnapshot(
                raw_game_id=1,
                move_number=2,
                turn="b",
                move="e5",
                fen=fen2,
                board_hash="hash2",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )

            game_snapshots.save_snapshot(snapshot1)
            game_snapshots.save_snapshot(snapshot2)

            # Verify FENs were saved correctly
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT fen FROM game_snapshots WHERE board_hash = ?", ("hash1",))
            saved_fen1 = cursor.fetchone()[0]
            cursor.execute("SELECT fen FROM game_snapshots WHERE board_hash = ?", ("hash2",))
            saved_fen2 = cursor.fetchone()[0]
            conn.close()

            assert saved_fen1 == fen1
            assert saved_fen2 == fen2

    def test_save_snapshot_with_none_elo(self, temp_db):
        """Test saving a snapshot with None ELO values."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                fen=fen,
                board_hash="hash1",
                white_elo=None,
                black_elo=None,
                result="1-0",
            )
            game_snapshots.save_snapshot(snapshot)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT white_elo, black_elo FROM game_snapshots WHERE board_hash = ?", ("hash1",)
            )
            row = cursor.fetchone()
            conn.close()

            assert row[0] is None
            assert row[1] is None

    def test_save_snapshot_different_results(self, temp_db):
        """Test saving snapshots with different game results."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            results = ["1-0", "0-1", "1/2-1/2", "*"]

            for i, result in enumerate(results):
                snapshot = GameSnapshot(
                    raw_game_id=1,
                    move_number=i,
                    turn="w",
                    move=f"move{i}",
                    fen=fen,
                    board_hash=f"hash{i}",
                    white_elo=1500,
                    black_elo=1500,
                    result=result,
                )
                game_snapshots.save_snapshot(snapshot)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT result FROM game_snapshots ORDER BY move_number")
            rows = cursor.fetchall()
            conn.close()

            assert [row[0] for row in rows] == results

    def test_save_snapshot_high_move_number(self, temp_db):
        """Test saving a snapshot with high move number."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            fen = "8/6k1/8/8/8/8/6K1/8 w - - 0 75"
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=150,
                turn="w",
                move="Kg3",
                fen=fen,
                board_hash="hash1",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )
            game_snapshots.save_snapshot(snapshot)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT move_number FROM game_snapshots WHERE board_hash = ?", ("hash1",)
            )
            move_num = cursor.fetchone()[0]
            conn.close()

            assert move_num == 150

    def test_save_snapshot_complex_move(self, temp_db):
        """Test saving snapshots with complex move notation."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            moves = ["e4", "Nf3", "O-O", "Qxd8+", "Rxd8#"]

            for i, move in enumerate(moves):
                snapshot = GameSnapshot(
                    raw_game_id=1,
                    move_number=i,
                    turn="w",
                    move=move,
                    fen=fen,
                    board_hash=f"hash{i}",
                    white_elo=1500,
                    black_elo=1500,
                    result="1-0",
                )
                game_snapshots.save_snapshot(snapshot)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT move FROM game_snapshots ORDER BY move_number")
            rows = cursor.fetchall()
            conn.close()

            assert [row[0] for row in rows] == moves
