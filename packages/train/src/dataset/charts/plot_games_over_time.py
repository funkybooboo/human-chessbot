"""Plot games over time (temporal analysis)."""

import argparse
import sqlite3
from collections import defaultdict
from datetime import datetime

from matplotlib import pyplot as plt

from packages.train.src.constants import DB_FILE


def compute_games_by_date(
    db_path: str = DB_FILE,
) -> tuple[list[str], list[int]]:
    """Compute game counts by date.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        (dates, counts)
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT utc_date, COUNT(*) as total
            FROM game_statistics
            WHERE utc_date IS NOT NULL AND utc_date != ''
            GROUP BY utc_date
            ORDER BY utc_date
            """
        )
        rows = cur.fetchall()

    dates = []
    counts = []
    for date, count in rows:
        dates.append(date)
        counts.append(count)

    return dates, counts


def compute_games_by_month(
    db_path: str = DB_FILE,
) -> tuple[list[str], list[int]]:
    """Compute game counts by month.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        (months, counts)
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT substr(utc_date, 1, 7) as month, COUNT(*) as total
            FROM game_statistics
            WHERE utc_date IS NOT NULL AND utc_date != ''
            GROUP BY month
            ORDER BY month
            """
        )
        rows = cur.fetchall()

    months = []
    counts = []
    for month, count in rows:
        months.append(month)
        counts.append(count)

    return months, counts


def compute_games_by_hour(
    db_path: str = DB_FILE,
) -> tuple[list[int], list[int]]:
    """Compute game counts by hour of day (UTC).

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        (hours, counts)
    """
    hour_counts: dict[int, int] = defaultdict(int)

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT utc_time FROM game_statistics
            WHERE utc_time IS NOT NULL AND utc_time != ''
            """
        )

        batch_size = 10_000
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            for (time_str,) in rows:
                try:
                    hour = int(time_str.split(":")[0])
                    hour_counts[hour] += 1
                except (ValueError, IndexError):
                    pass

    hours = list(range(24))
    counts = [hour_counts[h] for h in hours]

    return hours, counts


def compute_games_by_day_of_week(
    db_path: str = DB_FILE,
) -> tuple[list[str], list[int]]:
    """Compute game counts by day of week.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        (day_names, counts)
    """
    day_counts: dict[int, int] = defaultdict(int)
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT utc_date FROM game_statistics
            WHERE utc_date IS NOT NULL AND utc_date != ''
            """
        )

        batch_size = 10_000
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            for (date_str,) in rows:
                try:
                    dt = datetime.strptime(date_str, "%Y.%m.%d")
                    day_counts[dt.weekday()] += 1
                except ValueError:
                    pass

    counts = [day_counts[i] for i in range(7)]

    return day_names, counts


