"""Generate all dataset charts at once."""

import argparse
import os

from packages.train.src.constants import DB_FILE
from packages.train.src.dataset.charts.plot_elo_distribution import plot_elo_distribution
from packages.train.src.dataset.charts.plot_game_length import (
    plot_game_length_by_elo,
    plot_game_length_histogram,
)
from packages.train.src.dataset.charts.plot_games_over_time import (
    plot_games_by_day_of_week,
    plot_games_by_hour,
    plot_games_by_month,
    plot_temporal_overview,
)
from packages.train.src.dataset.charts.plot_opening_performance import plot_opening_performance
from packages.train.src.dataset.charts.plot_rating_changes import (
    plot_rating_change_violin,
    plot_rating_changes,
)
from packages.train.src.dataset.charts.plot_termination import (
    plot_termination_by_elo,
    plot_termination_pie,
)
from packages.train.src.dataset.charts.plot_time_control import (
    plot_time_control_distribution,
    plot_time_control_winrates,
)


def generate_all_charts(
    output_dir: str = "charts",
    db_path: str = DB_FILE,
    show: bool = False,
) -> None:
    """Generate all dataset visualization charts.

    Args:
        output_dir: Directory to save charts.
        db_path: Path to the SQLite database.
        show: Whether to display plots interactively.
    """
    os.makedirs(output_dir, exist_ok=True)

    print("Generating dataset charts...")

    # ELO Distribution
    print("  - ELO distribution...")
    plot_elo_distribution(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "elo_distribution.png"),
    )

    # Opening Performance
    print("  - Opening performance...")
    plot_opening_performance(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "opening_performance.png"),
    )

    # Time Control
    print("  - Time control distribution...")
    plot_time_control_distribution(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "time_control_distribution.png"),
    )
    print("  - Time control win rates...")
    plot_time_control_winrates(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "time_control_winrates.png"),
    )

    # Rating Changes
    print("  - Rating changes histogram...")
    plot_rating_changes(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "rating_changes.png"),
    )
    print("  - Rating changes violin...")
    plot_rating_change_violin(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "rating_changes_violin.png"),
    )

    # Game Length
    print("  - Game length histogram...")
    plot_game_length_histogram(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "game_length.png"),
    )
    print("  - Game length by ELO...")
    plot_game_length_by_elo(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "game_length_by_elo.png"),
    )

    # Termination
    print("  - Termination pie chart...")
    plot_termination_pie(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "termination.png"),
    )
    print("  - Termination by ELO...")
    plot_termination_by_elo(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "termination_by_elo.png"),
    )

    # Temporal
    print("  - Temporal overview...")
    plot_temporal_overview(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "games_over_time.png"),
    )
    print("  - Games by month...")
    plot_games_by_month(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "games_by_month.png"),
    )
    print("  - Games by hour...")
    plot_games_by_hour(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "games_by_hour.png"),
    )
    print("  - Games by day of week...")
    plot_games_by_day_of_week(
        db_path=db_path,
        show=show,
        save_path=os.path.join(output_dir, "games_by_day.png"),
    )

    print(f"\nAll charts saved to: {output_dir}/")
    print("Generated files:")
    for f in sorted(os.listdir(output_dir)):
        if f.endswith(".png"):
            print(f"  - {f}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate all dataset charts")
    p.add_argument(
        "-o",
        "--output-dir",
        default="charts",
        help="Output directory for charts (default: charts)",
    )
    p.add_argument(
        "--show",
        action="store_true",
        help="Display plots interactively",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    generate_all_charts(output_dir=args.output_dir, show=args.show)
