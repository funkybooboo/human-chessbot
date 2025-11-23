"""Dataset visualization charts."""

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

__all__ = [
    # ELO distribution
    "plot_elo_distribution",
    # Opening performance
    "plot_opening_performance",
    # Time control
    "plot_time_control_distribution",
    "plot_time_control_winrates",
    # Rating changes
    "plot_rating_changes",
    "plot_rating_change_violin",
    # Game length
    "plot_game_length_histogram",
    "plot_game_length_by_elo",
    # Termination
    "plot_termination_pie",
    "plot_termination_by_elo",
    # Temporal
    "plot_temporal_overview",
    "plot_games_by_month",
    "plot_games_by_hour",
    "plot_games_by_day_of_week",
]
