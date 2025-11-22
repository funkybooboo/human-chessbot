"""Plot hyperparameter search results and comparisons."""

import argparse
import os

import pandas as pd
from matplotlib import pyplot as plt

from packages.train.src.constants import (
    CHECK_POINT_INFO_FILE_NAME,
    EPOCH_INFO_FILE_NAME,
    FINAL_SAVES_DIR,
)


def parse_model_name(model_name: str) -> dict[str, float]:
    """Parse hyperparameters from model directory name.

    Expected format: del_lr{lr}_decay{decay}_beta{beta}_momentum{momentum}

    Args:
        model_name: Directory name containing hyperparameters.

    Returns:
        Dict with lr, decay, beta, momentum values.
    """
    params = {}
    try:
        parts = model_name.replace("del_", "").split("_")
        for part in parts:
            if part.startswith("lr"):
                params["lr"] = float(part[2:])
            elif part.startswith("decay"):
                params["decay"] = float(part[5:])
            elif part.startswith("beta"):
                params["beta"] = float(part[4:])
            elif part.startswith("momentum"):
                params["momentum"] = float(part[8:])
    except (ValueError, IndexError):
        pass
    return params


def load_all_training_runs(training_dir: str) -> pd.DataFrame:
    """Load training metrics from all model directories.

    Args:
        training_dir: Base training directory.

    Returns:
        DataFrame with columns: model_name, lr, decay, beta, momentum,
                               final_train_loss, final_val_loss, final_train_acc, final_val_acc
    """
    final_saves = os.path.join(training_dir, FINAL_SAVES_DIR)
    if not os.path.exists(final_saves):
        return pd.DataFrame()

    records = []
    for model_dir in os.listdir(final_saves):
        model_path = os.path.join(final_saves, model_dir)
        if not os.path.isdir(model_path):
            continue

        # Parse hyperparameters from name
        params = parse_model_name(model_dir)
        if not params:
            continue

        # Load final metrics from saves.csv
        saves_path = os.path.join(model_path, CHECK_POINT_INFO_FILE_NAME)
        if os.path.exists(saves_path):
            try:
                df = pd.read_csv(saves_path)
                if len(df) > 0:
                    last_row = df.iloc[-1]
                    records.append(
                        {
                            "model_name": model_dir,
                            "lr": params.get("lr"),
                            "decay": params.get("decay"),
                            "beta": params.get("beta"),
                            "momentum": params.get("momentum"),
                            "final_train_loss": last_row.get("train_loss"),
                            "final_val_loss": last_row.get("val_loss"),
                            "final_train_acc": last_row.get("train_accuracy"),
                            "final_val_acc": last_row.get("val_accuracy"),
                        }
                    )
            except Exception:
                pass

    return pd.DataFrame(records)


