"""Tests for combine_pgn_files module."""

from pathlib import Path

import pytest

from packages.convert.src.combine_pgn_files import PGNCombineConfig, combine_pgn_files


@pytest.fixture
def sample_pgn1(tmp_path: Path) -> Path:
    """Create a sample PGN file for testing."""
    pgn_file = tmp_path / "game1.pgn"
    content = """[Event "Test Game 1"]
[Site "Test"]
[Date "2024.01.01"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0"""
    pgn_file.write_text(content)
    return pgn_file


@pytest.fixture
def sample_pgn2(tmp_path: Path) -> Path:
    """Create another sample PGN file for testing."""
    pgn_file = tmp_path / "game2.pgn"
    content = """[Event "Test Game 2"]
[Site "Test"]
[Date "2024.01.02"]
[White "Player3"]
[Black "Player4"]
[Result "0-1"]

1. d4 d5 2. c4 e6 3. Nc3 Nf6 0-1"""
    pgn_file.write_text(content)
    return pgn_file


class TestPGNCombineConfig:
    """Tests for PGNCombineConfig class."""

    def test_valid_config(self, sample_pgn1: Path, sample_pgn2: Path, tmp_path: Path):
        """Test creating a valid configuration."""
        output_path = tmp_path / "output.pgn"
        config = PGNCombineConfig(
            pgn1_path=sample_pgn1,
            pgn2_path=sample_pgn2,
            output_path=output_path,
            delete_old=False,
        )
        assert config.pgn1_path == sample_pgn1
        assert config.pgn2_path == sample_pgn2
        assert config.output_path == output_path
        assert config.delete_old is False

    def test_missing_file_raises_error(self, sample_pgn1: Path, tmp_path: Path):
        """Test that missing input file raises FileNotFoundError."""
        missing_file = tmp_path / "nonexistent.pgn"
        output_path = tmp_path / "output.pgn"

        with pytest.raises(FileNotFoundError, match="File not found"):
            PGNCombineConfig(
                pgn1_path=sample_pgn1,
                pgn2_path=missing_file,
                output_path=output_path,
            )

    def test_output_directory_created(self, sample_pgn1: Path, sample_pgn2: Path, tmp_path: Path):
        """Test that output directory is created if it doesn't exist."""
        output_path = tmp_path / "subdir" / "output.pgn"
        PGNCombineConfig(
            pgn1_path=sample_pgn1,
            pgn2_path=sample_pgn2,
            output_path=output_path,
        )
        assert output_path.parent.exists()

    def test_string_paths_converted_to_path(
        self, sample_pgn1: Path, sample_pgn2: Path, tmp_path: Path
    ):
        """Test that string paths are converted to Path objects."""
        output_path = tmp_path / "output.pgn"
        config = PGNCombineConfig(
            pgn1_path=str(sample_pgn1),
            pgn2_path=str(sample_pgn2),
            output_path=str(output_path),
        )
        assert isinstance(config.pgn1_path, Path)
        assert isinstance(config.pgn2_path, Path)
        assert isinstance(config.output_path, Path)


class TestCombinePGNFiles:
    """Tests for combine_pgn_files function."""

    def test_basic_combination(self, sample_pgn1: Path, sample_pgn2: Path, tmp_path: Path, capsys):
        """Test basic combination of two PGN files."""
        output_path = tmp_path / "combined.pgn"
        config = PGNCombineConfig(
            pgn1_path=sample_pgn1,
            pgn2_path=sample_pgn2,
            output_path=output_path,
            delete_old=False,
        )

        combine_pgn_files(config)

        # Check output file exists
        assert output_path.exists()

        # Check content
        content = output_path.read_text()
        assert "Test Game 1" in content
        assert "Test Game 2" in content
        assert "Player1" in content
        assert "Player3" in content

        # Check proper formatting (double newline between games)
        assert "\n\n" in content

        # Check console output
        captured = capsys.readouterr()
        assert "Combined PGNs saved to" in captured.out

    def test_combination_preserves_order(
        self, sample_pgn1: Path, sample_pgn2: Path, tmp_path: Path
    ):
        """Test that combination preserves the order of games."""
        output_path = tmp_path / "combined.pgn"
        config = PGNCombineConfig(
            pgn1_path=sample_pgn1,
            pgn2_path=sample_pgn2,
            output_path=output_path,
        )

        combine_pgn_files(config)

        content = output_path.read_text()
        game1_pos = content.find("Test Game 1")
        game2_pos = content.find("Test Game 2")
        assert game1_pos < game2_pos

    def test_delete_old_files(self, sample_pgn1: Path, sample_pgn2: Path, tmp_path: Path, capsys):
        """Test that original files are deleted when delete_old=True."""
        output_path = tmp_path / "combined.pgn"
        config = PGNCombineConfig(
            pgn1_path=sample_pgn1,
            pgn2_path=sample_pgn2,
            output_path=output_path,
            delete_old=True,
        )

        combine_pgn_files(config)

        # Check output exists
        assert output_path.exists()

        # Check originals are deleted
        assert not sample_pgn1.exists()
        assert not sample_pgn2.exists()

        # Check console output
        captured = capsys.readouterr()
        assert "Original files deleted" in captured.out

    def test_keep_old_files(self, sample_pgn1: Path, sample_pgn2: Path, tmp_path: Path):
        """Test that original files are kept when delete_old=False."""
        output_path = tmp_path / "combined.pgn"
        config = PGNCombineConfig(
            pgn1_path=sample_pgn1,
            pgn2_path=sample_pgn2,
            output_path=output_path,
            delete_old=False,
        )

        combine_pgn_files(config)

        # Check all files exist
        assert output_path.exists()
        assert sample_pgn1.exists()
        assert sample_pgn2.exists()

    def test_empty_files(self, tmp_path: Path):
        """Test combining empty PGN files."""
        pgn1 = tmp_path / "empty1.pgn"
        pgn2 = tmp_path / "empty2.pgn"
        output_path = tmp_path / "combined.pgn"

        pgn1.write_text("")
        pgn2.write_text("")

        config = PGNCombineConfig(pgn1_path=pgn1, pgn2_path=pgn2, output_path=output_path)

        combine_pgn_files(config)

        assert output_path.exists()
        content = output_path.read_text()
        assert content == "\n\n\n"

    def test_whitespace_handling(self, tmp_path: Path):
        """Test that whitespace is properly handled."""
        pgn1 = tmp_path / "game1.pgn"
        pgn2 = tmp_path / "game2.pgn"
        output_path = tmp_path / "combined.pgn"

        pgn1.write_text("content1\n\n\n")
        pgn2.write_text("\n\ncontent2\n\n")

        config = PGNCombineConfig(pgn1_path=pgn1, pgn2_path=pgn2, output_path=output_path)

        combine_pgn_files(config)

        content = output_path.read_text()
        # Check that extra whitespace is stripped and proper formatting is applied
        assert content == "content1\n\ncontent2\n"
