"""Generate all charts for the human-chessbot project.

This script generates both dataset visualization charts and training analysis charts.

Usage:
    python -m packages.train.src.charts_main --output-dir charts/
    python -m packages.train.src.charts_main --dataset-only
    python -m packages.train.src.charts_main --training-only -d /path/to/training/dir
"""

import argparse
import os

from packages.train.src.constants import DB_FILE

# Dataset charts
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

# Training charts
from packages.train.src.train.charts.plot_hyperparameters import (
    plot_hyperparameter_comparison,
    plot_hyperparameter_heatmap,
    plot_learning_curves_comparison,
)
from packages.train.src.train.charts.plot_training_analysis import (
    find_models,
    plot_convergence_analysis,
    plot_overfitting_analysis,
    plot_training_summary,
)


def generate_dataset_charts(
    output_dir: str,
    db_path: str = DB_FILE,
    show: bool = False,
) -> list[str]:
    """Generate all dataset visualization charts.

    Args:
        output_dir: Directory to save charts.
        db_path: Path to the SQLite database.
        show: Whether to display plots interactively.

    Returns:
        List of generated file paths.
    """
    dataset_dir = os.path.join(output_dir, "dataset")
    os.makedirs(dataset_dir, exist_ok=True)

    generated = []

    charts = [
        (
            "elo_distribution.png",
            "ELO distribution",
            lambda p: plot_elo_distribution(db_path=db_path, show=show, save_path=p),
        ),
        (
            "opening_performance.png",
            "Opening performance",
            lambda p: plot_opening_performance(db_path=db_path, show=show, save_path=p),
        ),
        (
            "time_control_distribution.png",
            "Time control distribution",
            lambda p: plot_time_control_distribution(db_path=db_path, show=show, save_path=p),
        ),
        (
            "time_control_winrates.png",
            "Time control win rates",
            lambda p: plot_time_control_winrates(db_path=db_path, show=show, save_path=p),
        ),
        (
            "rating_changes.png",
            "Rating changes histogram",
            lambda p: plot_rating_changes(db_path=db_path, show=show, save_path=p),
        ),
        (
            "rating_changes_violin.png",
            "Rating changes violin",
            lambda p: plot_rating_change_violin(db_path=db_path, show=show, save_path=p),
        ),
        (
            "game_length.png",
            "Game length histogram",
            lambda p: plot_game_length_histogram(db_path=db_path, show=show, save_path=p),
        ),
        (
            "game_length_by_elo.png",
            "Game length by ELO",
            lambda p: plot_game_length_by_elo(db_path=db_path, show=show, save_path=p),
        ),
        (
            "termination.png",
            "Termination reasons",
            lambda p: plot_termination_pie(db_path=db_path, show=show, save_path=p),
        ),
        (
            "termination_by_elo.png",
            "Termination by ELO",
            lambda p: plot_termination_by_elo(db_path=db_path, show=show, save_path=p),
        ),
        (
            "temporal_overview.png",
            "Temporal overview",
            lambda p: plot_temporal_overview(db_path=db_path, show=show, save_path=p),
        ),
        (
            "games_by_month.png",
            "Games by month",
            lambda p: plot_games_by_month(db_path=db_path, show=show, save_path=p),
        ),
        (
            "games_by_hour.png",
            "Games by hour",
            lambda p: plot_games_by_hour(db_path=db_path, show=show, save_path=p),
        ),
        (
            "games_by_day.png",
            "Games by day of week",
            lambda p: plot_games_by_day_of_week(db_path=db_path, show=show, save_path=p),
        ),
    ]

    for filename, description, plot_func in charts:
        filepath = os.path.join(dataset_dir, filename)
        print(f"  Generating {description}...")
        try:
            plot_func(filepath)
            generated.append(filepath)
        except Exception as e:
            print(f"    Warning: Failed to generate {filename}: {e}")

    return generated


