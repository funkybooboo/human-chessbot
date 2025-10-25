"""Tests for pgn_to_csv module."""

import csv
from pathlib import Path

import pytest
import zstandard as zstd

from packages.convert.src.pgn_to_csv import (
    GameMetadata,
    PGNToCSVConfig,
    _convert_board_to_row,
    convert_pgn_to_csv,
)


@pytest.fixture
def sample_pgn_file(tmp_path: Path) -> Path:
    """Create a sample PGN file for testing."""
    pgn_file = tmp_path / "test.pgn"
    content = """[Event "Test Tournament"]
[Site "Test City"]
[Date "2024.01.01"]
[Round "1"]
[White "Player One"]
[Black "Player Two"]
[Result "1-0"]
[WhiteElo "2000"]
[BlackElo "1950"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0

[Event "Test Tournament"]
[Site "Test City"]
[Date "2024.01.02"]
[Round "2"]
[White "Player Three"]
[Black "Player Four"]
[Result "0-1"]
[WhiteElo "1800"]
[BlackElo "1850"]

1. d4 d5 2. c4 c6 0-1
"""
    pgn_file.write_text(content)
    return pgn_file


@pytest.fixture
def sample_pgn_no_elo(tmp_path: Path) -> Path:
    """Create a PGN file without Elo ratings."""
    pgn_file = tmp_path / "no_elo.pgn"
    content = """[Event "Casual Game"]
[Site "Test"]
[Date "2024.01.01"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 2. Nf3 1-0
"""
    pgn_file.write_text(content)
    return pgn_file


@pytest.fixture
def sample_compressed_pgn(tmp_path: Path, sample_pgn_file: Path) -> Path:
    """Create a Zstandard compressed PGN file."""
    compressed_file = tmp_path / "test.pgn.zst"
    content = sample_pgn_file.read_bytes()

    cctx = zstd.ZstdCompressor()
    compressed_data = cctx.compress(content)
    compressed_file.write_bytes(compressed_data)

    return compressed_file


class TestPGNToCSVConfig:
    """Tests for PGNToCSVConfig class."""

    def test_valid_config(self, sample_pgn_file: Path, tmp_path: Path):
        """Test creating a valid configuration."""
        dest_path = tmp_path / "output.csv"
        config = PGNToCSVConfig(
            source_path=sample_pgn_file, destination_path=dest_path, verbose=False
        )
        assert config.source_path == sample_pgn_file
        assert config.destination_path == dest_path
        assert config.verbose is False

    def test_missing_source_raises_error(self, tmp_path: Path):
        """Test that missing source file raises FileNotFoundError."""
        missing_file = tmp_path / "nonexistent.pgn"
        dest_path = tmp_path / "output.csv"

        with pytest.raises(FileNotFoundError, match="Source file not found"):
            PGNToCSVConfig(source_path=missing_file, destination_path=dest_path)

    def test_invalid_destination_extension(self, sample_pgn_file: Path, tmp_path: Path):
        """Test that non-.csv destination raises ValueError."""
        dest_path = tmp_path / "output.txt"

        with pytest.raises(ValueError, match="must end with .csv"):
            PGNToCSVConfig(source_path=sample_pgn_file, destination_path=dest_path)

    def test_destination_directory_created(self, sample_pgn_file: Path, tmp_path: Path):
        """Test that destination directory is created if it doesn't exist."""
        dest_path = tmp_path / "subdir" / "output.csv"
        PGNToCSVConfig(source_path=sample_pgn_file, destination_path=dest_path)
        assert dest_path.parent.exists()

    def test_verbose_flag(self, sample_pgn_file: Path, tmp_path: Path):
        """Test verbose flag configuration."""
        dest_path = tmp_path / "output.csv"
        config = PGNToCSVConfig(
            source_path=sample_pgn_file, destination_path=dest_path, verbose=True
        )
        assert config.verbose is True


class TestGameMetadata:
    """Tests for GameMetadata class."""

    def test_valid_metadata(self):
        """Test creating valid game metadata."""
        metadata = GameMetadata(white_elo="2000", black_elo="1950", is_black=False)
        assert metadata.white_elo == "2000"
        assert metadata.black_elo == "1950"
        assert metadata.is_black is False

    def test_metadata_with_boolean(self):
        """Test metadata with boolean values."""
        metadata = GameMetadata(white_elo="0", black_elo="0", is_black=True)
        assert metadata.is_black is True


