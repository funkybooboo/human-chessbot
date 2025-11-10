import os

import matplotlib.pyplot as plt
import pandas as pd

from packages.train.src.constants import (
    CHECK_POINT_DIR,
    CHECK_POINT_INFO_FILE_NAME,
    EPOCH_INFO_FILE_NAME,
    FINAL_SAVES_DIR,
)


class Analyzer:
    def __init__(self, training_directory):
        # Set up directories and get model paths
        self.training_directory = training_directory + "/"
        self.final_save = self.training_directory + FINAL_SAVES_DIR + "/"
        self.checkpoints = self.training_directory + CHECK_POINT_DIR + "/"
        self.model_directories = self._get_all_model_directories()

    def _get_all_model_directories(self) -> list[str]:
        """Find and return list of all model directories in final_saves path.

        Returns:
            list: List of directory names found in final_saves path
        """
        if not os.path.exists(self.final_save):
            return []

        directories = []
        for item in os.listdir(self.final_save):
            full_path = os.path.join(self.final_save, item)
            if os.path.isdir(full_path):
                directories.append(item)

        return directories

    def _validate_files(self, model_name: str) -> tuple[str, str] | None:
        """Validate required files exist and return their paths."""
        model_dir = os.path.join(self.final_save, model_name)
        if not os.path.exists(model_dir):
            return None

        save_csv_path = os.path.join(model_dir, CHECK_POINT_INFO_FILE_NAME)
        epoch_csv_path = os.path.join(model_dir, EPOCH_INFO_FILE_NAME)

        if not os.path.exists(save_csv_path) or not os.path.exists(epoch_csv_path):
            return None

        return save_csv_path, epoch_csv_path

    def _plot_metrics(
        self, ax, x, train_metric, val_metric, xlabel, ylabel, title=None, rotate_x=False
    ):
        """Helper method to plot training metrics."""
        ax.plot(x, train_metric, label="Training " + ylabel)
        ax.plot(x, val_metric, label="Validation " + ylabel)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        ax.legend()
        ax.grid(True)
        if rotate_x:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    def _save_single_plot(
        self, x, train_metric, val_metric, xlabel, ylabel, save_path, rotate_x=False
    ):
        """Create and save a single metric plot."""
        plt.figure(figsize=(10, 5))
        self._plot_metrics(
            plt.gca(), x, train_metric, val_metric, xlabel, ylabel, rotate_x=rotate_x
        )
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

    def _create_epoch_plots(self, epoch_df, model_name):
        """Create all epoch-related plots."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

        self._plot_metrics(
            ax1, epoch_df["epoch"], epoch_df["train_loss"], epoch_df["val_loss"], "Epoch", "Loss"
        )
        self._plot_metrics(
            ax2,
            epoch_df["epoch"],
            epoch_df["train_accuracy"],
            epoch_df["val_accuracy"],
            "Epoch",
            "Accuracy",
        )

        fig.tight_layout()
        fig.savefig(os.path.join(self.final_save, model_name, "epoch_curves.png"))

        # Save individual plots
        self._save_single_plot(
            epoch_df["epoch"],
            epoch_df["train_loss"],
            epoch_df["val_loss"],
            "Epoch",
            "Loss",
            os.path.join(self.final_save, model_name, "epoch_loss.png"),
        )
        self._save_single_plot(
            epoch_df["epoch"],
            epoch_df["train_accuracy"],
            epoch_df["val_accuracy"],
            "Epoch",
            "Accuracy",
            os.path.join(self.final_save, model_name, "epoch_accuracy.png"),
        )
        return fig

    def _create_save_plots(self, save_df, model_name):
        """Create all save-related plots."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

        self._plot_metrics(
            ax1,
            save_df["timestamp"],
            save_df["train_loss"],
            save_df["val_loss"],
            "Time",
            "Loss",
            rotate_x=True,
        )
        self._plot_metrics(
            ax2,
            save_df["timestamp"],
            save_df["train_accuracy"],
            save_df["val_accuracy"],
            "Time",
            "Accuracy",
            rotate_x=True,
        )

        fig.tight_layout()
        fig.savefig(os.path.join(self.final_save, model_name, "save_curves.png"))

        # Save individual plots
        self._save_single_plot(
            save_df["timestamp"],
            save_df["train_loss"],
            save_df["val_loss"],
            "Time",
            "Loss",
            os.path.join(self.final_save, model_name, "save_loss.png"),
            rotate_x=True,
        )
        self._save_single_plot(
            save_df["timestamp"],
            save_df["train_accuracy"],
            save_df["val_accuracy"],
            "Time",
            "Accuracy",
            os.path.join(self.final_save, model_name, "save_accuracy.png"),
            rotate_x=True,
        )
        return fig

    def _create_overview_plot(self, epoch_df, save_df, model_name):
        """Create overview plot combining epoch and save metrics."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 15))

        self._plot_metrics(
            ax1,
            epoch_df["epoch"],
            epoch_df["train_loss"],
            epoch_df["val_loss"],
            "Epoch",
            "Loss",
            "Epoch Loss",
        )
        self._plot_metrics(
            ax2,
            epoch_df["epoch"],
            epoch_df["train_accuracy"],
            epoch_df["val_accuracy"],
            "Epoch",
            "Accuracy",
            "Epoch Accuracy",
        )
        self._plot_metrics(
            ax3,
            save_df["timestamp"],
            save_df["train_loss"],
            save_df["val_loss"],
            "Time",
            "Loss",
            "Save Loss",
            rotate_x=True,
        )
        self._plot_metrics(
            ax4,
            save_df["timestamp"],
            save_df["train_accuracy"],
            save_df["val_accuracy"],
            "Time",
            "Accuracy",
            "Save Accuracy",
            rotate_x=True,
        )

        fig.tight_layout()
        fig.savefig(os.path.join(self.final_save, model_name, "overview.png"))
        return fig

    def _graph_training_curves(self, model_name: str):
        paths = self._validate_files(model_name)
        if not paths:
            return

        save_csv_path, epoch_csv_path = paths

        save_df = pd.read_csv(save_csv_path)
        epoch_df = pd.read_csv(epoch_csv_path)
        save_df["timestamp"] = pd.to_datetime(save_df["time_stamp"], format="%Y%m%d-%H%M%S")

        self._create_epoch_plots(epoch_df, model_name)
        self._create_save_plots(save_df, model_name)
        self._create_overview_plot(epoch_df, save_df, model_name)
        plt.close("all")


if __name__ == "__main__":
    analyzer = Analyzer(training_directory="analysis")
    print(analyzer.model_directories)
    for model in analyzer.model_directories:
        analyzer._graph_training_curves(model)
