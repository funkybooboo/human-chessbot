import argparse
import os
import sqlite3

from matplotlib import pyplot as plt

from packages.train.src.constants import DB_FILE, MAX_ELO, MIN_ELO


def compute_histograms(
    db_path: str = DB_FILE,
    bin_size: int = 50,
    min_val: int | None = MIN_ELO,
    max_val: int | None = MAX_ELO,
    batch_size: int = 10_000,
) -> tuple[list[int], list[int], list[float]]:
    """Compute histogram counts for white and black Elo ratings by streaming rows.

    Uses fixed-size bins specified by `bin_size` and a min/max range. Defaults
    to 50-point bins covering 600..1900.

    Args:
        db_path: Path to the SQLite database file.
        bin_size: Width of each bin (e.g. 50 for 50-point Elo bins).
        min_val: Minimum Elo to include (inclusive).
        max_val: Maximum Elo to include (exclusive upper edge).
        batch_size: Number of rows to fetch per roundtrip.

    Returns:
        (white_counts, black_counts, bin_edges)
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        # Efficiently compute min/max via SQL to avoid scanning everything in Python
        cur.execute(
            "SELECT MIN(white_elo), MAX(white_elo), MIN(black_elo), MAX(black_elo) FROM game_snapshots"
        )
        min_white, max_white, min_black, max_black = cur.fetchone()

        # If min/max not provided, derive from DB; otherwise use provided range
        if min_val is None or max_val is None:
            candidates = [v for v in (min_white, max_white, min_black, max_black) if v is not None]
            if not candidates:
                # No data
                return [], [], []
            overall_min = min(candidates)
            overall_max = max(candidates)
        else:
            overall_min = min_val
            overall_max = max_val

        if overall_min >= overall_max:
            raise ValueError("min_val must be less than max_val")

        # compute number of bins to exactly cover the requested range using the bin_size
        total_range = overall_max - overall_min
        bins = int((total_range + bin_size - 1) // bin_size)  # ceil division
        bin_edges = [float(overall_min + i * bin_size) for i in range(bins + 1)]

        white_counts = [0] * bins
        black_counts = [0] * bins

        # Stream rows and increment bin counters
        cur.execute("SELECT white_elo, black_elo FROM game_snapshots")
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            for white, black in rows:
                if white is not None:
                    # value stored as int already in DB; map to bin index
                    # Map to fixed-size bins, clamp out-of-range values
                    idx = (white - overall_min) // bin_size
                    if idx < 0:
                        idx = 0
                    elif idx >= bins:
                        idx = bins - 1
                    white_counts[int(idx)] += 1
                if black is not None:
                    idx = (black - overall_min) // bin_size
                    if idx < 0:
                        idx = 0
                    elif idx >= bins:
                        idx = bins - 1
                    black_counts[int(idx)] += 1

    return white_counts, black_counts, bin_edges


def plot_elo_distribution(
    db_path: str = DB_FILE,
    bins: int = 50,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot (and optionally save) the Elo rating distributions using precomputed counts.

    This function delegates to `compute_histograms` so it never needs to hold all
    Elo values in Python memory.

    Args:
        db_path: Path to the SQLite database file.
        bins: Bin width in Elo points.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    white_counts, black_counts, bin_edges = compute_histograms(
        db_path=db_path, bin_size=bins, min_val=600, max_val=1900
    )

    # compute bin centers and width
    bin_count = max(0, len(bin_edges) - 1)
    if bin_count == 0:
        return
    bin_width = float(bin_edges[1] - bin_edges[0])
    bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2.0 for i in range(bin_count)]

    plt.figure(figsize=(10, 6))
    # Plot side-by-side bars by shifting centers
    shift = bin_width * 0.25
    width = bin_width * 0.45
    plt.bar(
        [c - shift for c in bin_centers],
        white_counts,
        width=width,
        alpha=0.8,
        label="White Elo",
        color="#1f77b4",
    )
    plt.bar(
        [c + shift for c in bin_centers],
        black_counts,
        width=width,
        alpha=0.8,
        label="Black Elo",
        color="#111111",
    )

    plt.xlabel("Elo Rating")
    plt.ylabel("Frequency")
    plt.title("Distribution of White and Black Elo Ratings")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot Elo distributions from the database")
    p.add_argument(
        "-b", "--bins", type=int, default=50, help="Bin width in Elo points (default 50)"
    )
    p.add_argument(
        "--show",
        dest="show",
        action="store_true",
        help="Display plot in GUI (default: save to file)",
    )
    p.add_argument(
        "-o",
        "--output",
        default="elo_distribution.png",
        help="File path to save the plot (default: elo_distribution.png)",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    plot_elo_distribution(db_path=DB_FILE, bins=args.bins, show=args.show, save_path=args.output)
