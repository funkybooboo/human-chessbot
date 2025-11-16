"""Tests for GameSnapshot model.

Note: white_elo, black_elo, and result are now stored in the GameStatistics table.
These tests focus on the core GameSnapshot fields: raw_game_id, move_number, turn, move, and fen.
"""

from packages.train.src.dataset.models.game_snapshot import GameSnapshot


class TestGameSnapshot:
    """Tests for GameSnapshot dataclass."""

    def test_creation_minimal(self):
        """Test creating GameSnapshot with all required fields."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
        )
        assert snapshot.raw_game_id == 1
        assert snapshot.move_number == 1
        assert snapshot.turn == "w"
        assert snapshot.move == "e4"
        assert snapshot.fen == fen

    def test_fen_string(self):
        """Test creating GameSnapshot with different FEN positions."""
        # After 1. e4
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
        )
        assert snapshot.fen == fen
        assert "rnbqkbnr" in snapshot.fen

    def test_equality(self):
        """Test GameSnapshot equality comparison."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        s1 = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
        )
        s2 = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
        )
        assert s1 == s2

    def test_inequality_different_move(self):
        """Test GameSnapshot inequality with different moves."""
        fen1 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        fen2 = "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1"
        s1 = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen1,
        )
        s2 = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="d4",
            fen=fen2,
        )
        assert s1 != s2

    def test_black_turn(self):
        """Test GameSnapshot with black's turn."""
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=2,
            turn="b",
            move="e5",
            fen=fen,
        )
        assert snapshot.turn == "b"
        assert snapshot.move_number == 2

    def test_late_game_move(self):
        """Test GameSnapshot with high move number."""
        fen = "8/6k1/8/8/8/8/6K1/8 w - - 0 75"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=75,
            turn="w",
            move="Kg3",
            fen=fen,
        )
        assert snapshot.move_number == 75

    def test_complex_move_notation(self):
        """Test GameSnapshot with complex SAN notation."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        moves = ["e4", "Nf3", "Bb5", "O-O", "Qe2+", "Rxd8#", "exd5"]

        for move in moves:
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move=move,
                fen=fen,
            )
            assert snapshot.move == move

    def test_repr(self):
        """Test string representation of GameSnapshot."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
        )
        repr_str = repr(snapshot)
        assert "GameSnapshot" in repr_str
