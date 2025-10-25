"""Tests for game_snapshots processer."""

from packages.train.src.dataset.models.raw_game import RawGame
from packages.train.src.dataset.processers.game_snapshots import (
    _compute_board_hash,
    _piece_to_int,
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


class TestPieceToInt:
    """Tests for _piece_to_int helper function."""

    def test_none_square(self):
        """Test empty square."""
        assert _piece_to_int(None) == 0

    def test_white_pieces(self):
        """Test white piece mappings."""
        import chess

        assert _piece_to_int(chess.Piece(chess.PAWN, chess.WHITE)) == 1
        assert _piece_to_int(chess.Piece(chess.KNIGHT, chess.WHITE)) == 2
        assert _piece_to_int(chess.Piece(chess.BISHOP, chess.WHITE)) == 3
        assert _piece_to_int(chess.Piece(chess.ROOK, chess.WHITE)) == 4
        assert _piece_to_int(chess.Piece(chess.QUEEN, chess.WHITE)) == 5
        assert _piece_to_int(chess.Piece(chess.KING, chess.WHITE)) == 6

    def test_black_pieces(self):
        """Test black piece mappings."""
        import chess

        assert _piece_to_int(chess.Piece(chess.PAWN, chess.BLACK)) == -1
        assert _piece_to_int(chess.Piece(chess.KNIGHT, chess.BLACK)) == -2
        assert _piece_to_int(chess.Piece(chess.BISHOP, chess.BLACK)) == -3
        assert _piece_to_int(chess.Piece(chess.ROOK, chess.BLACK)) == -4
        assert _piece_to_int(chess.Piece(chess.QUEEN, chess.BLACK)) == -5
        assert _piece_to_int(chess.Piece(chess.KING, chess.BLACK)) == -6


class TestComputeBoardHash:
    """Tests for _compute_board_hash function."""

    def test_deterministic(self):
        """Test that hash is deterministic."""
        board = [0] * 64
        hash1 = _compute_board_hash(board, "w", "e4")
        hash2 = _compute_board_hash(board, "w", "e4")
        assert hash1 == hash2

    def test_different_boards(self):
        """Test that different boards produce different hashes."""
        board1 = [0] * 64
        board2 = [0] * 64
        board2[0] = 4  # Add a rook

        hash1 = _compute_board_hash(board1, "w", "e4")
        hash2 = _compute_board_hash(board2, "w", "e4")
        assert hash1 != hash2

    def test_different_turns(self):
        """Test that different turns produce different hashes."""
        board = [0] * 64
        hash1 = _compute_board_hash(board, "w", "e4")
        hash2 = _compute_board_hash(board, "b", "e4")
        assert hash1 != hash2

    def test_different_moves(self):
        """Test that different moves produce different hashes."""
        board = [0] * 64
        hash1 = _compute_board_hash(board, "w", "e4")
        hash2 = _compute_board_hash(board, "w", "d4")
        assert hash1 != hash2

    def test_hash_length(self):
        """Test that hash is SHA-256 (64 hex chars)."""
        board = [0] * 64
        hash_val = _compute_board_hash(board, "w", "e4")
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
        assert snapshot.white_player == "Magnus"
        assert snapshot.black_player == "Hikaru"
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

        # Boards should be different after each move
        assert snapshots[0].board != snapshots[1].board

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

    def test_unknown_players(self):
        """Test game without player names."""
        pgn = """[Event "Test"]
[Result "1-0"]

1. e4 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        # PGN parser returns "?" for missing players
        assert snapshots[0].white_player == "?"
        assert snapshots[0].black_player == "?"

    def test_board_size(self):
        """Test that all boards are 64 squares."""
        pgn = """[Event "Test"]
[White "P1"]
[Black "P2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 1-0"""
        game = RawGame(id=1, pgn=pgn)
        snapshots = list(raw_game_to_snapshots(game))

        assert all(len(s.board) == 64 for s in snapshots)
