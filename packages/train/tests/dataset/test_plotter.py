"""Tests for plotter module."""

import sqlite3
from unittest.mock import patch

import pytest

from packages.train.src.dataset.charts.plotter import compute_histograms, plot_elo_distribution


class TestComputeHistograms:
    """Tests for compute_histograms function."""

    def test_nonexistent_database(self):
        """Test that FileNotFoundError is raised for nonexistent database."""
        with pytest.raises(FileNotFoundError):
            compute_histograms("/nonexistent/database.db")

    def test_empty_database(self, tmp_path):
        """Test computing histograms on empty database."""
        db_path = tmp_path / "empty.db"

        # Create database with game_snapshots table but no data
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE game_snapshots (
                white_elo INTEGER,
                black_elo INTEGER
            )
        """
        )
        conn.commit()
        conn.close()

        white_counts, black_counts, bin_edges = compute_histograms(
            str(db_path), bin_size=50, min_val=600, max_val=1900
        )

        assert len(white_counts) > 0
        assert len(black_counts) > 0
        assert all(c == 0 for c in white_counts)
        assert all(c == 0 for c in black_counts)

    def test_database_with_data(self, tmp_path):
        """Test computing histograms with actual data."""
        db_path = tmp_path / "test.db"

        # Create and populate database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE game_snapshots (
                white_elo INTEGER,
                black_elo INTEGER
            )
        """
        )

        # Insert test data
        for _ in range(10):
            cursor.execute(
                "INSERT INTO game_snapshots (white_elo, black_elo) VALUES (?, ?)", (1500, 1600)
            )

        conn.commit()
        conn.close()

        white_counts, black_counts, bin_edges = compute_histograms(
            str(db_path), bin_size=100, min_val=1000, max_val=2000
        )

        # Should have counts in the appropriate bins
        assert sum(white_counts) == 10
        assert sum(black_counts) == 10

    def test_none_elo_values(self, tmp_path):
        """Test handling of None ELO values."""
        db_path = tmp_path / "test.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE game_snapshots (
                white_elo INTEGER,
                black_elo INTEGER
            )
        """
        )

        # Insert data with some None values
        cursor.execute("INSERT INTO game_snapshots (white_elo, black_elo) VALUES (1500, NULL)")
        cursor.execute("INSERT INTO game_snapshots (white_elo, black_elo) VALUES (NULL, 1600)")

        conn.commit()
        conn.close()

        white_counts, black_counts, bin_edges = compute_histograms(
            str(db_path), bin_size=100, min_val=1000, max_val=2000
        )

        # Should only count non-None values
        assert sum(white_counts) == 1
        assert sum(black_counts) == 1

    def test_custom_bin_size(self, tmp_path):
        """Test using custom bin size."""
        db_path = tmp_path / "test.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE game_snapshots (
                white_elo INTEGER,
                black_elo INTEGER
            )
        """
        )
        cursor.execute("INSERT INTO game_snapshots (white_elo, black_elo) VALUES (1500, 1500)")
        conn.commit()
        conn.close()

        white_counts, black_counts, bin_edges = compute_histograms(
            str(db_path), bin_size=200, min_val=1000, max_val=2000
        )

        # With range 1000-2000 and bin_size 200, should have 5 bins
        assert len(bin_edges) == 6  # n_bins + 1 edges

    def test_invalid_min_max(self, tmp_path):
        """Test that ValueError is raised when min >= max."""
        db_path = tmp_path / "test.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE game_snapshots (
                white_elo INTEGER,
                black_elo INTEGER
            )
        """
        )
        conn.commit()
        conn.close()

        with pytest.raises(ValueError):
            compute_histograms(str(db_path), min_val=2000, max_val=1000)

    def test_out_of_range_values(self, tmp_path):
        """Test that out-of-range values are clamped to bins."""
        db_path = tmp_path / "test.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE game_snapshots (
                white_elo INTEGER,
                black_elo INTEGER
            )
        """
        )

        # Insert values outside the range
        cursor.execute("INSERT INTO game_snapshots (white_elo, black_elo) VALUES (3000, 100)")

        conn.commit()
        conn.close()

        white_counts, black_counts, bin_edges = compute_histograms(
            str(db_path), bin_size=100, min_val=1000, max_val=2000
        )

        # Values should be clamped to edge bins
        assert sum(white_counts) == 1
        assert sum(black_counts) == 1


class TestPlotEloDistribution:
    """Tests for plot_elo_distribution function."""

    @patch("packages.train.src.dataset.plotter.plt")
    @patch("packages.train.src.dataset.plotter.compute_histograms")
    def test_plot_creation(self, mock_compute, mock_plt):
        """Test that plot is created correctly."""
        mock_compute.return_value = (
            [10, 20, 30],  # white_counts
            [15, 25, 35],  # black_counts
            [1000, 1100, 1200, 1300],  # bin_edges
        )

        plot_elo_distribution("dummy.db", bins=50, show=False)

        # Should create figure
        mock_plt.figure.assert_called_once()
        mock_compute.assert_called_once()

    @patch("packages.train.src.dataset.plotter.plt")
    @patch("packages.train.src.dataset.plotter.compute_histograms")
    def test_save_plot(self, mock_compute, mock_plt, tmp_path):
        """Test saving plot to file."""
        mock_compute.return_value = (
            [10, 20, 30],
            [15, 25, 35],
            [1000, 1100, 1200, 1300],
        )

        save_path = tmp_path / "plot.png"

        plot_elo_distribution("dummy.db", save_path=str(save_path), show=False)

        # Should call savefig (note: actual code doesn't use bbox_inches='tight')
        mock_plt.savefig.assert_called_once_with(str(save_path), dpi=150)

    @patch("packages.train.src.dataset.plotter.plt")
    @patch("packages.train.src.dataset.plotter.compute_histograms")
    def test_show_plot(self, mock_compute, mock_plt):
        """Test showing plot."""
        mock_compute.return_value = ([10], [15], [1000, 1100])

        plot_elo_distribution("dummy.db", show=True)

        # Should call plt.show()
        mock_plt.show.assert_called_once()

    @patch("packages.train.src.dataset.plotter.compute_histograms")
    def test_plot_with_custom_bins(self, mock_compute):
        """Test plotting with custom bin size."""
        mock_compute.return_value = ([10], [15], [1000, 1100])

        with patch("packages.train.src.dataset.plotter.plt"):
            plot_elo_distribution("dummy.db", bins=100, show=False)

        # Should pass bins parameter with min/max values to compute_histograms
        mock_compute.assert_called_once_with(
            db_path="dummy.db", bin_size=100, min_val=600, max_val=1900
        )

    @patch("packages.train.src.dataset.plotter.plt")
    @patch("packages.train.src.dataset.plotter.compute_histograms")
    def test_plot_formatting(self, mock_compute, mock_plt):
        """Test that plot has proper formatting."""
        mock_compute.return_value = (
            [10, 20, 30],
            [15, 25, 35],
            [1000, 1100, 1200, 1300],
        )

        plot_elo_distribution("dummy.db", show=False)

        # Should set labels and title using plt functions (not axes)
        mock_plt.xlabel.assert_called_once_with("Elo Rating")
        mock_plt.ylabel.assert_called_once_with("Frequency")
        mock_plt.title.assert_called_once_with("Distribution of White and Black Elo Ratings")


class TestPlotterConstants:
    """Test that plotter uses constants correctly."""

    def test_imports_constants(self):
        """Test that constants are imported."""
        from packages.train.src.dataset.charts.plotter import MAX_ELO, MIN_ELO

        assert MIN_ELO == 600
        assert MAX_ELO == 1900
