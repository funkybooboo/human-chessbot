import os
import random
import time

import torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader

from packages.train.src.constants import (
    CHECK_POINT_DIR,
    CHECK_POINT_INFO_FILE_NAME,
    EPOCH_INFO_FILE_NAME,
    FINAL_SAVES_DIR,
)
from packages.train.src.dataset.fillers.fill_snapshots_and_statistics import (
    fill_database_with_snapshots,
)
from packages.train.src.dataset.loaders.game_snapshots import GameSnapshotsDataset


def make_directory(directory_name):
    """
    Creates a directory if it does not already exist.

    Args:
        directory_name (str): The name of the directory to create.
    """
    try:
        os.mkdir(directory_name)
        print(f"Directory '{directory_name}' created successfully.")
    except FileExistsError:
        print(f"Directory '{directory_name}' already exists.")


class Trainer:
    """
    A class for training a PyTorch model for chess move prediction.

    This class encapsulates the entire training process, including data loading,
    hyperparameter tuning, model training, evaluation, and checkpointing.
    """

    def __init__(self, values: dict, model):
        """
        Initializes the Trainer object.

        Args:
            values (dict): A dictionary containing hyperparameters, database information, and checkpoint settings.
            model: The PyTorch model to be trained.
        """
        hyperparameters = values["hyperparameters"]
        database_info = values["database_info"]
        checkpoints = values["checkpoints"]

        # Model
        self.model = model
        self.criterion = nn.CrossEntropyLoss()

        # stable parameters
        self.num_epochs: int = hyperparameters["num_epochs"]
        self.batch_size: int = hyperparameters["batch_size"]
        self.num_workers: int = hyperparameters["num_workers"]

        # searchable parameters
        self.learning_rates: list = hyperparameters["learning_rates"]
        self.decay_rates: list = hyperparameters["decay_rates"]
        self.betas: list = hyperparameters["betas"]
        self.momentums: list = hyperparameters["momentums"]

        # current parameters
        self.current_lr: float = self.learning_rates[0]
        self.current_decay_rate: float = self.decay_rates[0]
        self.current_beta: float = self.betas[0]
        self.current_momentum: float = self.momentums[0]

        # data loaders
        total_instances = database_info["num_indexes"]

        # Other
        self.cuda_enabled: bool = values["cuda_enabled"]
        if self.cuda_enabled and not torch.cuda.is_available():
            print("Warning: cuda_enabled=True but CUDA is not available. Falling back to CPU.")
            self.cuda_enabled = False
        # Select device
        self.device = torch.device("cuda" if self.cuda_enabled else "cpu")

        # Move model and criterion to the device
        self.model.to(self.device)
        self.criterion = self.criterion.to(self.device)

        fill_database_with_snapshots(
            snapshots_threshold=total_instances, max_size_gb=database_info["max_size_gb"]
        )

        data_split = database_info["data_split"]
        start_index = 0

        self.train_dataloader = self._create_dataloader(
            start_index, int(total_instances * data_split["train"])
        )
        start_index += int(total_instances * data_split["train"])
        self.val_dataloader = self._create_dataloader(
            start_index, int(total_instances * data_split["validation"])
        )
        start_index += int(total_instances * data_split["validation"])
        self.test_dataloader = self._create_dataloader(
            start_index, int(total_instances * data_split["test"])
        )

        # Model Checkpoints Path
        self.save_directory = checkpoints["directory"]
        make_directory(self.save_directory)
        self.final_save = self.save_directory + FINAL_SAVES_DIR + "/"
        make_directory(self.final_save)

        self.auto_save_path = self.save_directory + CHECK_POINT_DIR + "/"
        make_directory(self.auto_save_path)
        self.auto_save_interval = checkpoints["auto_save_interval"]
        self.model_name = ""

    def _create_dataloader(self, start: int, num_indexes: int) -> DataLoader:
        """
        Creates a DataLoader for a subset of the GameSnapshotsDataset.

        Args:
            start (int): The starting index for the dataset subset.
            num_indexes (int): The number of indexes to include in the dataset subset.

        Returns:
            DataLoader: A DataLoader for the specified subset of the dataset.
        """
        dataset = GameSnapshotsDataset(start, num_indexes)

        dataloader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=(self.device.type == "cuda"),
        )

        return dataloader

    def _update_model_name(self):
        """
        Updates the model name to be a description of the current learning rate, decay rate,
        beta, and momentum values.
        """
        updated_name = f"del_lr{self.current_lr}"
        updated_name += f"_decay{self.current_decay_rate}"
        updated_name += f"_beta{self.current_beta}"
        updated_name += f"_momentum{self.current_momentum}"

        self.model_name = updated_name

    def train(self):
        """
        Trains the model using the current hyperparameters, saving the model periodically
        to a checkpoint directory based on self.auto_save_interval, as well as training
        information, before saving the final model.
        """
        # Define loss function and optimizer
        optimizer = Adam(
            self.model.parameters(),
            lr=self.current_lr,
            weight_decay=self.current_decay_rate,
            betas=(self.current_beta, self.current_momentum),
        )

        last_save_time = time.time()

        self.model.train()
        # Training loop
        non_blocking = self.device.type == "cuda"
        for epoch in range(self.num_epochs):
            self.model.train()

            for _batch, ((board, metadata), (chosen_move, valid_moves)) in enumerate(
                self.train_dataloader
            ):
                # batch_x is a tuple (metadata, board), need to handle each component
                # Unpack board and metadata from batch_x tuple
                metadata = metadata.to(self.device, non_blocking=non_blocking)
                board = board.to(self.device, non_blocking=non_blocking)
                chosen_move = chosen_move.to(self.device, non_blocking=non_blocking)
                valid_moves = valid_moves.to(self.device, non_blocking=non_blocking)

                optimizer.zero_grad()
                predicted_chosen, predicted_valid = self.model(metadata, board)

                # calculate loss
                move_loss = self.criterion(predicted_chosen, chosen_move)
                valid_loss = self.criterion(predicted_valid, valid_moves)
                loss = move_loss + valid_loss

                loss.backward()
                optimizer.step()

                # check for auto save
                if time.time() - last_save_time >= self.auto_save_interval:
                    self._save_model()
                    last_save_time = time.time()

            self._update_epoch_csv(epoch)
        self._save_model(auto_save=False)

    def _dataset_loss(self, dataloader: DataLoader) -> tuple[float, float]:
        """
        Computes the loss and accuracy of the model for a given dataloader.

        Args:
            dataloader (DataLoader): The DataLoader to evaluate the model on.

        Returns:
            tuple: A tuple containing the average loss and accuracy.
        """

        total_loss = 0.0
        correct_moves = 0

        self.model.eval()
        non_blocking = self.device.type == "cuda"
        with torch.no_grad():
            for _batch, ((board, metadata), (chosen_move, _)) in enumerate(dataloader):
                # batch_x is a tuple (metadata, board), need to handle each component
                metadata = metadata.to(self.device, non_blocking=non_blocking)
                board = board.to(self.device, non_blocking=non_blocking)
                chosen_move = chosen_move.to(self.device, non_blocking=non_blocking)

                predicted_moves, _ = self.model(metadata, board)

                move_loss = self.criterion(predicted_moves, chosen_move)
                loss = move_loss
                total_loss += loss.item()

                # Only calculate the accuracy of moves
                _, predicted_moves = torch.max(predicted_moves.data, 1)
                correct_moves += (predicted_moves == chosen_move).sum().item()

        avg_loss = total_loss / len(dataloader.dataset)
        accuracy = 100 * correct_moves / len(dataloader.dataset)

        self.model.train()

        return avg_loss, accuracy

    def randomize_hyperparameters(self):
        """
        Randomizes and assigns hyperparameter values from the lists of possible values.

        This method selects random values for learning rate, decay rate, beta,
        and momentum from their respective lists and assigns them to the object's
        instance variables.
        """
        self.current_lr = random.choice(self.learning_rates)
        self.current_decay_rate = random.choice(self.decay_rates)
        self.current_beta = random.choice(self.betas)
        self.current_momentum = random.choice(self.momentums)

    def random_search(self, iterations: int):
        """
        Conducts a random search for hyperparameter optimization by iteratively testing
        random configurations, evaluating their performance, and updating the best set
        of hyperparameters based on validation loss.

        Args:
            iterations (int): The number of random configurations to search over.
        """
        best_val_loss = float("inf")
        best_hyperparameters = {}

        for _ in range(iterations):
            self.randomize_hyperparameters()
            self._update_model_name()

            # create new directories
            make_directory(self.auto_save_path + self.model_name + "/")
            make_directory(self.final_save + self.model_name + "/")

            print(
                f"Testing with LR: {self.current_lr}, Decay: {self.current_decay_rate}, Beta: {self.current_beta}, Momentum: {self.current_momentum}"
            )
            self.train()
            self._save_model()
            avg_val_loss, _ = self._dataset_loss(self.val_dataloader)
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                best_hyperparameters = {
                    "learning_rate": self.current_lr,
                    "decay_rate": self.current_decay_rate,
                    "beta": self.current_beta,
                    "momentum": self.current_momentum,
                }
                print(
                    f"New best hyperparameters found: {best_hyperparameters} with Val Loss: {best_val_loss:.4f}"
                )

        print(f"Best Hyperparameters: {best_hyperparameters} with Val Loss: {best_val_loss:.4f}")

    def _save_model(self, auto_save: bool = True):
        """
        Saves the model state to a file in the appropriate directory.

        This method saves the state of the model to either the check_points
        directory for the model or the final output directory depending on
        whether the auto-save option is enabled or not.

        Args:
            auto_save (bool): Indicates whether to save the model in the auto-save
                directory or the final save directory. Defaults to True.
        """
        print("Saving model...")
        # save the model
        if auto_save:
            save_directory = f"{self.auto_save_path}{self.model_name}/"
        else:
            save_directory = f"{self.final_save}{self.model_name}/"
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        torch.save(self.model.state_dict(), f"{save_directory}{timestamp}.pth")

        # save model performance metrics to csv
        self._update_saves_csv(timestamp)

    def _update_saves_csv(self, timestamp: str):
        """
        Updates a CSV file with training and validation metrics for a model.

        This method writes performance metrics, including training loss, training
        accuracy, validation loss, and validation accuracy, along with hyperparameters
        and the timestamp to a CSV file. If the file does not exist, it creates the
        file and writes the appropriate headers.

        Args:
            timestamp (str): A timestamp string representing the version of the save.
        """
        csv_path = self.final_save + self.model_name + "/" + CHECK_POINT_INFO_FILE_NAME

        train_loss, train_accuracy = self._dataset_loss(self.train_dataloader)
        val_loss, val_accuracy = self._dataset_loss(self.val_dataloader)

        print(
            f"Train Loss: {train_loss:.4f}, Train Acc: {train_accuracy}, Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.2f}%"
        )

        # check if csv exists and if not create it and the associated headers
        if not os.path.exists(csv_path):
            header = "time_stamp,train_loss,train_accuracy,val_loss,val_accuracy\n"
            with open(csv_path, "w") as file:
                file.write(header)

        with open(csv_path, "a") as file:
            file.write(f"{timestamp},{train_loss},{train_accuracy},{val_loss},{val_accuracy}\n")

        print(f"Wrote {timestamp} info to {csv_path}")

    def _update_epoch_csv(self, epoch: int):
        """
        Updates the epoch data in a CSV file with the training and validation statistics.

        This method computes the training and validation loss and accuracy for the current
        epoch, records them, and appends the data into a CSV file. If the CSV file does not
        exist, it is created along with the appropriate headers.

        If the CSV file exists, the function appends the computed epoch details to it. The method
        also prints a summary of the epoch's performance statistics.

        Args:
            epoch (int): The current epoch index being processed.
        """
        csv_path = self.final_save + self.model_name + "/" + EPOCH_INFO_FILE_NAME

        train_loss, train_accuracy = self._dataset_loss(self.train_dataloader)
        val_loss, val_accuracy = self._dataset_loss(self.val_dataloader)

        print(
            f"Epoch: {epoch}/{self.num_epochs} | Train Loss: {train_loss:.4f}, Train Acc: {train_accuracy}, Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.2f}%"
        )

        # check if csv exists and if not create it and the associated headers
        if not os.path.exists(csv_path):
            header = "epoch,train_loss,train_accuracy,val_loss,val_accuracy\n"
            with open(csv_path, "w") as file:
                file.write(header)

        with open(csv_path, "a") as file:
            file.write(f"{epoch},{train_loss},{train_accuracy},{val_loss},{val_accuracy}\n")
        print(f"Wrote {epoch} info to {csv_path}")

        # save model
        save_directory = f"{self.auto_save_path}{self.model_name}/"
        torch.save(self.model.state_dict(), f"{save_directory}epoch_{epoch}.pth")
        print(f"Saved model for epoch {epoch} to {save_directory}epoch_{epoch}.pth")
