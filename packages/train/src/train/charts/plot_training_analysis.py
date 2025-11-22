"""Advanced training analysis charts including overfitting detection."""

import argparse
import os

import pandas as pd
from matplotlib import pyplot as plt

from packages.train.src.constants import (
    CHECK_POINT_INFO_FILE_NAME,
    EPOCH_INFO_FILE_NAME,
    FINAL_SAVES_DIR,
)


def load_training_data(
    training_dir: str, model_name: str
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Load epoch and save data for a model.

    Args:
        training_dir: Base training directory.
        model_name: Name of the model directory.

    Returns:
        Tuple of (epoch_df, saves_df) or (None, None) if not found.
    """
    model_path = os.path.join(training_dir, FINAL_SAVES_DIR, model_name)

    epoch_df = None
    saves_df = None

    epoch_path = os.path.join(model_path, EPOCH_INFO_FILE_NAME)
    if os.path.exists(epoch_path):
        epoch_df = pd.read_csv(epoch_path)

    saves_path = os.path.join(model_path, CHECK_POINT_INFO_FILE_NAME)
    if os.path.exists(saves_path):
        saves_df = pd.read_csv(saves_path)
        if "time_stamp" in saves_df.columns:
            saves_df["timestamp"] = pd.to_datetime(saves_df["time_stamp"], format="%Y%m%d-%H%M%S")

    return epoch_df, saves_df


def plot_overfitting_analysis(
    training_dir: str,
    model_name: str,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot overfitting analysis showing train/val gap over time.

    Args:
        training_dir: Base training directory.
        model_name: Name of the model to analyze.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    epoch_df, _ = load_training_data(training_dir, model_name)

    if epoch_df is None or epoch_df.empty:
        print(f"No epoch data found for model: {model_name}")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Loss curves with gap shading
    ax1 = axes[0, 0]
    ax1.plot(
        epoch_df["epoch"], epoch_df["train_loss"], label="Train Loss", color="#2196F3", linewidth=2
    )
    ax1.plot(
        epoch_df["epoch"], epoch_df["val_loss"], label="Val Loss", color="#F44336", linewidth=2
    )
    ax1.fill_between(
        epoch_df["epoch"],
        epoch_df["train_loss"],
        epoch_df["val_loss"],
        alpha=0.2,
        color="#FF9800",
        label="Generalization Gap",
    )
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.set_title("Loss with Generalization Gap")
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.4)

    # Plot 2: Gap over time
    ax2 = axes[0, 1]
    gap = epoch_df["val_loss"] - epoch_df["train_loss"]
    colors = ["#4CAF50" if g < gap.mean() else "#F44336" for g in gap]
    ax2.bar(epoch_df["epoch"], gap, color=colors, alpha=0.8)
    ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax2.axhline(y=gap.mean(), color="orange", linestyle="--", label=f"Mean Gap: {gap.mean():.4f}")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Val Loss - Train Loss")
    ax2.set_title("Generalization Gap Over Epochs")
    ax2.legend()
    ax2.grid(True, axis="y", linestyle="--", alpha=0.4)

    # Plot 3: Accuracy curves
    ax3 = axes[1, 0]
    ax3.plot(
        epoch_df["epoch"],
        epoch_df["train_accuracy"],
        label="Train Accuracy",
        color="#2196F3",
        linewidth=2,
    )
    ax3.plot(
        epoch_df["epoch"],
        epoch_df["val_accuracy"],
        label="Val Accuracy",
        color="#F44336",
        linewidth=2,
    )
    ax3.set_xlabel("Epoch")
    ax3.set_ylabel("Accuracy (%)")
    ax3.set_title("Accuracy Over Epochs")
    ax3.legend()
    ax3.grid(True, linestyle="--", alpha=0.4)

    # Plot 4: Learning rate decay effectiveness (loss improvement per epoch)
    ax4 = axes[1, 1]
    if len(epoch_df) > 1:
        loss_improvement = -epoch_df["val_loss"].diff()
        ax4.bar(epoch_df["epoch"][1:], loss_improvement[1:], color="#9C27B0", alpha=0.8)
        ax4.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
        ax4.set_xlabel("Epoch")
        ax4.set_ylabel("Val Loss Improvement")
        ax4.set_title("Validation Loss Improvement per Epoch")
        ax4.grid(True, axis="y", linestyle="--", alpha=0.4)

    plt.suptitle(f"Overfitting Analysis: {model_name}", fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def plot_convergence_analysis(
    training_dir: str,
    model_name: str,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot convergence analysis with smoothed curves and early stopping indicators.

    Args:
        training_dir: Base training directory.
        model_name: Name of the model to analyze.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    epoch_df, _ = load_training_data(training_dir, model_name)

    if epoch_df is None or epoch_df.empty:
        print(f"No epoch data found for model: {model_name}")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Smoothed loss curves (exponential moving average)
    window = min(5, len(epoch_df) // 3) if len(epoch_df) > 3 else 1
    if window > 1:
        epoch_df["train_loss_smooth"] = epoch_df["train_loss"].ewm(span=window).mean()
        epoch_df["val_loss_smooth"] = epoch_df["val_loss"].ewm(span=window).mean()
    else:
        epoch_df["train_loss_smooth"] = epoch_df["train_loss"]
        epoch_df["val_loss_smooth"] = epoch_df["val_loss"]

    ax1.plot(
        epoch_df["epoch"], epoch_df["train_loss"], alpha=0.3, color="#2196F3", label="Train (raw)"
    )
    ax1.plot(epoch_df["epoch"], epoch_df["val_loss"], alpha=0.3, color="#F44336", label="Val (raw)")
    ax1.plot(
        epoch_df["epoch"],
        epoch_df["train_loss_smooth"],
        color="#2196F3",
        linewidth=2,
        label="Train (smoothed)",
    )
    ax1.plot(
        epoch_df["epoch"],
        epoch_df["val_loss_smooth"],
        color="#F44336",
        linewidth=2,
        label="Val (smoothed)",
    )

    # Mark best validation loss
    best_epoch = epoch_df.loc[epoch_df["val_loss"].idxmin(), "epoch"]
    best_loss = epoch_df["val_loss"].min()
    ax1.axvline(x=best_epoch, color="green", linestyle="--", alpha=0.7)
    ax1.scatter(
        [best_epoch], [best_loss], color="green", s=100, zorder=5, label=f"Best: Epoch {best_epoch}"
    )

    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.set_title("Loss Convergence (with Smoothing)")
    ax1.legend(fontsize=8)
    ax1.grid(True, linestyle="--", alpha=0.4)

    # Relative improvement plot
    if len(epoch_df) > 1:
        initial_loss = epoch_df["val_loss"].iloc[0]
        relative_improvement = 100 * (initial_loss - epoch_df["val_loss"]) / initial_loss
        ax2.plot(epoch_df["epoch"], relative_improvement, color="#4CAF50", linewidth=2)
        ax2.fill_between(epoch_df["epoch"], 0, relative_improvement, alpha=0.3, color="#4CAF50")
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Improvement from Initial (%)")
        ax2.set_title("Relative Loss Improvement")
        ax2.grid(True, linestyle="--", alpha=0.4)

        # Annotate final improvement
        final_improvement = relative_improvement.iloc[-1]
        ax2.annotate(
            f"Final: {final_improvement:.1f}%",
            xy=(epoch_df["epoch"].iloc[-1], final_improvement),
            xytext=(10, 10),
            textcoords="offset points",
            fontsize=10,
            color="#4CAF50",
        )

    plt.suptitle(f"Convergence Analysis: {model_name}", fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def plot_training_summary(
    training_dir: str,
    model_name: str,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot comprehensive training summary.

    Args:
        training_dir: Base training directory.
        model_name: Name of the model to analyze.
        show: Whether to display the plot.
        save_path: Path to save the plot image (optional).
    """
    epoch_df, saves_df = load_training_data(training_dir, model_name)

    if epoch_df is None or epoch_df.empty:
        print(f"No epoch data found for model: {model_name}")
        return

    fig = plt.figure(figsize=(16, 12))

    # Create grid for subplots
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # Loss curves (large)
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.plot(epoch_df["epoch"], epoch_df["train_loss"], label="Train", color="#2196F3", linewidth=2)
    ax1.plot(
        epoch_df["epoch"], epoch_df["val_loss"], label="Validation", color="#F44336", linewidth=2
    )
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.set_title("Training and Validation Loss")
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.4)

    # Accuracy curves
    ax2 = fig.add_subplot(gs[1, :2])
    ax2.plot(
        epoch_df["epoch"], epoch_df["train_accuracy"], label="Train", color="#2196F3", linewidth=2
    )
    ax2.plot(
        epoch_df["epoch"],
        epoch_df["val_accuracy"],
        label="Validation",
        color="#F44336",
        linewidth=2,
    )
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy (%)")
    ax2.set_title("Training and Validation Accuracy")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.4)

    # Summary statistics (text box)
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis("off")
    stats_text = f"""Training Summary
─────────────────
Total Epochs: {len(epoch_df)}

Final Metrics:
  Train Loss: {epoch_df['train_loss'].iloc[-1]:.4f}
  Val Loss: {epoch_df['val_loss'].iloc[-1]:.4f}
  Train Acc: {epoch_df['train_accuracy'].iloc[-1]:.2f}%
  Val Acc: {epoch_df['val_accuracy'].iloc[-1]:.2f}%

Best Validation:
  Epoch: {epoch_df.loc[epoch_df['val_loss'].idxmin(), 'epoch']}
  Loss: {epoch_df['val_loss'].min():.4f}
  Acc: {epoch_df.loc[epoch_df['val_accuracy'].idxmax(), 'val_accuracy']:.2f}%

Overfitting Indicator:
  Gap: {(epoch_df['val_loss'].iloc[-1] - epoch_df['train_loss'].iloc[-1]):.4f}"""
    ax3.text(
        0.1,
        0.9,
        stats_text,
        transform=ax3.transAxes,
        fontsize=10,
        verticalalignment="top",
        fontfamily="monospace",
    )

    # Generalization gap
    ax4 = fig.add_subplot(gs[1, 2])
    gap = epoch_df["val_loss"] - epoch_df["train_loss"]
    ax4.fill_between(epoch_df["epoch"], gap, alpha=0.5, color="#FF9800")
    ax4.plot(epoch_df["epoch"], gap, color="#FF9800", linewidth=2)
    ax4.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax4.set_xlabel("Epoch")
    ax4.set_ylabel("Gap")
    ax4.set_title("Generalization Gap")
    ax4.grid(True, linestyle="--", alpha=0.4)

    # Loss improvement per epoch
    ax5 = fig.add_subplot(gs[2, :])
    if len(epoch_df) > 1:
        train_improvement = -epoch_df["train_loss"].diff()
        val_improvement = -epoch_df["val_loss"].diff()
        width = 0.35
        x = epoch_df["epoch"][1:]
        ax5.bar(
            [i - width / 2 for i in x],
            train_improvement[1:],
            width,
            label="Train",
            color="#2196F3",
            alpha=0.8,
        )
        ax5.bar(
            [i + width / 2 for i in x],
            val_improvement[1:],
            width,
            label="Val",
            color="#F44336",
            alpha=0.8,
        )
        ax5.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
        ax5.set_xlabel("Epoch")
        ax5.set_ylabel("Loss Improvement")
        ax5.set_title("Loss Improvement per Epoch")
        ax5.legend()
        ax5.grid(True, axis="y", linestyle="--", alpha=0.4)

    plt.suptitle(f"Training Summary: {model_name}", fontsize=14, y=0.98)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()