def plot_hyperparameter_comparison(
    training_dir: str,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot comparison of validation loss across hyperparameter configurations.

    Args:
        training_dir: Base training directory.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    df = load_all_training_runs(training_dir)

    if df.empty:
        print("No training runs found.")
        return

    # Sort by validation loss
    df = df.sort_values("final_val_loss")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Validation loss by learning rate
    ax1 = axes[0, 0]
    if "lr" in df.columns and df["lr"].notna().any():
        ax1.scatter(df["lr"], df["final_val_loss"], c=df["final_val_acc"], cmap="viridis", s=100)
        ax1.set_xlabel("Learning Rate")
        ax1.set_ylabel("Final Validation Loss")
        ax1.set_title("Val Loss vs Learning Rate")
        ax1.set_xscale("log")
        ax1.grid(True, linestyle="--", alpha=0.4)

    # Plot 2: Validation loss by decay rate
    ax2 = axes[0, 1]
    if "decay" in df.columns and df["decay"].notna().any():
        ax2.scatter(df["decay"], df["final_val_loss"], c=df["final_val_acc"], cmap="viridis", s=100)
        ax2.set_xlabel("Weight Decay")
        ax2.set_ylabel("Final Validation Loss")
        ax2.set_title("Val Loss vs Weight Decay")
        ax2.set_xscale("log")
        ax2.grid(True, linestyle="--", alpha=0.4)

    # Plot 3: Best models bar chart
    ax3 = axes[1, 0]
    top_n = min(10, len(df))
    top_df = df.head(top_n)
    y_pos = range(top_n)
    ax3.barh(y_pos, top_df["final_val_loss"], color="#2196F3", alpha=0.8)
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels([f"lr={row['lr']:.0e}" for _, row in top_df.iterrows()], fontsize=8)
    ax3.set_xlabel("Validation Loss")
    ax3.set_title(f"Top {top_n} Models by Validation Loss")
    ax3.grid(True, axis="x", linestyle="--", alpha=0.4)

    # Plot 4: Train vs Val loss (overfitting indicator)
    ax4 = axes[1, 1]
    ax4.scatter(df["final_train_loss"], df["final_val_loss"], c=df["lr"], cmap="plasma", s=100)
    # Add diagonal line (no overfitting reference)
    lims = [
        min(df["final_train_loss"].min(), df["final_val_loss"].min()),
        max(df["final_train_loss"].max(), df["final_val_loss"].max()),
    ]
    ax4.plot(lims, lims, "r--", alpha=0.5, label="No overfit")
    ax4.set_xlabel("Final Training Loss")
    ax4.set_ylabel("Final Validation Loss")
    ax4.set_title("Train vs Val Loss (Overfitting Check)")
    ax4.legend()
    ax4.grid(True, linestyle="--", alpha=0.4)

    plt.suptitle("Hyperparameter Search Results", fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def plot_learning_curves_comparison(
    training_dir: str,
    top_n: int = 5,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot learning curves for top N models.

    Args:
        training_dir: Base training directory.
        top_n: Number of top models to plot.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    df = load_all_training_runs(training_dir)

    if df.empty:
        print("No training runs found.")
        return

    # Get top N models by validation loss
    df = df.sort_values("final_val_loss").head(top_n)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    colors = plt.cm.tab10(range(top_n))

    final_saves = os.path.join(training_dir, FINAL_SAVES_DIR)

    for i, (_, row) in enumerate(df.iterrows()):
        model_name = row["model_name"]
        epoch_path = os.path.join(final_saves, model_name, EPOCH_INFO_FILE_NAME)

        if not os.path.exists(epoch_path):
            continue

        try:
            epoch_df = pd.read_csv(epoch_path)
            label = f"lr={row['lr']:.0e}"

            ax1.plot(
                epoch_df["epoch"], epoch_df["val_loss"], color=colors[i], label=label, linewidth=2
            )
            ax2.plot(
                epoch_df["epoch"],
                epoch_df["val_accuracy"],
                color=colors[i],
                label=label,
                linewidth=2,
            )
        except Exception:
            pass

    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Validation Loss")
    ax1.set_title("Validation Loss Over Epochs")
    ax1.legend(fontsize=8)
    ax1.grid(True, linestyle="--", alpha=0.4)

    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Validation Accuracy (%)")
    ax2.set_title("Validation Accuracy Over Epochs")
    ax2.legend(fontsize=8)
    ax2.grid(True, linestyle="--", alpha=0.4)

    plt.suptitle(f"Learning Curves for Top {top_n} Models", fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def plot_hyperparameter_heatmap(
    training_dir: str,
    x_param: str = "lr",
    y_param: str = "decay",
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot heatmap of validation loss for two hyperparameters.

    Args:
        training_dir: Base training directory.
        x_param: Parameter for x-axis (lr, decay, beta, momentum).
        y_param: Parameter for y-axis (lr, decay, beta, momentum).
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    df = load_all_training_runs(training_dir)

    if df.empty:
        print("No training runs found.")
        return

    if x_param not in df.columns or y_param not in df.columns:
        print(f"Parameters {x_param} or {y_param} not found.")
        return

    fig, ax = plt.subplots(figsize=(10, 8))

    scatter = ax.scatter(
        df[x_param],
        df[y_param],
        c=df["final_val_loss"],
        cmap="RdYlGn_r",
        s=200,
        edgecolors="black",
        linewidth=1,
    )

    ax.set_xlabel(x_param.upper())
    ax.set_ylabel(y_param.upper())
    ax.set_title(f"Validation Loss by {x_param.upper()} and {y_param.upper()}")

    if df[x_param].max() / df[x_param].min() > 10:
        ax.set_xscale("log")
    if df[y_param].max() / df[y_param].min() > 10:
        ax.set_yscale("log")

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Validation Loss")

    ax.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot hyperparameter search results")
    p.add_argument(
        "-d",
        "--training-dir",
        default=".",
        help="Base training directory (default: current directory)",
    )
    p.add_argument(
        "-n", "--top-n", type=int, default=5, help="Number of top models to compare (default 5)"
    )
    p.add_argument(
        "--show", action="store_true", help="Display plot in GUI (default: save to file)"
    )
    p.add_argument(
        "-o",
        "--output",
        default="hyperparameter_comparison.png",
        help="File path to save comparison plot",
    )
    p.add_argument(
        "--curves-output",
        default="learning_curves_comparison.png",
        help="File path to save learning curves plot",
    )
    p.add_argument(
        "--heatmap-output",
        default="hyperparameter_heatmap.png",
        help="File path to save heatmap plot",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    plot_hyperparameter_comparison(
        training_dir=args.training_dir, show=args.show, save_path=args.output
    )
    plot_learning_curves_comparison(
        training_dir=args.training_dir,
        top_n=args.top_n,
        show=args.show,
        save_path=args.curves_output,
    )
    plot_hyperparameter_heatmap(
        training_dir=args.training_dir, show=args.show, save_path=args.heatmap_output
    )
