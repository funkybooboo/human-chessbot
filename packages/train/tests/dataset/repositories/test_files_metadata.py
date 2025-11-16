"""Tests for database layer."""

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from packages.train.src.dataset.models.file_metadata import FileMetadata
from packages.train.src.dataset.repositories import database, files_metadata


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    with (
        patch("packages.train.src.dataset.repositories.db_utils.DB_FILE", str(db_path)),
        patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", str(db_path)),
    ):
        yield str(db_path)


class TestDatabaseInitialization:
    """Tests for database initialization."""

    def test_initialize_database_creates_file(self, temp_db):
        """Test that initialize_database creates the database file."""
        with patch("packages.train.src.dataset.repositories.database.DB_FILE", temp_db):
            database.initialize_database()
        assert Path(temp_db).exists()

    def test_initialize_database_creates_tables(self, temp_db):
        """Test that initialize_database creates all required tables."""
        with (
            patch("packages.train.src.dataset.repositories.database.DB_FILE", temp_db),
            patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db),
        ):
            database.initialize_database()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "files_metadata" in tables

    def test_initialize_database_idempotent(self, temp_db):
        """Test that initialize_database can be called multiple times."""
        with (
            patch("packages.train.src.dataset.repositories.database.DB_FILE", temp_db),
            patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db),
        ):
            database.initialize_database()
            database.initialize_database()  # Should not raise


