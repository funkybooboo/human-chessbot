"""Tests for RawGame model."""

import hashlib

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
        assert len(game.pgn_hash) == 64  # SHA-256 hex length

    def test_pgn_hash_computed(self):
        """Test that pgn_hash is automatically computed."""
        game1 = RawGame(pgn="1. e4 e5")
        game2 = RawGame(pgn="1. e4 e5")
        game3 = RawGame(pgn="1. d4 d5")

        # Same PGN should produce same hash
        assert game1.pgn_hash == game2.pgn_hash
        # Different PGN should produce different hash
        assert game1.pgn_hash != game3.pgn_hash

    def test_pgn_hash_uniqueness(self):
        """Test that different PGNs produce different hashes."""
        game1 = RawGame(pgn="1. e4 e5 2. Nf3 Nc6")
        game2 = RawGame(pgn="1. e4 e5 2. Nf3 Nc7")
        assert game1.pgn_hash != game2.pgn_hash

    def test_creation_with_all_fields(self):
        """Test creating RawGame with all fields."""
        game = RawGame(id=1, file_id=2, pgn="1. e4 e5", processed=True)
        assert game.id == 1
        assert game.file_id == 2
        assert game.pgn == "1. e4 e5"
        assert game.processed is True

    def test_empty_pgn_hash(self):
        """Test hash computation for empty PGN."""
        game = RawGame(pgn="")
        assert len(game.pgn_hash) == 64
        assert game.pgn_hash is not None

    def test_pgn_hash_is_sha256(self):
        """Test that pgn_hash is correct SHA-256."""
        pgn = "1. e4 e5"
        game = RawGame(pgn=pgn)
        expected_hash = hashlib.sha256(pgn.encode("utf-8")).hexdigest()
        assert game.pgn_hash == expected_hash

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
        assert len(game.pgn_hash) == 64

    def test_pgn_with_unicode(self):
        """Test RawGame with unicode characters in PGN."""
        pgn = "1. e4 e5 # Commented move ♔"
        game = RawGame(pgn=pgn)
        assert game.pgn == pgn
        assert len(game.pgn_hash) == 64

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
        # Note: pgn_hash is computed in __post_init__, so they should be equal
        assert game1 == game2

    def test_inequality_different_pgn(self):
        """Test RawGame inequality with different PGN."""
        game1 = RawGame(pgn="1. e4 e5")
        game2 = RawGame(pgn="1. d4 d5")
        assert game1 != game2

    def test_hash_deterministic(self):
        """Test that hash is deterministic across multiple creations."""
        pgn = "1. e4 e5 2. Nf3 Nc6"
        hashes = [RawGame(pgn=pgn).pgn_hash for _ in range(10)]
        assert len(set(hashes)) == 1  # All hashes should be identical

    def test_long_pgn(self):
        """Test RawGame with very long PGN."""
        moves = " ".join([f"{i}. e4 e5" for i in range(1, 100)])
        game = RawGame(pgn=moves)
        assert len(game.pgn) > 500
        assert len(game.pgn_hash) == 64

    def test_mutable_fields(self):
        """Test that fields can be modified after creation."""
        game = RawGame(pgn="1. e4 e5")
        original_hash = game.pgn_hash

        game.id = 42
        game.file_id = 1
        game.processed = True

        assert game.id == 42
        assert game.file_id == 1
        assert game.processed is True
        # Hash should not change when other fields change
        assert game.pgn_hash == original_hash

    def test_pgn_field_immutability_of_hash(self):
        """Test that modifying pgn field doesn't auto-update hash."""
        game = RawGame(pgn="1. e4 e5")
        original_hash = game.pgn_hash

        # Modify PGN (note: this doesn't re-trigger __post_init__)
        game.pgn = "1. d4 d5"

        # Hash remains the same as it's only computed in __post_init__
        assert game.pgn_hash == original_hash

    def test_whitespace_affects_hash(self):
        """Test that whitespace differences affect hash."""
        game1 = RawGame(pgn="1. e4 e5")
        game2 = RawGame(pgn="1.e4 e5")  # No space after period
        assert game1.pgn_hash != game2.pgn_hash

    def test_case_sensitivity(self):
        """Test that PGN is case-sensitive for hashing."""
        game1 = RawGame(pgn="1. E4 e5")
        game2 = RawGame(pgn="1. e4 e5")
        assert game1.pgn_hash != game2.pgn_hash
