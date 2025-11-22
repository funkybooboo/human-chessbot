"""Plot rating change distributions."""

import argparse
import sqlite3

from matplotlib import pyplot as plt

from packages.train.src.constants import DB_FILE


def compute_rating_change_histogram(
    db_path: str = DB_FILE,
    bin_size: int = 2,
    min_val: int = -50,
    max_val: int = 50,
) -> tuple[list[int], list[int], list[float]]:
    """Compute histogram of rating changes.

    Args:
        db_path: Path to the SQLite database file.
        bin_size: Width of each bin.
        min_val: Minimum rating change to include.
        max_val: Maximum rating change to include.

    Returns:
        (white_counts, black_counts, bin_edges)
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()

        bins = (max_val - min_val) // bin_size
        bin_edges = [float(min_val + i * bin_size) for i in range(bins + 1)]

        white_counts = [0] * bins
        black_counts = [0] * bins

        cur.execute(
            """
            SELECT white_rating_diff, black_rating_diff
            FROM game_statistics
            WHERE white_rating_diff IS NOT NULL AND black_rating_diff IS NOT NULL
            """
        )

        batch_size = 10_000
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            for white_diff, black_diff in rows:
                if white_diff is not None:
                    idx = (white_diff - min_val) // bin_size
                    if 0 <= idx < bins:
                        white_counts[idx] += 1
                if black_diff is not None:
                    idx = (black_diff - min_val) // bin_size
                    if 0 <= idx < bins:
                        black_counts[idx] += 1

    return white_counts, black_counts, bin_edges


def plot_rating_changes(
    db_path: str = DB_FILE,
    bin_size: int = 2,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot histogram of rating changes.

    Args:
        db_path: Path to the SQLite database file.
        bin_size: Width of each bin.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    white_counts, black_counts, bin_edges = compute_rating_change_histogram(
        db_path=db_path, bin_size=bin_size
    )

    if not bin_edges:
        print("No rating change data found.")
        return

    bin_count = len(bin_edges) - 1
    bin_width = bin_edges[1] - bin_edges[0]
    bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2.0 for i in range(bin_count)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # White rating changes
    ax1.bar(bin_centers, white_counts, width=bin_width * 0.9, color="#1f77b4", alpha=0.8)
    ax1.axvline(x=0, color="red", linestyle="--", linewidth=1.5, label="No Change")
    ax1.set_xlabel("Rating Change")
    ax1.set_ylabel("Frequency")
    ax1.set_title("White Player Rating Changes")
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend()

    # Black rating changes
    ax2.bar(bin_centers, black_counts, width=bin_width * 0.9, color="#111111", alpha=0.8)
    ax2.axvline(x=0, color="red", linestyle="--", linewidth=1.5, label="No Change")
    ax2.set_xlabel("Rating Change")
    ax2.set_ylabel("Frequency")
    ax2.set_title("Black Player Rating Changes")
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend()

    plt.suptitle("Distribution of Rating Changes per Game", fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def plot_rating_change_violin(
    db_path: str = DB_FILE,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot violin plot of rating changes by result.

    Args:
        db_path: Path to the SQLite database file.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT result, white_rating_diff, black_rating_diff
            FROM game_statistics
            WHERE white_rating_diff IS NOT NULL
              AND black_rating_diff IS NOT NULL
              AND result IN ('1-0', '0-1', '1/2-1/2')
            LIMIT 100000
            """
        )
        rows = cur.fetchall()

    if not rows:
        print("No rating change data found.")
        return

    # Organize data by result
    data_by_result: dict[str, list[float]] = {
        "White Wins\n(1-0)": [],
        "Draw\n(1/2-1/2)": [],
        "Black Wins\n(0-1)": [],
    }

    for result, white_diff, black_diff in rows:
        if result == "1-0":
            data_by_result["White Wins\n(1-0)"].append(white_diff)
        elif result == "0-1":
            data_by_result["Black Wins\n(0-1)"].append(black_diff)
        elif result == "1/2-1/2":
            # For draws, average both players' changes
            data_by_result["Draw\n(1/2-1/2)"].append((white_diff + black_diff) / 2)

    fig, ax = plt.subplots(figsize=(10, 6))

    labels = list(data_by_result.keys())
    data = [data_by_result[k] for k in labels]

    parts = ax.violinplot(data, showmeans=True, showmedians=True)

    # Color the violins
    colors = ["#4CAF50", "#9E9E9E", "#212121"]
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)

    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Rating Change")
    ax.set_title("Rating Changes by Game Result (Winner's Perspective)")
    ax.axhline(y=0, color="red", linestyle="--", alpha=0.5)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot rating change distributions")
    p.add_argument(
        "-b", "--bin-size", type=int, default=2, help="Bin width for histogram (default 2)"
    )
    p.add_argument(
        "--show", action="store_true", help="Display plot in GUI (default: save to file)"
    )
    p.add_argument(
        "-o",
        "--output",
        default="rating_changes.png",
        help="File path to save the histogram plot",
    )
    p.add_argument(
        "--violin-output",
        default="rating_changes_violin.png",
        help="File path to save the violin plot",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    plot_rating_changes(
        db_path=DB_FILE, bin_size=args.bin_size, show=args.show, save_path=args.output
    )
    plot_rating_change_violin(db_path=DB_FILE, show=args.show, save_path=args.violin_output)
