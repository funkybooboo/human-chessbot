"""Tests for fill_snapshots module."""

from unittest.mock import MagicMock, patch

import pytest

from packages.train.src.dataset.fillers.fill_snapshots import (
    fill_database_with_snapshots,
    fill_database_with_snapshots_from_lichess_file,
)
from packages.train.src.dataset.models.file_metadata import FileMetadata
from packages.train.src.dataset.models.raw_game import RawGame


class TestFillDatabaseWithSnapshots:
    """Tests for fill_database_with_snapshots function."""

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.count_snapshots")
    def test_stops_when_threshold_reached(self, mock_count, mock_files_exist, _mock_init):
        """Test that function stops when snapshot threshold is reached."""
        mock_files_exist.return_value = True
        mock_count.return_value = 10_000  # Already at threshold

        fill_database_with_snapshots(snapshots_threshold=10_000)

        _mock_init.assert_called_once()
        mock_files_exist.assert_called_once()

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.save_files_metadata")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_files_metadata")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.count_snapshots")
    def test_fetches_metadata_if_not_exists(
        self,
        mock_count,
        mock_fetch_metadata,
        mock_save_metadata,
        mock_files_exist,
        _mock_init,
    ):
        """Test that metadata is fetched if it doesn't exist."""
        mock_files_exist.return_value = False
        mock_count.return_value = 10_000  # Stop immediately
        mock_fetch_metadata.return_value = [
            FileMetadata(
                url="https://example.com/file.pgn",
                filename="file.pgn",
                games=100,
                size_gb=0.5,
            )
        ]

        fill_database_with_snapshots(snapshots_threshold=10_000)

        mock_fetch_metadata.assert_called_once()
        mock_save_metadata.assert_called_once()

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.count_snapshots")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_unprocessed_raw_games")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.raw_game_to_snapshots")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.save_snapshot")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.mark_raw_game_as_processed")
    def test_processes_unprocessed_games(
        self,
        mock_mark_processed,
        mock_save_snapshot,
        mock_to_snapshots,
        mock_fetch_games,
        mock_count,
        mock_files_exist,
        _mock_init,
    ):
        """Test that unprocessed games are processed."""
        mock_files_exist.return_value = True

        # Mock count to reach threshold after processing
        mock_count.side_effect = [0, 1, 10_000, 10_000]  # Added extra value

        game = RawGame(id=1, pgn="1. e4 e5", processed=False)
        mock_fetch_games.return_value = [game]

        from packages.train.src.dataset.models.game_snapshot import GameSnapshot

        snapshot = GameSnapshot(
            raw_game_id=1,
            move_number=1,
            turn="w",
            move="e4",
            fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            white_elo=1500,
            black_elo=1500,
            result="1-0",
        )
        mock_to_snapshots.return_value = [snapshot]

        fill_database_with_snapshots(snapshots_threshold=10_000, print_interval=1)

        mock_to_snapshots.assert_called()
        mock_save_snapshot.assert_called()
        mock_mark_processed.assert_called()

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.count_snapshots")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_unprocessed_raw_games")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_new_raw_games")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.save_raw_game")
    def test_fetches_new_files_when_no_unprocessed(
        self,
        _mock_save_game,
        mock_fetch_new,
        mock_fetch_unprocessed,
        mock_count,
        mock_files_exist,
        _mock_init,
    ):
        """Test that new files are fetched when no unprocessed games exist."""
        mock_files_exist.return_value = True
        mock_fetch_unprocessed.return_value = []  # No unprocessed games
        mock_count.side_effect = [0, 10_000]  # Stop after fetching

        game = RawGame(id=1, pgn="1. e4 e5", processed=False)
        mock_fetch_new.return_value = [game]

        fill_database_with_snapshots(snapshots_threshold=10_000)

        mock_fetch_new.assert_called_once()

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.count_snapshots")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_unprocessed_raw_games")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_new_raw_games")
    def test_stops_when_no_new_files_available(
        self,
        mock_fetch_new,
        mock_fetch_unprocessed,
        mock_count,
        mock_files_exist,
        _mock_init,
    ):
        """Test that function stops when no new files are available."""
        mock_files_exist.return_value = True
        mock_fetch_unprocessed.return_value = []
        mock_fetch_new.return_value = []  # No new files
        mock_count.return_value = 0

        fill_database_with_snapshots(snapshots_threshold=10_000)

        # Should have attempted to fetch new files
        mock_fetch_new.assert_called_once()

    def test_uses_default_parameters(self):
        """Test that function uses default parameters correctly."""
        with (
            patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database"),
            patch(
                "packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist",
                return_value=True,
            ),
            patch(
                "packages.train.src.dataset.fillers.fill_snapshots.count_snapshots",
                return_value=100_000,
            ),
        ):
            # Should stop immediately with high threshold already met
            fill_database_with_snapshots()

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.count_snapshots")
    def test_respects_custom_threshold(self, mock_count, mock_files_exist, _mock_init):
        """Test that custom threshold is respected."""
        mock_files_exist.return_value = True
        mock_count.return_value = 500

        fill_database_with_snapshots(snapshots_threshold=500)

        # Should stop with 500 snapshots when threshold is 500
        assert mock_count.call_count >= 1


