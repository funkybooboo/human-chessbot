"""Tests for FileMetadata model."""

from packages.train.src.dataset.models.file_metadata import FileMetadata


class TestFileMetadata:
    """Tests for FileMetadata dataclass."""

    def test_creation_with_required_fields(self):
        """Test creating FileMetadata with required fields sets defaults correctly."""
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

    def test_creation_with_all_fields(self):
        """Test creating FileMetadata with all fields."""
        metadata = FileMetadata(
            url="https://example.com/file.pgn",
            filename="file.pgn",
            games=100,
            size_gb=0.5,
            id=42,
            processed=True,
        )
        assert metadata.id == 42
        assert metadata.processed is True
