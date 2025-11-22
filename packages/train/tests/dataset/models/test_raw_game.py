"""Tests for RawGame model."""

from packages.train.src.dataset.models.raw_game import RawGame


class TestRawGame:
    """Tests for RawGame dataclass."""

    def test_creation_with_required_fields(self):
        """Test creating RawGame with required fields sets defaults correctly."""
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

    def test_complex_pgn_with_headers(self):
        """Test RawGame with complex PGN including headers."""
        pgn = """[Event "Rated Blitz game"]
[Site "https://lichess.org/abcd1234"]
[Date "2024.01.15"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0"""
        game = RawGame(pgn=pgn)
        assert "[Event" in game.pgn
        assert "1. e4 e5" in game.pgn
