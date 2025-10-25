"""Tests for GameSnapshot model."""

from packages.train.src.dataset.models.game_snapshot import GameSnapshot


class TestGameSnapshot:
    """Tests for GameSnapshot dataclass."""

    def test_creation_minimal(self):
        """Test creating GameSnapshot with all required fields."""
        board = [0] * 64
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            board=board,
            board_hash="abc123",
            white_player="Player1",
            black_player="Player2",
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        assert snapshot.raw_game_id == 1
        assert snapshot.move_number == 1
        assert snapshot.turn == "w"
        assert snapshot.move == "e4"
        assert len(snapshot.board) == 64
        assert snapshot.board_hash == "abc123"
        assert snapshot.white_player == "Player1"
        assert snapshot.black_player == "Player2"
        assert snapshot.white_elo == 1500
        assert snapshot.black_elo == 1500
        assert snapshot.result == "1-0"

    def test_creation_with_none_elo(self):
        """Test creating GameSnapshot with None ELO values."""
        board = [0] * 64
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            board=board,
            board_hash="abc123",
            white_player="Player1",
            black_player="Player2",
            white_elo=None,
            black_elo=None,
            result="1-0",
        )
        assert snapshot.white_elo is None
        assert snapshot.black_elo is None

    def test_board_with_pieces(self):
        """Test creating GameSnapshot with actual piece positions."""
        # Starting position for white pieces on first rank
        board = [4, 2, 3, 5, 6, 3, 2, 4] + [1] * 8 + [0] * 48
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            board=board,
            board_hash="hash1",
            white_player="Player1",
            black_player="Player2",
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        assert snapshot.board[0] == 4  # Rook
        assert snapshot.board[1] == 2  # Knight
        assert snapshot.board[8] == 1  # Pawn

    def test_equality(self):
        """Test GameSnapshot equality comparison."""
        board = [0] * 64
        s1 = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            board=board,
            board_hash="abc123",
            white_player="Player1",
            black_player="Player2",
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        s2 = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            board=board,
            board_hash="abc123",
            white_player="Player1",
            black_player="Player2",
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        assert s1 == s2

    def test_inequality_different_move(self):
        """Test GameSnapshot inequality with different moves."""
        board = [0] * 64
        s1 = GameSnapshot(
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
        s2 = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="d4",
            board=board,
            board_hash="hash2",
            white_player="P1",
            black_player="P2",
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        assert s1 != s2

    def test_black_turn(self):
        """Test GameSnapshot with black's turn."""
        board = [0] * 64
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=2,
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
        assert snapshot.turn == "b"
        assert snapshot.move_number == 2

    def test_different_results(self):
        """Test GameSnapshot with different game results."""
        board = [0] * 64
        results = ["1-0", "0-1", "1/2-1/2", "*"]

        for result in results:
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
                result=result,
            )
            assert snapshot.result == result

    def test_high_elo_ratings(self):
        """Test GameSnapshot with high ELO ratings."""
        board = [0] * 64
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            board=board,
            board_hash="hash1",
            white_player="Magnus",
            black_player="Hikaru",
            white_elo=2800,
            black_elo=2750,
            result="1-0",
        )
        assert snapshot.white_elo == 2800
        assert snapshot.black_elo == 2750

    def test_low_elo_ratings(self):
        """Test GameSnapshot with low ELO ratings."""
        board = [0] * 64
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            board=board,
            board_hash="hash1",
            white_player="Beginner1",
            black_player="Beginner2",
            white_elo=400,
            black_elo=500,
            result="1-0",
        )
        assert snapshot.white_elo == 400
        assert snapshot.black_elo == 500

    def test_late_game_move(self):
        """Test GameSnapshot with high move number."""
        board = [0] * 64
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=75,
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
        assert snapshot.move_number == 75

    def test_complex_move_notation(self):
        """Test GameSnapshot with complex SAN notation."""
        board = [0] * 64
        moves = ["e4", "Nf3", "Bb5", "O-O", "Qe2+", "Rxd8#", "exd5"]

        for move in moves:
            snapshot = GameSnapshot(
                raw_game_id=1,
                move_number=1,
                turn="w",
                move=move,
                board=board,
                board_hash=f"hash_{move}",
                white_player="P1",
                black_player="P2",
                white_elo=1500,
                black_elo=1500,
                result="1-0",
            )
            assert snapshot.move == move

    def test_negative_piece_values(self):
        """Test GameSnapshot with negative piece values (black pieces)."""
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
        assert snapshot.board[0] == -4  # Black rook
        assert snapshot.board[4] == -6  # Black king

    def test_mixed_elo_availability(self):
        """Test GameSnapshot with one ELO missing."""
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
            black_elo=None,
            result="1-0",
        )
        assert snapshot.white_elo == 1500
        assert snapshot.black_elo is None

    def test_repr(self):
        """Test string representation of GameSnapshot."""
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
        repr_str = repr(snapshot)
        assert "GameSnapshot" in repr_str

    def test_board_mutability(self):
        """Test that board list can be modified."""
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
        snapshot.board[0] = 4  # Place a rook
        assert snapshot.board[0] == 4

    def test_special_characters_in_player_names(self):
        """Test GameSnapshot with special characters in player names."""
        board = [0] * 64
        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            board=board,
            board_hash="hash1",
            white_player="Player_123",
            black_player="Player-456",
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        assert snapshot.white_player == "Player_123"
        assert snapshot.black_player == "Player-456"
