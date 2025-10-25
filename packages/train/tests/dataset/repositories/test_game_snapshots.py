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
        patch("packages.train.src.dataset.repositories.config.DB_FILE", str(db_path)),
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

    def test_table_has_64_square_columns(self, temp_db):
        """Test that table has all 64 square columns."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(game_snapshots)")
        columns = cursor.fetchall()
        conn.close()

        square_columns = [col for col in columns if col[1].startswith("square_")]
        assert len(square_columns) == 64

    def test_table_exists(self, temp_db):
        """Test checking if table exists."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            assert game_snapshots.game_snapshots_table_exists() is True

    def test_save_snapshot(self, temp_db):
        """Test saving a single snapshot."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            board = [0] * 64
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                board=board,
                board_hash="hash1",
                white_player="P1",
                black_player="P2",
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

    def test_save_snapshot_duplicate(self, temp_db):
        """Test that duplicate board hashes are not inserted."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            board = [0] * 64
            snapshot1 = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                board=board,
                board_hash="hash1",
                white_player="P1",
                black_player="P2",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )
            snapshot2 = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                board=board,
                board_hash="hash1",
                white_player="P1",
                black_player="P2",
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
            board = [0] * 64
            snapshots = [
                GameSnapshot(
                    raw_game_id=1,
                    move_number=i,
                    turn="w",
                    move=f"move{i}",
                    board=board,
                    board_hash=f"hash{i}",
                    white_player="P1",
                    black_player="P2",
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
            board = [0] * 64
            snapshots = [
                GameSnapshot(
                    raw_game_id=1,
                    move_number=i,
                    turn="w",
                    move=f"move{i}",
                    board=board,
                    board_hash=f"hash{i}",
                    white_player="P1",
                    black_player="P2",
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

    def test_save_snapshot_with_pieces(self, temp_db):
        """Test saving a snapshot with actual piece positions."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            # Starting position
            board = [4, 2, 3, 5, 6, 3, 2, 4] + [1] * 8 + [0] * 48
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                board=board,
                board_hash="hash1",
                white_player="P1",
                black_player="P2",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )
            game_snapshots.save_snapshot(snapshot)

            # Verify board was saved correctly
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT square_0, square_1, square_8 FROM game_snapshots WHERE board_hash = ?",
                ("hash1",),
            )
            row = cursor.fetchone()
            conn.close()

            assert row[0] == 4  # Rook
            assert row[1] == 2  # Knight
            assert row[2] == 1  # Pawn

    def test_save_snapshot_with_negative_pieces(self, temp_db):
        """Test saving a snapshot with black pieces (negative values)."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            board = [-4, -2, -3, -5, -6, -3, -2, -4] + [-1] * 8 + [0] * 48
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="b",
                move="e5",
                board=board,
                board_hash="hash1",
                white_player="P1",
                black_player="P2",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )
            game_snapshots.save_snapshot(snapshot)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT square_0, square_4 FROM game_snapshots WHERE board_hash = ?", ("hash1",)
            )
            row = cursor.fetchone()
            conn.close()

            assert row[0] == -4  # Black rook
            assert row[1] == -6  # Black king

    def test_save_snapshot_with_none_elo(self, temp_db):
        """Test saving a snapshot with None ELO values."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            board = [0] * 64
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                board=board,
                board_hash="hash1",
                white_player="P1",
                black_player="P2",
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
            board = [0] * 64
            results = ["1-0", "0-1", "1/2-1/2", "*"]

            for i, result in enumerate(results):
                snapshot = GameSnapshot(
                    raw_game_id=1,
                    move_number=i,
                    turn="w",
                    move=f"move{i}",
                    board=board,
                    board_hash=f"hash{i}",
                    white_player="P1",
                    black_player="P2",
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
            board = [0] * 64
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=150,
                turn="w",
                move="Kg3",
                board=board,
                board_hash="hash1",
                white_player="P1",
                black_player="P2",
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
            board = [0] * 64
            moves = ["e4", "Nf3", "O-O", "Qxd8+", "Rxd8#"]

            for i, move in enumerate(moves):
                snapshot = GameSnapshot(
                    raw_game_id=1,
                    move_number=i,
                    turn="w",
                    move=move,
                    board=board,
                    board_hash=f"hash{i}",
                    white_player="P1",
                    black_player="P2",
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

    def test_save_snapshot_unicode_player_names(self, temp_db):
        """Test saving snapshots with unicode in player names."""
        with patch("packages.train.src.dataset.repositories.game_snapshots.DB_FILE", temp_db):
            board = [0] * 64
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                board=board,
                board_hash="hash1",
                white_player="Иван",
                black_player="José",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )
            game_snapshots.save_snapshot(snapshot)

            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT white_player, black_player FROM game_snapshots WHERE board_hash = ?",
                ("hash1",),
            )
            row = cursor.fetchone()
            conn.close()

            assert row[0] == "Иван"
            assert row[1] == "José"
