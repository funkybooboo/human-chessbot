"""Plot game distribution and win rates by time control."""

import argparse
import sqlite3

from matplotlib import pyplot as plt

from packages.train.src.constants import DB_FILE


def compute_time_control_stats(
    db_path: str = DB_FILE,
) -> tuple[list[str], list[int], list[float], list[float], list[float]]:
    """Compute game counts and win rates by time control.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        (time_controls, game_counts, white_win_rates, draw_rates, black_win_rates)
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT time_control,
                   COUNT(*) as total,
                   SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) as white_wins,
                   SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                   SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) as black_wins
            FROM game_statistics
            WHERE time_control IS NOT NULL AND time_control != ''
            GROUP BY time_control
            ORDER BY COUNT(*) DESC
            """
        )
        rows = cur.fetchall()

    time_controls = []
    game_counts = []
    white_win_rates = []
    draw_rates = []
    black_win_rates = []

    for tc, total, white_wins, draws, black_wins in rows:
        time_controls.append(tc)
        game_counts.append(total)
        white_win_rates.append(100 * white_wins / total if total > 0 else 0)
        draw_rates.append(100 * draws / total if total > 0 else 0)
        black_win_rates.append(100 * black_wins / total if total > 0 else 0)

    return time_controls, game_counts, white_win_rates, draw_rates, black_win_rates


def _categorize_time_control(tc: str) -> str:
    """Categorize a time control string into bullet/blitz/rapid/classical."""
    try:
        # Parse formats like "300+0" or "180+2"
        if "+" in tc:
            base, inc = tc.split("+")
            base_seconds = int(base)
            increment = int(inc)
        else:
            base_seconds = int(tc)
            increment = 0

        # Estimated game time = base + 40 * increment
        estimated_time = base_seconds + 40 * increment

        if estimated_time < 180:
            return "Bullet"
        elif estimated_time < 600:
            return "Blitz"
        elif estimated_time < 1800:
            return "Rapid"
        else:
            return "Classical"
    except (ValueError, TypeError):
        return "Other"


def compute_categorized_stats(
    db_path: str = DB_FILE,
) -> tuple[list[str], list[int], list[float], list[float], list[float]]:
    """Compute stats grouped by time control category."""
    time_controls, counts, white_rates, draw_rates, black_rates = compute_time_control_stats(
        db_path
    )

    categories: dict[str, dict] = {}
    for tc, count, wr, dr, br in zip(
        time_controls, counts, white_rates, draw_rates, black_rates, strict=False
    ):
        cat = _categorize_time_control(tc)
        if cat not in categories:
            categories[cat] = {
                "count": 0,
                "white_wins": 0,
                "draws": 0,
                "black_wins": 0,
            }
        categories[cat]["count"] += count
        categories[cat]["white_wins"] += count * wr / 100
        categories[cat]["draws"] += count * dr / 100
        categories[cat]["black_wins"] += count * br / 100

    cat_names = []
    cat_counts = []
    cat_white = []
    cat_draw = []
    cat_black = []

    for cat in ["Bullet", "Blitz", "Rapid", "Classical", "Other"]:
        if cat in categories:
            data = categories[cat]
            total = data["count"]
            cat_names.append(cat)
            cat_counts.append(total)
            cat_white.append(100 * data["white_wins"] / total if total > 0 else 0)
            cat_draw.append(100 * data["draws"] / total if total > 0 else 0)
            cat_black.append(100 * data["black_wins"] / total if total > 0 else 0)

    return cat_names, cat_counts, cat_white, cat_draw, cat_black


def plot_time_control_distribution(
    db_path: str = DB_FILE,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot pie chart of games by time control category.

    Args:
        db_path: Path to the SQLite database file.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    cat_names, cat_counts, _, _, _ = compute_categorized_stats(db_path)

    if not cat_names:
        print("No time control data found.")
        return

    colors = ["#FF5722", "#2196F3", "#4CAF50", "#9C27B0", "#607D8B"]

    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(
        cat_counts,
        labels=cat_names,
        autopct=lambda p: f"{p:.1f}%\n({int(p * sum(cat_counts) / 100):,})",
        colors=colors[: len(cat_names)],
        explode=[0.02] * len(cat_names),
        shadow=True,
    )

    for autotext in autotexts:
        autotext.set_fontsize(9)

    ax.set_title("Game Distribution by Time Control Category")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def plot_time_control_winrates(
    db_path: str = DB_FILE,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot win rates by time control category.

    Args:
        db_path: Path to the SQLite database file.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    cat_names, cat_counts, white_rates, draw_rates, black_rates = compute_categorized_stats(db_path)

    if not cat_names:
        print("No time control data found.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(cat_names))
    width = 0.25

    ax.bar([i - width for i in x], white_rates, width, label="White Wins", color="#4CAF50")
    ax.bar(x, draw_rates, width, label="Draws", color="#9E9E9E")
    ax.bar([i + width for i in x], black_rates, width, label="Black Wins", color="#212121")

    ax.set_xlabel("Time Control Category")
    ax.set_ylabel("Percentage (%)")
    ax.set_title("Win Rates by Time Control Category")
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{name}\n(n={count:,})" for name, count in zip(cat_names, cat_counts, strict=False)]
    )
    ax.legend()
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot time control statistics")
    p.add_argument(
        "--show", action="store_true", help="Display plot in GUI (default: save to file)"
    )
    p.add_argument(
        "-o",
        "--output",
        default="time_control_distribution.png",
        help="File path to save distribution plot",
    )
    p.add_argument(
        "--winrates-output",
        default="time_control_winrates.png",
        help="File path to save win rates plot",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    plot_time_control_distribution(db_path=DB_FILE, show=args.show, save_path=args.output)
    plot_time_control_winrates(db_path=DB_FILE, show=args.show, save_path=args.winrates_output)