class TestFilesMetadataTable:
    """Tests for files_metadata table operations."""

    @pytest.fixture(autouse=True)
    def setup_db(self, temp_db):
        """Initialize database before each test."""
        with (
            patch("packages.train.src.dataset.repositories.database.DB_FILE", temp_db),
            patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db),
            patch("packages.train.src.dataset.repositories.db_utils.DB_FILE", temp_db),
        ):
            database.initialize_database()
            self.db_path = temp_db

    def test_save_file_metadata(self, temp_db):
        """Test saving a single FileMetadata object."""
        with patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db):
            metadata = FileMetadata(
                url="https://example.com/file.pgn",
                filename="file.pgn",
                games=100,
                size_gb=0.5,
            )
            files_metadata.save_file_metadata(metadata)

            # Check that ID was assigned
            assert metadata.id is not None

            # Verify in database
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files_metadata WHERE url = ?", (metadata.url,))
            row = cursor.fetchone()
            conn.close()

            assert row is not None
            assert row[1] == "https://example.com/file.pgn"
            assert row[2] == "file.pgn"
            assert row[3] == 100
            assert row[4] == 0.5

    def test_save_file_metadata_duplicate_url(self, temp_db):
        """Test that duplicate URLs are not inserted."""
        with patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db):
            metadata1 = FileMetadata(
                url="https://example.com/file.pgn",
                filename="file.pgn",
                games=100,
                size_gb=0.5,
            )
            metadata2 = FileMetadata(
                url="https://example.com/file.pgn",
                filename="file2.pgn",
                games=200,
                size_gb=1.0,
            )

            files_metadata.save_file_metadata(metadata1)
            first_id = metadata1.id
            files_metadata.save_file_metadata(metadata2)

            # Should return existing ID
            assert metadata2.id == first_id

            # Should only have one row
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM files_metadata")
            count = cursor.fetchone()[0]
            conn.close()
            assert count == 1

    def test_save_files_metadata_multiple(self, temp_db):
        """Test saving multiple FileMetadata objects."""
        with patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db):
            metadata_list = [
                FileMetadata(
                    url=f"https://example.com/file{i}.pgn",
                    filename=f"file{i}.pgn",
                    games=100 * i,
                    size_gb=0.5 * i,
                )
                for i in range(1, 4)
            ]

            files_metadata.save_files_metadata(metadata_list)

            # Check all have IDs
            for m in metadata_list:
                assert m.id is not None

            # Verify count in database
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM files_metadata")
            count = cursor.fetchone()[0]
            conn.close()
            assert count == 3

    def test_mark_file_as_processed(self, temp_db):
        """Test marking a file as processed."""
        with patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db):
            metadata = FileMetadata(
                url="https://example.com/file.pgn",
                filename="file.pgn",
                games=100,
                size_gb=0.5,
            )
            files_metadata.save_file_metadata(metadata)
            assert metadata.processed is False

            files_metadata.mark_file_as_processed(metadata)
            assert metadata.processed

        # Verify in database (outside the patch context to avoid mypy unreachable code warning)
        conn = sqlite3.connect(temp_db)  # type: ignore[unreachable]
        cursor = conn.cursor()
        cursor.execute("SELECT processed FROM files_metadata WHERE url = ?", (metadata.url,))
        row = cursor.fetchone()
        conn.close()
        assert row is not None and row[0] == 1

    def test_fetch_all_files_metadata(self, temp_db):
        """Test fetching all FileMetadata objects."""
        with patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db):
            # Insert test data
            metadata_list = [
                FileMetadata(
                    url=f"https://example.com/file{i}.pgn",
                    filename=f"file{i}.pgn",
                    games=100 * i,
                    size_gb=0.5 * i,
                )
                for i in range(1, 4)
            ]
            files_metadata.save_files_metadata(metadata_list)

            # Fetch all
            fetched = list(files_metadata.fetch_all_files_metadata())
            assert len(fetched) == 3
            assert all(isinstance(f, FileMetadata) for f in fetched)

    def test_fetch_files_metadata_under_size(self, temp_db):
        """Test fetching files under a size limit."""
        with patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db):
            # Insert test data with different sizes
            metadata_list = [
                FileMetadata(
                    url="https://example.com/small.pgn",
                    filename="small.pgn",
                    games=100,
                    size_gb=0.5,
                ),
                FileMetadata(
                    url="https://example.com/medium.pgn",
                    filename="medium.pgn",
                    games=200,
                    size_gb=1.5,
                ),
                FileMetadata(
                    url="https://example.com/large.pgn",
                    filename="large.pgn",
                    games=300,
                    size_gb=5.0,
                ),
            ]
            files_metadata.save_files_metadata(metadata_list)

            # Fetch only files under 2 GB
            fetched = list(files_metadata.fetch_files_metadata_under_size(2.0))
            assert len(fetched) == 2
            assert all(f.size_gb < 2.0 for f in fetched)

    def test_files_metadata_exist_empty(self, temp_db):
        """Test files_metadata_exist returns False for empty table."""
        with (
            patch("packages.train.src.dataset.repositories.db_utils.DB_FILE", temp_db),
            patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db),
        ):
            result = files_metadata.files_metadata_exist()
            assert result is False

    def test_files_metadata_exist_with_data(self, temp_db):
        """Test files_metadata_exist returns True when data exists."""
        with patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db):
            metadata = FileMetadata(
                url="https://example.com/file.pgn",
                filename="file.pgn",
                games=100,
                size_gb=0.5,
            )
            files_metadata.save_file_metadata(metadata)

        with patch("packages.train.src.dataset.repositories.db_utils.DB_FILE", temp_db):
            result = files_metadata.files_metadata_exist()
            assert result is True

    def test_fetch_file_metadata_by_filename(self, temp_db):
        """Test fetching FileMetadata by filename."""
        with patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db):
            metadata = FileMetadata(
                url="https://example.com/test.pgn",
                filename="test.pgn",
                games=100,
                size_gb=0.5,
            )
            files_metadata.save_file_metadata(metadata)

            result = files_metadata.fetch_file_metadata_by_filename("test.pgn")
            assert result is not None
            assert result.filename == "test.pgn"
            assert result.games == 100

    def test_fetch_file_metadata_by_filename_not_found(self, temp_db):
        """Test fetching FileMetadata by filename when not found."""
        with patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db):
            result = files_metadata.fetch_file_metadata_by_filename("nonexistent.pgn")
            assert result is None

    def test_ensure_metadata_exists_when_empty(self, temp_db):
        """Test ensure_metadata_exists fetches when database is empty."""
        with (
            patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db),
            patch("packages.train.src.dataset.repositories.db_utils.DB_FILE", temp_db),
            patch(
                "packages.train.src.dataset.requesters.file_metadata.fetch_files_metadata"
            ) as mock_fetch,
        ):
            mock_fetch.return_value = [
                FileMetadata(
                    url="https://example.com/file.pgn",
                    filename="file.pgn",
                    games=100,
                    size_gb=0.5,
                )
            ]

            files_metadata.ensure_metadata_exists()

            mock_fetch.assert_called_once()

    def test_ensure_metadata_exists_when_populated(self, temp_db):
        """Test ensure_metadata_exists skips fetch when database has data."""
        with (
            patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db),
            patch("packages.train.src.dataset.repositories.db_utils.DB_FILE", temp_db),
        ):
            # Add some data first
            metadata = FileMetadata(
                url="https://example.com/file.pgn",
                filename="file.pgn",
                games=100,
                size_gb=0.5,
            )
            files_metadata.save_file_metadata(metadata)

        with (
            patch("packages.train.src.dataset.repositories.files_metadata.DB_FILE", temp_db),
            patch("packages.train.src.dataset.repositories.db_utils.DB_FILE", temp_db),
            patch(
                "packages.train.src.dataset.requesters.file_metadata.fetch_files_metadata"
            ) as mock_fetch,
        ):
            files_metadata.ensure_metadata_exists()

            mock_fetch.assert_not_called()
