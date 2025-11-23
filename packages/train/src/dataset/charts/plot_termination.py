"""Plot game termination reasons."""

import argparse
import sqlite3

from matplotlib import pyplot as plt

from packages.train.src.constants import DB_FILE


def compute_termination_stats(
    db_path: str = DB_FILE,
) -> tuple[list[str], list[int]]:
    """Compute game counts by termination reason.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        (termination_reasons, counts)
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT termination, COUNT(*) as total
            FROM game_statistics
            WHERE termination IS NOT NULL AND termination != ''
            GROUP BY termination
            ORDER BY COUNT(*) DESC
            """
        )
        rows = cur.fetchall()

    terminations = []
    counts = []
    for term, count in rows:
        terminations.append(term)
        counts.append(count)

    return terminations, counts


def compute_termination_by_elo(
    db_path: str = DB_FILE,
    elo_brackets: list[tuple[int, int]] | None = None,
) -> dict[str, dict[str, int]]:
    """Compute termination counts by ELO bracket.

    Args:
        db_path: Path to the SQLite database file.
        elo_brackets: List of (min_elo, max_elo) tuples.

    Returns:
        Dict mapping bracket label to dict of termination -> count.
    """
    if elo_brackets is None:
        elo_brackets = [
            (600, 1000),
            (1000, 1300),
            (1300, 1600),
            (1600, 1900),
        ]

    results = {}
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        for min_elo, max_elo in elo_brackets:
            label = f"{min_elo}-{max_elo}"
            cur.execute(
                """
                SELECT termination, COUNT(*) as total
                FROM game_statistics
                WHERE termination IS NOT NULL AND termination != ''
                  AND ((white_elo >= ? AND white_elo < ?) OR (black_elo >= ? AND black_elo < ?))
                GROUP BY termination
                ORDER BY COUNT(*) DESC
                """,
                (min_elo, max_elo, min_elo, max_elo),
            )
            results[label] = {row[0]: row[1] for row in cur.fetchall()}

    return results


def plot_termination_pie(
    db_path: str = DB_FILE,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot pie chart of termination reasons.

    Args:
        db_path: Path to the SQLite database file.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    terminations, counts = compute_termination_stats(db_path)

    if not terminations:
        print("No termination data found.")
        return

    # Clean up labels
    label_map = {
        "Normal": "Checkmate/Resignation",
        "Time forfeit": "Time Forfeit",
        "Abandoned": "Abandoned",
        "Rules infraction": "Rules Infraction",
    }
    labels = [label_map.get(t, t) for t in terminations]

    colors = ["#4CAF50", "#F44336", "#9E9E9E", "#FF9800", "#2196F3", "#9C27B0"]

    fig, ax = plt.subplots(figsize=(10, 8))

    # Only show percentage for slices > 2%
    def autopct_func(pct):
        if pct > 2:
            return f"{pct:.1f}%"
        return ""

    wedges, texts, autotexts = ax.pie(
        counts,
        labels=labels,
        autopct=autopct_func,
        colors=colors[: len(labels)],
        explode=[0.02] * len(labels),
        shadow=True,
        startangle=90,
    )

    # Add legend with counts
    legend_labels = [f"{label} ({count:,})" for label, count in zip(labels, counts, strict=False)]
    ax.legend(wedges, legend_labels, loc="lower right", fontsize=9)

    ax.set_title("Game Termination Reasons")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def plot_termination_by_elo(
    db_path: str = DB_FILE,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot stacked bar chart of termination by ELO bracket.

    Args:
        db_path: Path to the SQLite database file.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    data_by_elo = compute_termination_by_elo(db_path)

    if not data_by_elo:
        print("No termination data found.")
        return

    # Get all unique termination types
    all_terminations: set[str] = set()
    for bracket_data in data_by_elo.values():
        all_terminations.update(bracket_data.keys())

    # Sort by overall frequency
    term_totals = {}
    for term in all_terminations:
        term_totals[term] = sum(data_by_elo[bracket].get(term, 0) for bracket in data_by_elo)
    sorted_terminations = sorted(all_terminations, key=lambda t: term_totals[t], reverse=True)

    fig, ax = plt.subplots(figsize=(12, 6))

    brackets = list(data_by_elo.keys())
    x = range(len(brackets))
    width = 0.6

    colors = ["#4CAF50", "#F44336", "#9E9E9E", "#FF9800", "#2196F3", "#9C27B0"]
    bottom: list[float] = [0.0] * len(brackets)

    for i, term in enumerate(sorted_terminations):
        values = []
        for bracket in brackets:
            bracket_total = sum(data_by_elo[bracket].values())
            count = data_by_elo[bracket].get(term, 0)
            pct = 100 * count / bracket_total if bracket_total > 0 else 0
            values.append(pct)

        color = colors[i % len(colors)]
        ax.bar(x, values, width, bottom=bottom, label=term, color=color)
        bottom = [b + v for b, v in zip(bottom, values, strict=False)]

    ax.set_xlabel("ELO Rating Bracket")
    ax.set_ylabel("Percentage (%)")
    ax.set_title("Game Termination by ELO Rating")
    ax.set_xticks(x)
    ax.set_xticklabels(brackets)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_ylim(0, 100)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot game termination statistics")
    p.add_argument(
        "--show", action="store_true", help="Display plot in GUI (default: save to file)"
    )
    p.add_argument(
        "-o",
        "--output",
        default="termination.png",
        help="File path to save the pie chart",
    )
    p.add_argument(
        "--elo-output",
        default="termination_by_elo.png",
        help="File path to save the ELO breakdown plot",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    plot_termination_pie(db_path=DB_FILE, show=args.show, save_path=args.output)
    plot_termination_by_elo(db_path=DB_FILE, show=args.show, save_path=args.elo_output)
