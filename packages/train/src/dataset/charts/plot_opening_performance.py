"""Plot win rates by opening (ECO code)."""

import argparse
import sqlite3

from matplotlib import pyplot as plt

from packages.train.src.constants import DB_FILE


def compute_opening_stats(
    db_path: str = DB_FILE,
    min_games: int = 100,
) -> tuple[list[str], list[float], list[float], list[float], list[int]]:
    """Compute win/draw/loss rates by ECO code.

    Args:
        db_path: Path to the SQLite database file.
        min_games: Minimum games required for an opening to be included.

    Returns:
        (eco_codes, white_win_rates, draw_rates, black_win_rates, game_counts)
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT eco,
                   COUNT(*) as total,
                   SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) as white_wins,
                   SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                   SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) as black_wins
            FROM game_statistics
            WHERE eco IS NOT NULL AND eco != ''
            GROUP BY eco
            HAVING COUNT(*) >= ?
            ORDER BY COUNT(*) DESC
            """,
            (min_games,),
        )
        rows = cur.fetchall()

    eco_codes = []
    white_win_rates = []
    draw_rates = []
    black_win_rates = []
    game_counts = []

    for eco, total, white_wins, draws, black_wins in rows:
        eco_codes.append(eco)
        white_win_rates.append(100 * white_wins / total)
        draw_rates.append(100 * draws / total)
        black_win_rates.append(100 * black_wins / total)
        game_counts.append(total)

    return eco_codes, white_win_rates, draw_rates, black_win_rates, game_counts


def plot_opening_performance(
    db_path: str = DB_FILE,
    min_games: int = 100,
    top_n: int = 20,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot win rates by opening ECO code.

    Args:
        db_path: Path to the SQLite database file.
        min_games: Minimum games for an opening to be included.
        top_n: Number of top openings to display.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    eco_codes, white_wins, draws, black_wins, counts = compute_opening_stats(
        db_path=db_path, min_games=min_games
    )

    if not eco_codes:
        print("No opening data found.")
        return

    # Take top N openings by game count
    eco_codes = eco_codes[:top_n]
    white_wins = white_wins[:top_n]
    draws = draws[:top_n]
    black_wins = black_wins[:top_n]
    counts = counts[:top_n]

    # Reverse for horizontal bar chart (top at top)
    eco_codes = eco_codes[::-1]
    white_wins = white_wins[::-1]
    draws = draws[::-1]
    black_wins = black_wins[::-1]
    counts = counts[::-1]

    fig, ax = plt.subplots(figsize=(12, 8))

    y_pos = range(len(eco_codes))
    bar_height = 0.8

    # Stacked horizontal bar chart
    ax.barh(y_pos, white_wins, bar_height, label="White Wins", color="#4CAF50")
    ax.barh(y_pos, draws, bar_height, left=white_wins, label="Draws", color="#9E9E9E")
    ax.barh(
        y_pos,
        black_wins,
        bar_height,
        left=[w + d for w, d in zip(white_wins, draws, strict=False)],
        label="Black Wins",
        color="#212121",
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{eco} (n={c:,})" for eco, c in zip(eco_codes, counts, strict=False)])
    ax.set_xlabel("Percentage (%)")
    ax.set_title(f"Win Rates by Opening (Top {len(eco_codes)} by Game Count)")
    ax.legend(loc="lower right")
    ax.set_xlim(0, 100)
    ax.grid(True, axis="x", linestyle="--", alpha=0.4)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot win rates by opening ECO code")
    p.add_argument(
        "-n", "--top-n", type=int, default=20, help="Number of top openings to show (default 20)"
    )
    p.add_argument(
        "-m",
        "--min-games",
        type=int,
        default=100,
        help="Minimum games for inclusion (default 100)",
    )
    p.add_argument(
        "--show", action="store_true", help="Display plot in GUI (default: save to file)"
    )
    p.add_argument(
        "-o",
        "--output",
        default="opening_performance.png",
        help="File path to save the plot (default: opening_performance.png)",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    plot_opening_performance(
        db_path=DB_FILE,
        min_games=args.min_games,
        top_n=args.top_n,
        show=args.show,
        save_path=args.output,
    )