def find_models(training_dir: str) -> list[str]:
    """Find all model directories in training directory.

    Args:
        training_dir: Base training directory.

    Returns:
        List of model directory names.
    """
    final_saves = os.path.join(training_dir, FINAL_SAVES_DIR)
    if not os.path.exists(final_saves):
        return []

    models = []
    for item in os.listdir(final_saves):
        if os.path.isdir(os.path.join(final_saves, item)):
            models.append(item)
    return models


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot advanced training analysis")
    p.add_argument(
        "-d",
        "--training-dir",
        default=".",
        help="Base training directory (default: current directory)",
    )
    p.add_argument(
        "-m",
        "--model",
        default=None,
        help="Model name to analyze (default: first found)",
    )
    p.add_argument(
        "--show", action="store_true", help="Display plot in GUI (default: save to file)"
    )
    p.add_argument(
        "-o",
        "--output",
        default="training_summary.png",
        help="File path to save summary plot",
    )
    p.add_argument(
        "--overfit-output",
        default="overfitting_analysis.png",
        help="File path to save overfitting analysis",
    )
    p.add_argument(
        "--convergence-output",
        default="convergence_analysis.png",
        help="File path to save convergence analysis",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    model_name = args.model
    if model_name is None:
        models = find_models(args.training_dir)
        if models:
            model_name = models[0]
            print(f"Using first model found: {model_name}")
        else:
            print("No models found in training directory.")
            exit(1)

    plot_training_summary(
        training_dir=args.training_dir, model_name=model_name, show=args.show, save_path=args.output
    )
    plot_overfitting_analysis(
        training_dir=args.training_dir,
        model_name=model_name,
        show=args.show,
        save_path=args.overfit_output,
    )
    plot_convergence_analysis(
        training_dir=args.training_dir,
        model_name=model_name,
        show=args.show,
        save_path=args.convergence_output,
    )
