"""Plot game length (total moves) distributions."""

import argparse
import sqlite3

from matplotlib import pyplot as plt

from packages.train.src.constants import DB_FILE, MAX_ELO, MIN_ELO


def compute_game_length_histogram(
    db_path: str = DB_FILE,
    bin_size: int = 5,
    max_moves: int = 150,
) -> tuple[list[int], list[float]]:
    """Compute histogram of game lengths.

    Args:
        db_path: Path to the SQLite database file.
        bin_size: Width of each bin (number of moves).
        max_moves: Maximum moves to include.

    Returns:
        (counts, bin_edges)
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()

        bins = max_moves // bin_size
        bin_edges = [float(i * bin_size) for i in range(bins + 1)]
        counts = [0] * bins

        cur.execute(
            """
            SELECT total_moves FROM game_statistics
            WHERE total_moves IS NOT NULL
            """
        )

        batch_size = 10_000
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            for (moves,) in rows:
                if moves is not None:
                    idx = min(moves // bin_size, bins - 1)
                    if idx >= 0:
                        counts[idx] += 1

    return counts, bin_edges


def compute_game_length_by_elo(
    db_path: str = DB_FILE,
    elo_brackets: list[tuple[int, int]] | None = None,
) -> dict[str, list[int]]:
    """Compute game lengths grouped by ELO bracket.

    Args:
        db_path: Path to the SQLite database file.
        elo_brackets: List of (min_elo, max_elo) tuples.

    Returns:
        Dict mapping bracket label to list of game lengths.
    """
    if elo_brackets is None:
        elo_brackets = [
            (MIN_ELO, 1000),
            (1000, 1200),
            (1200, 1400),
            (1400, 1600),
            (1600, MAX_ELO),
        ]

    results = {}
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        for min_elo, max_elo in elo_brackets:
            label = f"{min_elo}-{max_elo}"
            cur.execute(
                """
                SELECT total_moves FROM game_statistics
                WHERE total_moves IS NOT NULL
                  AND ((white_elo >= ? AND white_elo < ?) OR (black_elo >= ? AND black_elo < ?))
                LIMIT 50000
                """,
                (min_elo, max_elo, min_elo, max_elo),
            )
            results[label] = [row[0] for row in cur.fetchall()]

    return results


def plot_game_length_histogram(
    db_path: str = DB_FILE,
    bin_size: int = 5,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot histogram of game lengths.

    Args:
        db_path: Path to the SQLite database file.
        bin_size: Width of each bin.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    counts, bin_edges = compute_game_length_histogram(db_path=db_path, bin_size=bin_size)

    if not counts or sum(counts) == 0:
        print("No game length data found.")
        return

    bin_count = len(bin_edges) - 1
    bin_width = bin_edges[1] - bin_edges[0]
    bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2.0 for i in range(bin_count)]

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(
        bin_centers, counts, width=bin_width * 0.9, color="#2196F3", alpha=0.8, edgecolor="white"
    )

    # Add mean line
    total_games = sum(counts)
    weighted_sum = sum(c * center for c, center in zip(counts, bin_centers, strict=False))
    mean_length = weighted_sum / total_games if total_games > 0 else 0

    ax.axvline(
        x=mean_length,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {mean_length:.1f} moves",
    )

    ax.set_xlabel("Number of Moves")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Game Lengths")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def plot_game_length_by_elo(
    db_path: str = DB_FILE,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot box plot of game lengths by ELO bracket.

    Args:
        db_path: Path to the SQLite database file.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    data_by_elo = compute_game_length_by_elo(db_path)

    if not data_by_elo or all(len(v) == 0 for v in data_by_elo.values()):
        print("No game length data found.")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    labels = list(data_by_elo.keys())
    data = [data_by_elo[k] for k in labels]

    bp = ax.boxplot(data, labels=labels, patch_artist=True)

    # Color the boxes
    colors = ["#FF5722", "#FF9800", "#FFC107", "#8BC34A", "#4CAF50"]
    for patch, color in zip(bp["boxes"], colors, strict=False):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xlabel("ELO Rating Bracket")
    ax.set_ylabel("Number of Moves")
    ax.set_title("Game Length Distribution by ELO Rating")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    # Add sample sizes
    for i, (_label, values) in enumerate(data_by_elo.items()):
        ax.annotate(
            f"n={len(values):,}",
            xy=(i + 1, ax.get_ylim()[1]),
            ha="center",
            va="bottom",
            fontsize=8,
        )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot game length distributions")
    p.add_argument(
        "-b", "--bin-size", type=int, default=5, help="Bin width for histogram (default 5)"
    )
    p.add_argument(
        "--show", action="store_true", help="Display plot in GUI (default: save to file)"
    )
    p.add_argument(
        "-o",
        "--output",
        default="game_length.png",
        help="File path to save the histogram plot",
    )
    p.add_argument(
        "--elo-output",
        default="game_length_by_elo.png",
        help="File path to save the ELO breakdown plot",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    plot_game_length_histogram(
        db_path=DB_FILE, bin_size=args.bin_size, show=args.show, save_path=args.output
    )
    plot_game_length_by_elo(db_path=DB_FILE, show=args.show, save_path=args.elo_output)
