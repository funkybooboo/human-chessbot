"""Tests for RawGame model."""

from packages.train.src.dataset.models.raw_game import RawGame


class TestRawGame:
    """Tests for RawGame dataclass."""

    def test_creation_minimal(self):
        """Test creating RawGame with minimal fields."""
        game = RawGame(pgn="1. e4 e5")
        assert game.pgn == "1. e4 e5"
        assert game.id is None
        assert game.file_id is None
        assert game.processed is False

    def test_creation_with_all_fields(self):
        """Test creating RawGame with all fields."""
        game = RawGame(id=1, file_id=2, pgn="1. e4 e5", processed=True)
        assert game.id == 1
        assert game.file_id == 2
        assert game.pgn == "1. e4 e5"
        assert game.processed is True

    def test_complex_pgn(self):
        """Test RawGame with complex PGN including headers."""
        pgn = """[Event "Rated Blitz game"]
[Site "https://lichess.org/abcd1234"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0"""
        game = RawGame(pgn=pgn)
        assert game.pgn == pgn

    def test_pgn_with_unicode(self):
        """Test RawGame with unicode characters in PGN."""
        pgn = "1. e4 e5 # Commented move ♔"
        game = RawGame(pgn=pgn)
        assert game.pgn == pgn

    def test_pgn_with_newlines(self):
        """Test RawGame with newlines in PGN."""
        pgn = "1. e4 e5\n2. Nf3 Nc6\n3. Bb5"
        game = RawGame(pgn=pgn)
        assert game.pgn == pgn
        assert "\n" in game.pgn

    def test_equality(self):
        """Test RawGame equality."""
        game1 = RawGame(id=1, file_id=2, pgn="1. e4 e5", processed=False)
        game2 = RawGame(id=1, file_id=2, pgn="1. e4 e5", processed=False)
        assert game1 == game2

    def test_inequality_different_pgn(self):
        """Test RawGame inequality with different PGN."""
        game1 = RawGame(pgn="1. e4 e5")
        game2 = RawGame(pgn="1. d4 d5")
        assert game1 != game2

    def test_long_pgn(self):
        """Test RawGame with very long PGN."""
        moves = " ".join([f"{i}. e4 e5" for i in range(1, 100)])
        game = RawGame(pgn=moves)
        assert len(game.pgn) > 500

    def test_mutable_fields(self):
        """Test that fields can be modified after creation."""
        game = RawGame(pgn="1. e4 e5")

        game.id = 42
        game.file_id = 1
        game.processed = True

        assert game.id == 42
        assert game.file_id == 1
        assert game.processed is True
