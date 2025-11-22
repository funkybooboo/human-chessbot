"""Tests for GameSnapshot model."""

from packages.train.src.dataset.models.game_snapshot import GameSnapshot


class TestGameSnapshot:
    """Tests for GameSnapshot dataclass."""

    def test_creation_with_all_fields(self):
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

    def test_black_turn(self):
        """Test GameSnapshot with black's turn."""
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=2,
            turn="b",
            move="e5",
            fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
        )
        assert snapshot.turn == "b"
        assert snapshot.move_number == 2

    def test_various_move_notations(self):
        """Test GameSnapshot accepts various SAN notations."""
        moves = ["e4", "Nf3", "Bb5", "O-O", "Qe2+", "Rxd8#", "exd5", "e8=Q"]
        for move in moves:
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move=move,
                fen="8/8/8/8/8/8/8/8 w - - 0 1",
            )
            assert snapshot.move == move