def generate_training_charts(
    output_dir: str,
    training_dir: str,
    model_name: str | None = None,
    show: bool = False,
) -> list[str]:
    """Generate all training analysis charts.

    Args:
        output_dir: Directory to save charts.
        training_dir: Base training directory containing trained_models/.
        model_name: Specific model to analyze (default: all models).
        show: Whether to display plots interactively.

    Returns:
        List of generated file paths.
    """
    training_output = os.path.join(output_dir, "training")
    os.makedirs(training_output, exist_ok=True)

    generated = []

    # Hyperparameter comparison charts (across all models)
    print("  Generating hyperparameter comparison...")
    try:
        filepath = os.path.join(training_output, "hyperparameter_comparison.png")
        plot_hyperparameter_comparison(training_dir=training_dir, show=show, save_path=filepath)
        generated.append(filepath)
    except Exception as e:
        print(f"    Warning: Failed to generate hyperparameter comparison: {e}")

    print("  Generating learning curves comparison...")
    try:
        filepath = os.path.join(training_output, "learning_curves_comparison.png")
        plot_learning_curves_comparison(training_dir=training_dir, show=show, save_path=filepath)
        generated.append(filepath)
    except Exception as e:
        print(f"    Warning: Failed to generate learning curves: {e}")

    print("  Generating hyperparameter heatmap...")
    try:
        filepath = os.path.join(training_output, "hyperparameter_heatmap.png")
        plot_hyperparameter_heatmap(training_dir=training_dir, show=show, save_path=filepath)
        generated.append(filepath)
    except Exception as e:
        print(f"    Warning: Failed to generate heatmap: {e}")

    # Per-model analysis charts
    models = [model_name] if model_name else find_models(training_dir)

    for model in models:
        model_dir = os.path.join(training_output, model)
        os.makedirs(model_dir, exist_ok=True)

        print(f"  Generating charts for model: {model}")

        try:
            filepath = os.path.join(model_dir, "training_summary.png")
            plot_training_summary(
                training_dir=training_dir, model_name=model, show=show, save_path=filepath
            )
            generated.append(filepath)
        except Exception as e:
            print(f"    Warning: Failed to generate training summary: {e}")

        try:
            filepath = os.path.join(model_dir, "overfitting_analysis.png")
            plot_overfitting_analysis(
                training_dir=training_dir, model_name=model, show=show, save_path=filepath
            )
            generated.append(filepath)
        except Exception as e:
            print(f"    Warning: Failed to generate overfitting analysis: {e}")

        try:
            filepath = os.path.join(model_dir, "convergence_analysis.png")
            plot_convergence_analysis(
                training_dir=training_dir, model_name=model, show=show, save_path=filepath
            )
            generated.append(filepath)
        except Exception as e:
            print(f"    Warning: Failed to generate convergence analysis: {e}")

    return generated


def generate_all_charts(
    output_dir: str = "charts",
    db_path: str = DB_FILE,
    training_dir: str | None = None,
    model_name: str | None = None,
    dataset_only: bool = False,
    training_only: bool = False,
    show: bool = False,
) -> None:
    """Generate all charts for the project.

    Args:
        output_dir: Base output directory for all charts.
        db_path: Path to the SQLite database.
        training_dir: Training directory (for training charts).
        model_name: Specific model to analyze.
        dataset_only: Only generate dataset charts.
        training_only: Only generate training charts.
        show: Whether to display plots interactively.
    """
    os.makedirs(output_dir, exist_ok=True)

    all_generated = []

    # Dataset charts
    if not training_only:
        print("\n" + "=" * 50)
        print("GENERATING DATASET CHARTS")
        print("=" * 50)
        generated = generate_dataset_charts(output_dir, db_path=db_path, show=show)
        all_generated.extend(generated)
        print(f"Generated {len(generated)} dataset charts")

    # Training charts
    if not dataset_only and training_dir:
        print("\n" + "=" * 50)
        print("GENERATING TRAINING CHARTS")
        print("=" * 50)
        generated = generate_training_charts(
            output_dir, training_dir=training_dir, model_name=model_name, show=show
        )
        all_generated.extend(generated)
        print(f"Generated {len(generated)} training charts")

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total charts generated: {len(all_generated)}")
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print("\nGenerated files:")
    for f in sorted(all_generated):
        rel_path = os.path.relpath(f, output_dir)
        print(f"  {rel_path}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate all charts for the human-chessbot project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all dataset charts
  python -m packages.train.src.charts_main --dataset-only

  # Generate all training charts
  python -m packages.train.src.charts_main --training-only -d ./training_output

  # Generate everything
  python -m packages.train.src.charts_main -d ./training_output

  # Generate charts for a specific model
  python -m packages.train.src.charts_main -d ./training_output -m del_lr0.001_decay0.0001_beta0.9_momentum0.999
        """,
    )
    p.add_argument(
        "-o",
        "--output-dir",
        default="charts",
        help="Output directory for all charts (default: charts)",
    )
    p.add_argument(
        "-d",
        "--training-dir",
        default=None,
        help="Training directory containing trained_models/ (required for training charts)",
    )
    p.add_argument(
        "-m",
        "--model",
        default=None,
        help="Specific model name to analyze (default: all models)",
    )
    p.add_argument(
        "--dataset-only",
        action="store_true",
        help="Only generate dataset charts",
    )
    p.add_argument(
        "--training-only",
        action="store_true",
        help="Only generate training charts (requires --training-dir)",
    )
    p.add_argument(
        "--show",
        action="store_true",
        help="Display plots interactively instead of just saving",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    if args.training_only and not args.training_dir:
        print("Error: --training-only requires --training-dir")
        exit(1)

    generate_all_charts(
        output_dir=args.output_dir,
        training_dir=args.training_dir,
        model_name=args.model,
        dataset_only=args.dataset_only,
        training_only=args.training_only,
        show=args.show,
    )