class TestFillDatabaseWithSnapshotsFromLichessFile:
    """Tests for fill_database_with_snapshots_from_lichess_file function."""

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.save_files_metadata")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_files_metadata")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_all_files_metadata")
    def test_fetches_metadata_when_table_empty(
        self,
        mock_fetch_all,
        mock_fetch_metadata,
        mock_save_metadata,
        mock_metadata_exist,
        _mock_init,
    ):
        """Test that function fetches and saves metadata when table is empty."""
        # First call: metadata doesn't exist
        # Second call: metadata exists after being saved
        mock_metadata_exist.side_effect = [False, True]

        # Mock metadata to fetch
        file_meta = FileMetadata(
            id=1,
            url="https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst",
            filename="lichess_db_standard_rated_2024-01.pgn.zst",
            games=1000,
            size_gb=0.5,
            processed=True,
        )
        mock_fetch_metadata.return_value = iter([file_meta])
        mock_fetch_all.return_value = [file_meta]

        result = fill_database_with_snapshots_from_lichess_file("lichess_db_standard_rated_2024-01.pgn.zst")

        assert result is None
        mock_fetch_metadata.assert_called_once()
        mock_save_metadata.assert_called_once()

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_all_files_metadata")
    def test_file_already_processed_noop(self, mock_fetch_all, mock_metadata_exist, _mock_init):
        """Test that function does nothing when file is already processed (noop/idempotent)."""
        mock_metadata_exist.return_value = True

        # Mock existing file that is already processed
        processed_file = FileMetadata(
            id=1,
            url="https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst",
            filename="lichess_db_standard_rated_2024-01.pgn.zst",
            games=1000,
            size_gb=0.5,
            processed=True,
        )
        mock_fetch_all.return_value = [processed_file]

        result = fill_database_with_snapshots_from_lichess_file("lichess_db_standard_rated_2024-01.pgn.zst")

        assert result is None
        _mock_init.assert_called_once()
        mock_metadata_exist.assert_called_once()

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_all_files_metadata")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_unprocessed_raw_games")
    @patch("packages.train.src.dataset.fillers.fill_snapshots._process_file_snapshots")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.mark_file_as_processed")
    def test_file_exists_not_processed_processes_games(
        self,
        mock_mark_processed,
        mock_process,
        mock_unprocessed_games,
        mock_fetch_all,
        mock_metadata_exist,
        _mock_init,
    ):
        """Test that function processes existing raw games when file exists but not processed."""
        mock_metadata_exist.return_value = True

        # Mock existing file that is not processed
        unprocessed_file = FileMetadata(
            id=1,
            url="https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst",
            filename="lichess_db_standard_rated_2024-01.pgn.zst",
            games=1000,
            size_gb=0.5,
            processed=False,
        )
        mock_fetch_all.return_value = [unprocessed_file]

        # Mock unprocessed raw games
        mock_game = RawGame(id=1, file_id=1, pgn="test", processed=False)
        mock_unprocessed_games.return_value = iter([mock_game])

        result = fill_database_with_snapshots_from_lichess_file("lichess_db_standard_rated_2024-01.pgn.zst")

        assert result is None
        mock_process.assert_called_once_with(
            unprocessed_file, batch_size=1000, print_interval=1000
        )
        mock_mark_processed.assert_called_once_with(unprocessed_file)

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_all_files_metadata")
    def test_invalid_file_raises_error(self, mock_fetch_all, mock_metadata_exist, _mock_init):
        """Test that function raises error when file is not a valid lichess file."""
        mock_metadata_exist.return_value = True

        # Mock metadata with different file (the requested file is not in metadata)
        other_file = FileMetadata(
            id=1,
            url="https://database.lichess.org/standard/other_file.pgn.zst",
            filename="other_file.pgn.zst",
            games=1000,
            size_gb=0.5,
            processed=False,
        )
        mock_fetch_all.return_value = [other_file]

        with pytest.raises(ValueError, match="not a valid lichess file"):
            fill_database_with_snapshots_from_lichess_file("nonexistent_file.pgn.zst")

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_all_files_metadata")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_unprocessed_raw_games")
    @patch("packages.train.src.dataset.fillers.fill_snapshots._download_and_save_lichess_file")
    @patch("packages.train.src.dataset.fillers.fill_snapshots._process_file_snapshots")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.mark_file_as_processed")
    def test_downloads_and_processes_new_file(
        self,
        mock_mark_processed,
        mock_process,
        mock_download,
        mock_unprocessed_games,
        mock_fetch_all,
        mock_metadata_exist,
        _mock_init,
    ):
        """Test that function downloads and processes a new file."""
        mock_metadata_exist.return_value = True

        # Mock file metadata exists in table
        file_meta = FileMetadata(
            id=1,
            url="https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.zst",
            filename="lichess_db_standard_rated_2024-01.pgn.zst",
            games=1000,
            size_gb=0.5,
            processed=False,
        )
        mock_fetch_all.return_value = [file_meta]

        # No unprocessed games exist (file hasn't been downloaded yet)
        mock_unprocessed_games.return_value = iter([])

        # Mock download returns count of games
        mock_download.return_value = 100

        result = fill_database_with_snapshots_from_lichess_file("lichess_db_standard_rated_2024-01.pgn.zst")

        assert result is None
        mock_download.assert_called_once_with(file_meta)
        mock_process.assert_called_once()
        mock_mark_processed.assert_called_once()

    @patch("packages.train.src.dataset.fillers.fill_snapshots.initialize_database")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.files_metadata_exist")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_all_files_metadata")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_unprocessed_raw_games")
    @patch("packages.train.src.dataset.fillers.fill_snapshots._download_and_save_lichess_file")
    def test_download_failure_raises_error(
        self, mock_download, mock_unprocessed_games, mock_fetch_all, mock_metadata_exist, _mock_init
    ):
        """Test that function raises error when download fails."""
        mock_metadata_exist.return_value = True

        # Mock file metadata exists in table
        file_meta = FileMetadata(
            id=1,
            url="https://database.lichess.org/standard/test_file.pgn.zst",
            filename="test_file.pgn.zst",
            games=1000,
            size_gb=0.5,
            processed=False,
        )
        mock_fetch_all.return_value = [file_meta]

        # No unprocessed games exist
        mock_unprocessed_games.return_value = iter([])

        # Mock download fails
        mock_download.side_effect = RuntimeError("Failed to download test_file.pgn.zst (status 500)")

        with pytest.raises(RuntimeError, match="Failed to download"):
            fill_database_with_snapshots_from_lichess_file("test_file.pgn.zst")


class TestFillSnapshotsIntegration:
    """Integration tests for fill_snapshots (with mocked external dependencies)."""

    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_files_metadata")
    @patch("packages.train.src.dataset.fillers.fill_snapshots.fetch_new_raw_games")
    def test_full_pipeline_mock(self, mock_fetch_new, mock_fetch_metadata, tmp_path):
        """Test the full pipeline with mocked external dependencies."""
        # This is a placeholder for a more comprehensive integration test
        # that would require a full database setup
        pass