class TestConvertBoardToRow:
    """Tests for _convert_board_to_row function."""

    def test_starting_position(self):
        """Test converting the starting chess position."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        metadata = GameMetadata(white_elo="2000", black_elo="1950", is_black=False)
        move = "e2e4"

        row = _convert_board_to_row(fen, metadata, move)

        # Check format
        assert row.endswith("e2e4\n")
        assert row.startswith("2000,1950,0,")

        # Check board representation
        parts = row.strip().split(",")
        assert len(parts) == 68  # 3 metadata + 64 squares + 1 move

        # Check some piece positions (FEN is read from rank 8 to rank 1, so A8 is first)
        board_values = [int(x) for x in parts[3:67]]
        assert board_values[0] == 10  # A8: Black Rook
        assert board_values[7] == 10  # H8: Black Rook
        assert board_values[56] == 4  # A1: White Rook
        assert board_values[63] == 4  # H1: White Rook

    def test_empty_board(self):
        """Test converting an empty board."""
        fen = "8/8/8/8/8/8/8/8 w - - 0 1"
        metadata = GameMetadata(white_elo="0", black_elo="0", is_black=False)
        move = "none"

        row = _convert_board_to_row(fen, metadata, move)

        parts = row.strip().split(",")
        board_values = [int(x) for x in parts[3:67]]

        # All squares should be empty (0)
        assert all(val == 0 for val in board_values)

    def test_black_move(self):
        """Test converting a position with black to move."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        metadata = GameMetadata(white_elo="2000", black_elo="1950", is_black=True)
        move = "e7e5"

        row = _convert_board_to_row(fen, metadata, move)

        assert row.startswith("2000,1950,1,")  # is_black=1

    def test_piece_values(self):
        """Test that piece values are correctly mapped."""
        # Position with one of each piece type
        fen = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"
        metadata = GameMetadata(white_elo="0", black_elo="0", is_black=False)
        move = "test"

        row = _convert_board_to_row(fen, metadata, move)
        parts = row.strip().split(",")
        board_values = [int(x) for x in parts[3:67]]

        # Black king at E8 (FEN reads from rank 8 first, so index 4 for E8)
        assert board_values[4] == 12  # k = 12

        # White king at E1 (last rank in FEN, so index 60 for E1)
        assert board_values[60] == 6  # K = 6


class TestConvertPGNToCSV:
    """Tests for convert_pgn_to_csv function."""

    def test_basic_conversion(self, sample_pgn_file: Path, tmp_path: Path):
        """Test basic PGN to CSV conversion."""
        output_csv = tmp_path / "output.csv"
        config = PGNToCSVConfig(
            source_path=sample_pgn_file, destination_path=output_csv, verbose=False
        )

        convert_pgn_to_csv(config)

        # Check file was created
        assert output_csv.exists()

        # Read and validate CSV
        with open(output_csv, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        header = rows[0]
        assert header[0] == "white_elo"
        assert header[1] == "black_elo"
        assert header[2] == "blacks_move"
        assert header[-1] == "selected_move"
        assert len(header) == 68  # 3 metadata + 64 squares + 1 move

        # Check data rows exist (2 games with multiple moves each)
        assert len(rows) > 1

        # Check first data row has correct Elo ratings
        assert rows[1][0] == "2000"  # white_elo
        assert rows[1][1] == "1950"  # black_elo

    def test_conversion_with_no_elo(self, sample_pgn_no_elo: Path, tmp_path: Path):
        """Test conversion of games without Elo ratings."""
        output_csv = tmp_path / "output.csv"
        config = PGNToCSVConfig(source_path=sample_pgn_no_elo, destination_path=output_csv)

        convert_pgn_to_csv(config)

        with open(output_csv, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check default Elo of "0"
        assert rows[1][0] == "0"
        assert rows[1][1] == "0"

    def test_compressed_file_conversion(self, sample_compressed_pgn: Path, tmp_path: Path):
        """Test conversion of Zstandard compressed PGN files."""
        output_csv = tmp_path / "output.csv"
        config = PGNToCSVConfig(source_path=sample_compressed_pgn, destination_path=output_csv)

        convert_pgn_to_csv(config)

        # Check file was created and has content
        assert output_csv.exists()

        with open(output_csv, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) > 1  # Header + data rows

    def test_verbose_output(self, sample_pgn_file: Path, tmp_path: Path, capsys):
        """Test that verbose mode produces output."""
        output_csv = tmp_path / "output.csv"
        config = PGNToCSVConfig(
            source_path=sample_pgn_file, destination_path=output_csv, verbose=True
        )

        convert_pgn_to_csv(config)

        captured = capsys.readouterr()
        assert "[INFO]" in captured.out
        assert "[DONE]" in captured.out

    def test_move_alternation(self, sample_pgn_file: Path, tmp_path: Path):
        """Test that moves alternate correctly between white and black."""
        output_csv = tmp_path / "output.csv"
        config = PGNToCSVConfig(source_path=sample_pgn_file, destination_path=output_csv)

        convert_pgn_to_csv(config)

        with open(output_csv, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Skip header, check first few moves of first game
        # Move 1 white (blacks_move=0), Move 1 black (blacks_move=1), etc.
        assert rows[1][2] == "0"  # White's first move
        assert rows[2][2] == "1"  # Black's first move
        assert rows[3][2] == "0"  # White's second move
        assert rows[4][2] == "1"  # Black's second move

    def test_board_values_range(self, sample_pgn_file: Path, tmp_path: Path):
        """Test that all board values are in valid range."""
        output_csv = tmp_path / "output.csv"
        config = PGNToCSVConfig(source_path=sample_pgn_file, destination_path=output_csv)

        convert_pgn_to_csv(config)

        with open(output_csv, encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check all board values are 0-12
        for row in rows[1:]:  # Skip header
            board_values = [int(x) for x in row[3:67]]
            assert all(0 <= val <= 12 for val in board_values)

    def test_empty_pgn_file(self, tmp_path: Path):
        """Test conversion of empty PGN file."""
        empty_pgn = tmp_path / "empty.pgn"
        empty_pgn.write_text("")

        output_csv = tmp_path / "output.csv"
        config = PGNToCSVConfig(source_path=empty_pgn, destination_path=output_csv)

        convert_pgn_to_csv(config)

        # Should still create file with header
        assert output_csv.exists()

        with open(output_csv, encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 1  # Only header
