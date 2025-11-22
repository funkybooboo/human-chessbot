"""Tests for legal_move repository."""

import sqlite3
from unittest.mock import patch

import pytest

from packages.train.src.dataset.models.legal_move import LegalMove
from packages.train.src.dataset.repositories import legal_move


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    with patch("packages.train.src.dataset.repositories.legal_move.DB_FILE", str(db_path)):
        legal_move.create_legal_moves_table()
        yield str(db_path)


class TestLegalMovesRepository:
    """Tests for legal_move repository functions."""

    def test_create_table(self, temp_db):
        """Test that create_legal_moves_table creates the table."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='legal_moves'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None

    def test_save_and_count_legal_move(self, temp_db):
        """Test saving a legal move and counting."""
        with patch("packages.train.src.dataset.repositories.legal_move.DB_FILE", temp_db):
            move = LegalMove(move="e2e4", types=["P"])
            legal_move.save_legal_move(move)
            count = legal_move.count_legal_moves()
        assert count == 1

    def test_save_duplicate_move_ignored(self, temp_db):
        """Test that duplicate moves are ignored."""
        with patch("packages.train.src.dataset.repositories.legal_move.DB_FILE", temp_db):
            move = LegalMove(move="e2e4", types=["P"])
            legal_move.save_legal_move(move)
            legal_move.save_legal_move(move)
            count = legal_move.count_legal_moves()
        assert count == 1

    def test_save_multiple_legal_moves(self, temp_db):
        """Test saving multiple legal moves at once."""
        with patch("packages.train.src.dataset.repositories.legal_move.DB_FILE", temp_db):
            moves = [
                LegalMove(move="e2e4", types=["P"]),
                LegalMove(move="d2d4", types=["P"]),
                LegalMove(move="g1f3", types=["N"]),
            ]
            legal_move.save_legal_moves(moves)
            count = legal_move.count_legal_moves()
        assert count == 3

    def test_save_moves_with_multiple_piece_types(self, temp_db):
        """Test saving move that can be made by multiple piece types."""
        with patch("packages.train.src.dataset.repositories.legal_move.DB_FILE", temp_db):
            move = LegalMove(move="e4e5", types=["P", "Q", "R"])
            legal_move.save_legal_move(move)

            moves = legal_move.get_all_legal_moves()
            assert len(moves) == 1
            assert moves[0].types == ["P", "Q", "R"]

    def test_get_all_legal_moves_empty(self, temp_db):
        """Test getting moves from empty table."""
        with patch("packages.train.src.dataset.repositories.legal_move.DB_FILE", temp_db):
            moves = legal_move.get_all_legal_moves()
        assert moves == []

    def test_get_all_legal_moves(self, temp_db):
        """Test getting all legal moves."""
        with patch("packages.train.src.dataset.repositories.legal_move.DB_FILE", temp_db):
            legal_move.save_legal_moves(
                [
                    LegalMove(move="e2e4", types=["P"]),
                    LegalMove(move="d2d4", types=["P"]),
                ]
            )
            moves = legal_move.get_all_legal_moves()

        assert len(moves) == 2
        move_strs = {m.move for m in moves}
        assert move_strs == {"e2e4", "d2d4"}

    def test_count_legal_moves_empty(self, temp_db):
        """Test counting moves in empty table."""
        with patch("packages.train.src.dataset.repositories.legal_move.DB_FILE", temp_db):
            count = legal_move.count_legal_moves()
        assert count == 0
