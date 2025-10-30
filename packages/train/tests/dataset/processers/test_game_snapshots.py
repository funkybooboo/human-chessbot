"""Tests for game_snapshots processer."""

from packages.train.src.dataset.models.raw_game import RawGame
from packages.train.src.dataset.processers.game_snapshots import (
    _compute_board_hash,
    _safe_int,
    raw_game_to_snapshots,
)


class TestSafeInt:
    """Tests for _safe_int helper function."""

    def test_valid_int_string(self):
        """Test converting valid int string."""
        assert _safe_int("1500") == 1500

    def test_none(self):
        """Test converting None."""
        assert _safe_int(None) is None

    def test_invalid_string(self):
        """Test converting invalid string."""
        assert _safe_int("not a number") is None

    def test_empty_string(self):
        """Test converting empty string."""
        assert _safe_int("") is None

    def test_negative_number(self):
        """Test converting negative number."""
        assert _safe_int("-100") == -100

    def test_zero(self):
        """Test converting zero."""
        assert _safe_int("0") == 0


class TestComputeBoardHash:
    """Tests for _compute_board_hash function."""

    def test_deterministic(self):
        """Test that hash is deterministic."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        hash1 = _compute_board_hash(fen, "w", "e4")
        hash2 = _compute_board_hash(fen, "w", "e4")
        assert hash1 == hash2

    def test_different_boards(self):
        """Test that different FEN positions produce different hashes."""
        fen1 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        fen2 = "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1"

        hash1 = _compute_board_hash(fen1, "w", "e4")
        hash2 = _compute_board_hash(fen2, "w", "e4")
        assert hash1 != hash2

    def test_different_turns(self):
        """Test that different turns produce different hashes."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        hash1 = _compute_board_hash(fen, "w", "e4")
        hash2 = _compute_board_hash(fen, "b", "e4")
        assert hash1 != hash2

    def test_different_moves(self):
        """Test that different moves produce different hashes."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        hash1 = _compute_board_hash(fen, "w", "e4")
        hash2 = _compute_board_hash(fen, "w", "d4")
        assert hash1 != hash2

    def test_hash_length(self):
        """Test that hash is SHA-256 (64 hex chars)."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        hash_val = _compute_board_hash(fen, "w", "e4")
        assert len(hash_val) == 64


class TestRawGameToSnapshots:
    """Tests for raw_game_to_snapshots function."""

    def test_simple_game(self):
        """Test converting a simple game."""
        pgn = """[Event "Test"]
[Site "Test"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]
[WhiteElo "1500"]
[BlackElo "1500"]

1. e4 e5 2. Nf3 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        assert len(snapshots) == 3  # e4, e5, Nf3
        assert snapshots[0].move == "e4"
        assert snapshots[0].turn == "w"
        assert snapshots[1].move == "e5"
        assert snapshots[1].turn == "b"
        assert snapshots[2].move == "Nf3"
        assert snapshots[2].turn == "w"

    def test_game_metadata(self):
        """Test that game metadata is preserved."""
        pgn = """[Event "Test Event"]
[Site "Test Site"]
[White "Magnus"]
[Black "Hikaru"]
[Result "1-0"]
[WhiteElo "2800"]
[BlackElo "2750"]

1. e4 1-0"""
        game = RawGame(id=42, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        snapshot = snapshots[0]
        assert snapshot.raw_game_id == 42
        assert snapshot.white_elo == 2800
        assert snapshot.black_elo == 2750
        assert snapshot.result == "1-0"

    def test_game_without_elo(self):
        """Test game without ELO ratings."""
        pgn = """[Event "Test"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        assert len(snapshots) == 1
        assert snapshots[0].white_elo is None
        assert snapshots[0].black_elo is None

    def test_invalid_elo(self):
        """Test game with invalid ELO ratings."""
        pgn = """[Event "Test"]
[White "Player1"]
[Black "Player2"]
[WhiteElo "?"]
[BlackElo "invalid"]
[Result "1-0"]

1. e4 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        assert snapshots[0].white_elo is None
        assert snapshots[0].black_elo is None

    def test_move_numbers(self):
        """Test that move numbers are sequential."""
        pgn = """[Event "Test"]
[White "P1"]
[Black "P2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        assert len(snapshots) == 5
        for i, snapshot in enumerate(snapshots):
            assert snapshot.move_number == i + 1

    def test_board_state_changes(self):
        """Test that board state changes after each move."""
        pgn = """[Event "Test"]
[White "P1"]
[Black "P2"]
[Result "1-0"]

1. e4 e5 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        # FENs should be different after each move
        assert snapshots[0].fen != snapshots[1].fen

    def test_unique_board_hashes(self):
        """Test that each snapshot has a unique board hash."""
        pgn = """[Event "Test"]
[White "P1"]
[Black "P2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        hashes = [s.board_hash for s in snapshots]
        assert len(hashes) == len(set(hashes))  # All unique

    def test_invalid_pgn(self):
        """Test handling of invalid PGN."""
        game = RawGame(id=1, pgn="not a valid pgn")
        snapshots = list(raw_game_to_snapshots(game))
        assert len(snapshots) == 0

    def test_empty_pgn(self):
        """Test handling of empty PGN."""
        game = RawGame(id=1, pgn="")
        snapshots = list(raw_game_to_snapshots(game))
        assert len(snapshots) == 0

    def test_game_with_no_moves(self):
        """Test game with headers but no moves."""
        pgn = """[Event "Test"]
[White "P1"]
[Black "P2"]
[Result "*"]

*"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))
        assert len(snapshots) == 0

    def test_long_game(self):
        """Test a longer game."""
        # Sicilian Defense, Dragon Variation
        pgn = """[Event "Test"]
[White "P1"]
[Black "P2"]
[Result "1-0"]

1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 g6 6. Be3 Bg7 7. f3 O-O 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        assert len(snapshots) == 14  # 7 moves each
        assert snapshots[-1].move == "O-O"

    def test_castling_moves(self):
        """Test games with castling."""
        pgn = """[Event "Test"]
[White "P1"]
[Black "P2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nf6 3. Be2 Be7 4. O-O O-O 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        castling_moves = [s.move for s in snapshots if "O-O" in s.move]
        assert len(castling_moves) == 2

    def test_promotion_move(self):
        """Test game with pawn promotion."""
        pgn = """[Event "Test"]
[White "P1"]
[Black "P2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nf6 3. h4 h5 4. a4 a5 5. b4 axb4 6. a5 Ra6 7. axb6 Rxa1 8. b7 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        assert len(snapshots) > 0
        assert all(s.raw_game_id == 1 for s in snapshots)

    def test_check_and_checkmate_notation(self):
        """Test games with check and checkmate notation."""
        pgn = """[Event "Fool's Mate"]
[White "P1"]
[Black "P2"]
[Result "0-1"]

1. f3 e5 2. g4 Qh4# 0-1"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        assert len(snapshots) == 4
        # Checkmate move should be recorded
        assert snapshots[-1].move == "Qh4#"

    def test_draw_result(self):
        """Test game with draw result."""
        pgn = """[Event "Test"]
[White "P1"]
[Black "P2"]
[Result "1/2-1/2"]

1. e4 e5 2. Nf3 Nf6 1/2-1/2"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        assert all(s.result == "1/2-1/2" for s in snapshots)

    def test_fen_format(self):
        """Test that all snapshots have valid FEN strings."""
        pgn = """[Event "Test"]
[White "P1"]
[Black "P2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        # All snapshots should have FEN strings
        assert all(s.fen for s in snapshots)
        # FEN strings should have the correct format (contains spaces)
        assert all(" " in s.fen for s in snapshots)
