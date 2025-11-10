"""Tests for GameSnapshot model."""

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
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        assert snapshot.raw_game_id == 1
        assert snapshot.move_number == 1
        assert snapshot.turn == "w"
        assert snapshot.move == "e4"
        assert snapshot.fen == fen
        assert snapshot.white_elo == 1500
        assert snapshot.black_elo == 1500
        assert snapshot.result == "1-0"

    def test_creation_with_none_elo(self):
        """Test creating GameSnapshot with None ELO values."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
            white_elo=None,
            black_elo=None,
            result="1-0",
        )
        assert snapshot.white_elo is None
        assert snapshot.black_elo is None

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
            white_elo=1500,
            black_elo=1500,
            result="1-0",
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
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        s2 = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
            white_elo=1500,
            black_elo=1500,
            result="1-0",
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
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        s2 = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="d4",
            fen=fen2,
            white_elo=1500,
            black_elo=1500,
            result="1-0",
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
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        assert snapshot.turn == "b"
        assert snapshot.move_number == 2

    def test_different_results(self):
        """Test GameSnapshot with different game results."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        results = ["1-0", "0-1", "1/2-1/2", "*"]

        for result in results:
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move="e4",
                fen=fen,
                white_elo=1500,
                black_elo=1500,
                result=result,
            )
            assert snapshot.result == result

    def test_high_elo_ratings(self):
        """Test GameSnapshot with high ELO ratings."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
            white_elo=2800,
            black_elo=2750,
            result="1-0",
        )
        assert snapshot.white_elo == 2800
        assert snapshot.black_elo == 2750

    def test_low_elo_ratings(self):
        """Test GameSnapshot with low ELO ratings."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
            white_elo=400,
            black_elo=500,
            result="1-0",
        )
        assert snapshot.white_elo == 400
        assert snapshot.black_elo == 500

    def test_late_game_move(self):
        """Test GameSnapshot with high move number."""
        fen = "8/6k1/8/8/8/8/6K1/8 w - - 0 75"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=75,
            turn="w",
            move="Kg3",
            fen=fen,
            white_elo=1500,
            black_elo=1500,
            result="1-0",
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
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )
            assert snapshot.move == move

    def test_mixed_elo_availability(self):
        """Test GameSnapshot with one ELO missing."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
            white_elo=1500,
            black_elo=None,
            result="1-0",
        )
        assert snapshot.white_elo == 1500
        assert snapshot.black_elo is None

    def test_repr(self):
        """Test string representation of GameSnapshot."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen=fen,
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        repr_str = repr(snapshot)
        assert "GameSnapshot" in repr_str