def plot_games_by_month(
    db_path: str = DB_FILE,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot line chart of games by month.

    Args:
        db_path: Path to the SQLite database file.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    months, counts = compute_games_by_month(db_path)

    if not months:
        print("No temporal data found.")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.fill_between(range(len(months)), counts, alpha=0.3, color="#2196F3")
    ax.plot(range(len(months)), counts, color="#2196F3", linewidth=2)

    # Show only some x labels to avoid crowding
    step = max(1, len(months) // 12)
    ax.set_xticks(range(0, len(months), step))
    ax.set_xticklabels([months[i] for i in range(0, len(months), step)], rotation=45, ha="right")

    ax.set_xlabel("Month")
    ax.set_ylabel("Number of Games")
    ax.set_title("Games Processed by Month")
    ax.grid(True, linestyle="--", alpha=0.4)

    # Add cumulative line on secondary axis
    ax2 = ax.twinx()
    cumulative = []
    total = 0
    for c in counts:
        total += c
        cumulative.append(total)
    ax2.plot(
        range(len(months)),
        cumulative,
        color="#F44336",
        linestyle="--",
        linewidth=1.5,
        label="Cumulative",
    )
    ax2.set_ylabel("Cumulative Games", color="#F44336")
    ax2.tick_params(axis="y", labelcolor="#F44336")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def plot_games_by_hour(
    db_path: str = DB_FILE,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot bar chart of games by hour of day.

    Args:
        db_path: Path to the SQLite database file.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    hours, counts = compute_games_by_hour(db_path)

    if sum(counts) == 0:
        print("No hour data found.")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ["#1a237e" if 6 <= h < 18 else "#0d47a1" for h in hours]
    ax.bar(hours, counts, color=colors, alpha=0.8, edgecolor="white")

    ax.set_xlabel("Hour of Day (UTC)")
    ax.set_ylabel("Number of Games")
    ax.set_title("Games by Hour of Day")
    ax.set_xticks(hours)
    ax.set_xticklabels([f"{h:02d}:00" for h in hours], rotation=45, ha="right")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def plot_games_by_day_of_week(
    db_path: str = DB_FILE,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot bar chart of games by day of week.

    Args:
        db_path: Path to the SQLite database file.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    day_names, counts = compute_games_by_day_of_week(db_path)

    if sum(counts) == 0:
        print("No day of week data found.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ["#4CAF50" if i < 5 else "#FF9800" for i in range(7)]
    ax.bar(day_names, counts, color=colors, alpha=0.8, edgecolor="white")

    ax.set_xlabel("Day of Week")
    ax.set_ylabel("Number of Games")
    ax.set_title("Games by Day of Week")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    # Add weekday/weekend labels
    ax.axvline(x=4.5, color="gray", linestyle="--", alpha=0.5)
    ax.text(2, ax.get_ylim()[1] * 0.95, "Weekdays", ha="center", fontsize=10, color="gray")
    ax.text(5.5, ax.get_ylim()[1] * 0.95, "Weekend", ha="center", fontsize=10, color="gray")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def plot_temporal_overview(
    db_path: str = DB_FILE,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot overview of temporal patterns (2x2 grid).

    Args:
        db_path: Path to the SQLite database file.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    months, month_counts = compute_games_by_month(db_path)
    hours, hour_counts = compute_games_by_hour(db_path)
    day_names, day_counts = compute_games_by_day_of_week(db_path)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    # Games by month
    if months:
        ax1.fill_between(range(len(months)), month_counts, alpha=0.3, color="#2196F3")
        ax1.plot(range(len(months)), month_counts, color="#2196F3", linewidth=2)
        step = max(1, len(months) // 6)
        ax1.set_xticks(range(0, len(months), step))
        ax1.set_xticklabels(
            [months[i] for i in range(0, len(months), step)], rotation=45, ha="right"
        )
        ax1.set_title("Games by Month")
        ax1.set_ylabel("Games")
        ax1.grid(True, linestyle="--", alpha=0.4)

    # Games by hour
    if sum(hour_counts) > 0:
        ax2.bar(hours, hour_counts, color="#1a237e", alpha=0.8)
        ax2.set_xticks(range(0, 24, 3))
        ax2.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 3)])
        ax2.set_title("Games by Hour (UTC)")
        ax2.set_ylabel("Games")
        ax2.grid(True, axis="y", linestyle="--", alpha=0.4)

    # Games by day of week
    if sum(day_counts) > 0:
        colors = ["#4CAF50" if i < 5 else "#FF9800" for i in range(7)]
        ax3.bar(range(7), day_counts, color=colors, alpha=0.8)
        ax3.set_xticks(range(7))
        ax3.set_xticklabels([d[:3] for d in day_names])
        ax3.set_title("Games by Day of Week")
        ax3.set_ylabel("Games")
        ax3.grid(True, axis="y", linestyle="--", alpha=0.4)

    # Cumulative games
    if months:
        cumulative = []
        total = 0
        for c in month_counts:
            total += c
            cumulative.append(total)
        ax4.plot(range(len(months)), cumulative, color="#F44336", linewidth=2)
        ax4.fill_between(range(len(months)), cumulative, alpha=0.2, color="#F44336")
        step = max(1, len(months) // 6)
        ax4.set_xticks(range(0, len(months), step))
        ax4.set_xticklabels(
            [months[i] for i in range(0, len(months), step)], rotation=45, ha="right"
        )
        ax4.set_title("Cumulative Games")
        ax4.set_ylabel("Total Games")
        ax4.grid(True, linestyle="--", alpha=0.4)

    plt.suptitle("Temporal Analysis of Chess Games", fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot temporal game statistics")
    p.add_argument(
        "--show", action="store_true", help="Display plot in GUI (default: save to file)"
    )
    p.add_argument(
        "-o",
        "--output",
        default="games_over_time.png",
        help="File path to save the overview plot",
    )
    p.add_argument(
        "--month-output",
        default="games_by_month.png",
        help="File path to save monthly plot",
    )
    p.add_argument(
        "--hour-output",
        default="games_by_hour.png",
        help="File path to save hourly plot",
    )
    p.add_argument(
        "--day-output",
        default="games_by_day.png",
        help="File path to save day of week plot",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    plot_temporal_overview(db_path=DB_FILE, show=args.show, save_path=args.output)
    plot_games_by_month(db_path=DB_FILE, show=args.show, save_path=args.month_output)
    plot_games_by_hour(db_path=DB_FILE, show=args.show, save_path=args.hour_output)
    plot_games_by_day_of_week(db_path=DB_FILE, show=args.show, save_path=args.day_output)
