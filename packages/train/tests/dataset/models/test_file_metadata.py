"""Tests for FileMetadata model."""

from packages.train.src.dataset.models.file_metadata import FileMetadata


class TestFileMetadata:
    """Tests for FileMetadata dataclass."""

    def test_creation_minimal(self):
        """Test creating FileMetadata with required fields only."""
        metadata = FileMetadata(
            url="https://example.com/file.pgn",
            filename="file.pgn",
            games=100,
            size_gb=0.5,
        )
        assert metadata.url == "https://example.com/file.pgn"
        assert metadata.filename == "file.pgn"
        assert metadata.games == 100
        assert metadata.size_gb == 0.5
        assert metadata.id is None
        assert metadata.processed is False

    def test_creation_with_id(self):
        """Test creating FileMetadata with database ID."""
        metadata = FileMetadata(
            url="https://example.com/file.pgn",
            filename="file.pgn",
            games=100,
            size_gb=0.5,
            id=42,
        )
        assert metadata.id == 42

    def test_creation_processed(self):
        """Test creating FileMetadata with processed flag."""
        metadata = FileMetadata(
            url="https://example.com/file.pgn",
            filename="file.pgn",
            games=100,
            size_gb=0.5,
            processed=True,
        )
        assert metadata.processed is True

    def test_equality(self):
        """Test FileMetadata equality comparison."""
        m1 = FileMetadata(
            url="https://example.com/file.pgn",
            filename="file.pgn",
            games=100,
            size_gb=0.5,
        )
        m2 = FileMetadata(
            url="https://example.com/file.pgn",
            filename="file.pgn",
            games=100,
            size_gb=0.5,
        )
        assert m1 == m2

    def test_inequality(self):
        """Test FileMetadata inequality."""
        m1 = FileMetadata(
            url="https://example.com/file1.pgn",
            filename="file1.pgn",
            games=100,
            size_gb=0.5,
        )
        m2 = FileMetadata(
            url="https://example.com/file2.pgn",
            filename="file2.pgn",
            games=200,
            size_gb=1.0,
        )
        assert m1 != m2

    def test_zero_games(self):
        """Test FileMetadata with zero games."""
        metadata = FileMetadata(
            url="https://example.com/empty.pgn",
            filename="empty.pgn",
            games=0,
            size_gb=0.1,
        )
        assert metadata.games == 0

    def test_large_file_size(self):
        """Test FileMetadata with large file size."""
        metadata = FileMetadata(
            url="https://example.com/large.pgn",
            filename="large.pgn",
            games=1_000_000,
            size_gb=50.5,
        )
        assert metadata.size_gb == 50.5
        assert metadata.games == 1_000_000

    def test_repr(self):
        """Test string representation of FileMetadata."""
        metadata = FileMetadata(
            url="https://example.com/file.pgn",
            filename="file.pgn",
            games=100,
            size_gb=0.5,
        )
        repr_str = repr(metadata)
        assert "FileMetadata" in repr_str
        assert "file.pgn" in repr_str

    def test_mutable_fields(self):
        """Test that fields can be modified after creation."""
        metadata = FileMetadata(
            url="https://example.com/file.pgn",
            filename="file.pgn",
            games=100,
            size_gb=0.5,
        )
        metadata.processed = True
        metadata.id = 42
        assert metadata.processed is True
        assert metadata.id == 42

    def test_different_processed_states(self):
        """Test FileMetadata with different processed states."""
        m1 = FileMetadata(
            url="https://example.com/file.pgn",
            filename="file.pgn",
            games=100,
            size_gb=0.5,
            processed=False,
        )
        m2 = FileMetadata(
            url="https://example.com/file.pgn",
            filename="file.pgn",
            games=100,
            size_gb=0.5,
            processed=True,
        )
        assert m1.processed != m2.processed
        assert m1 != m2
