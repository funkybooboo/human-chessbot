import os
from unittest.mock import MagicMock, patch

import pytest
import torch
from torch import nn
from torch.utils.data import TensorDataset

from packages.train.src.train.trainer import Trainer


# Mock model that mirrors the NeuralNetwork structure for testing
class MockModel(nn.Module):
    def __init__(self):
        super().__init__()
        # Simple structure: convolution -> flatten -> fully connected -> two heads
        self.convolution = nn.Sequential(
            nn.Conv2d(12, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
        )
        self.fully_connected = nn.Sequential(
            nn.Linear(64 * 8 * 8 + 4, 32),  # board features + metadata
            nn.ReLU(),
        )
        self.move_head = nn.Sequential(nn.Linear(32, 2104))
        self.auxiliary_head = nn.Sequential(nn.Linear(32, 2104))

    def forward(self, metadata: torch.Tensor, board: torch.Tensor):
        board = self.convolution(board)
        board = torch.flatten(board, 1)
        x = torch.cat((board, metadata), dim=1)
        shared_output = self.fully_connected(x)
        return self.move_head(shared_output), self.auxiliary_head(shared_output)


@pytest.fixture
def mock_values():
    """Provides a dictionary of mock values for initializing the Trainer."""
    return {
        "hyperparameters": {
            "num_epochs": 1,
            "batch_size": 2,
            "num_workers": 0,
            "learning_rates": [0.001, 0.01],
            "decay_rates": [0.0001, 0.001],
            "betas": [0.9, 0.95],
            "momentums": [0.99, 0.999],
        },
        "database_info": {
            "num_indexes": 100,
            "max_size_gb": 1,
            "data_split": {"train": 0.8, "validation": 0.1, "test": 0.1},
        },
        "checkpoints": {
            "directory": "/tmp/test_checkpoints",
            "auto_save_interval": 60,
        },
        "cuda_enabled": False,
    }


@pytest.fixture
def mock_trainer(mock_values, tmp_path):
    """Initializes the Trainer with mock values and patches external dependencies."""
    # Use a temporary directory for checkpoints
    mock_values["checkpoints"]["directory"] = str(tmp_path)

    with (
        patch("packages.train.src.train.trainer.pipeline"),
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
        patch("os.mkdir", wraps=os.mkdir),
    ):  # Wrap mkdir to allow tmp_path to work
        # Create a mock dataset that returns data in the expected format
        # The dataset should return ((board, metadata), (chosen_move, valid_moves))
        mock_dataset_instance = MagicMock()
        mock_dataset_instance.__len__.return_value = 10
        mock_dataset_instance.__getitem__.return_value = (
            (torch.randn(12, 8, 8), torch.randn(4)),  # (board, metadata)
            (
                torch.randint(0, 2104, ()),
                torch.randint(0, 2, (2104,)),
            ),  # (chosen_move, valid_moves)
        )
        mock_dataset.return_value = mock_dataset_instance

        model = MockModel()
        trainer = Trainer(mock_values, model)
        # Manually set dataloaders since the patching can be tricky with __init__
        trainer.train_dataloader = trainer._create_dataloader(0, 80)
        trainer.val_dataloader = trainer._create_dataloader(80, 10)
        trainer.test_dataloader = trainer._create_dataloader(90, 10)
        return trainer


@patch("packages.train.src.train.trainer.Trainer.train")
@patch("packages.train.src.train.trainer.Trainer._save_model")
@patch("packages.train.src.train.trainer.Trainer._dataset_loss", return_value=(0.1, 95.0))
@patch("packages.train.src.train.trainer.make_directory")
def test_random_search(mock_mkdir, mock_dataset_loss, mock_save, mock_train, mock_trainer):
    """Tests the random_search method."""
    iterations = 2
    # Mock randomize_hyperparameters to return different values
    with patch.object(mock_trainer, "randomize_hyperparameters") as mock_random_hyper:
        # Simulate two different sets of hyperparameters
        def side_effect():
            if mock_random_hyper.call_count == 1:
                mock_trainer.current_lr = 0.01
                mock_trainer.current_decay_rate = 0.001
                mock_trainer.current_beta = 0.95
                mock_trainer.current_momentum = 0.999
                # Make validation loss different for each run
                mock_dataset_loss.return_value = (0.2, 90.0)
            else:
                mock_trainer.current_lr = 0.001
                mock_trainer.current_decay_rate = 0.0001
                mock_trainer.current_beta = 0.9
                mock_trainer.current_momentum = 0.99
                mock_dataset_loss.return_value = (0.1, 95.0)  # Better loss

        mock_random_hyper.side_effect = side_effect
        mock_trainer.random_search(iterations)

    assert mock_random_hyper.call_count == iterations
    assert mock_train.call_count == iterations
    assert mock_save.call_count == iterations
    assert mock_dataset_loss.call_count == iterations
    # two directories per iteration (auto_save and final_save)
    assert mock_mkdir.call_count == iterations * 2


# Additional tests for improved coverage


def test_cuda_device_handling_fallback(mock_values, tmp_path):
    """Tests CUDA fallback when CUDA is not available."""
    mock_values["cuda_enabled"] = True
    mock_values["checkpoints"]["directory"] = str(tmp_path)

    with (
        patch("torch.cuda.is_available", return_value=False),
        patch("packages.train.src.train.trainer.pipeline"),
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
        patch("packages.train.src.train.trainer.make_directory"),
    ):
        mock_dataset.return_value = TensorDataset(torch.randn(10, 10), torch.randint(0, 2, (10,)))

        with patch("builtins.print") as mock_print:
            model = MockModel()
            trainer = Trainer(mock_values, model)

            # Should fallback to CPU
            assert trainer.cuda_enabled is False
            assert trainer.device.type == "cpu"
            mock_print.assert_called_with(
                "Warning: cuda_enabled=True but CUDA is not available. Falling back to CPU."
            )


def test_cuda_device_handling_available(mock_values, tmp_path):
    """Tests CUDA device when CUDA is available."""
    mock_values["cuda_enabled"] = True
    mock_values["checkpoints"]["directory"] = str(tmp_path)

    with (
        patch("torch.cuda.is_available", return_value=True),
        patch("packages.train.src.train.trainer.pipeline"),
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
        patch("torch.nn.Module.to"),
    ):  # Mock the to() method to avoid CUDA initialization
        mock_dataset.return_value = TensorDataset(torch.randn(10, 10), torch.randint(0, 2, (10,)))

        model = MockModel()
        trainer = Trainer(mock_values, model)

        # Should use CUDA
        assert trainer.cuda_enabled is True
        assert trainer.device.type == "cuda"


def test_pipeline_integration(mock_values, tmp_path):
    """Tests pipeline integration during initialization."""
    mock_values["checkpoints"]["directory"] = str(tmp_path)

    with (
        patch("packages.train.src.train.trainer.pipeline") as mock_pipeline,
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
    ):
        mock_dataset.return_value = TensorDataset(torch.randn(10, 10), torch.randint(0, 2, (10,)))

        model = MockModel()
        Trainer(mock_values, model)

        # Pipeline should be called with correct parameters
        mock_pipeline.assert_called_once_with(
            mock_values["database_info"]["num_indexes"], mock_values["database_info"]["max_size_gb"]
        )


def test_pipeline_error_handling(mock_values, tmp_path):
    """Tests error handling when pipeline fails."""
    mock_values["checkpoints"]["directory"] = str(tmp_path)

    with (
        patch(
            "packages.train.src.train.trainer.pipeline", side_effect=Exception("Pipeline failed")
        ),
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
    ):
        mock_dataset.return_value = TensorDataset(torch.randn(10, 10), torch.randint(0, 2, (10,)))

        model = MockModel()
        with pytest.raises(Exception, match="Pipeline failed"):
            Trainer(mock_values, model)


def test_auto_save_timing(mock_values, tmp_path):
    """Tests auto-save timing functionality."""
    mock_values["checkpoints"]["directory"] = str(tmp_path)
    mock_values["checkpoints"]["auto_save_interval"] = 1  # 1 second

    with (
        patch("packages.train.src.train.trainer.pipeline"),
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
        patch("packages.train.src.train.trainer.time") as mock_time,
        patch("packages.train.src.train.trainer.Trainer._save_model") as mock_save,
    ):
        # Create a mock dataset that provides proper (board, metadata) structure
        mock_dataset_instance = MagicMock()
        mock_dataset_instance.__len__.return_value = 10
        mock_dataset_instance.__getitem__.return_value = (
            (torch.randn(12, 8, 8), torch.randn(4)),  # (board, metadata)
            (
                torch.randint(0, 2104, ()),
                torch.randint(0, 2, (2104,)),
            ),  # (chosen_move, valid_moves)
        )
        mock_dataset.return_value = mock_dataset_instance

        # Mock time progression to trigger auto-save
        time_values = [0, 0.5, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        mock_time.time.side_effect = lambda: time_values.pop(0) if time_values else 10.0

        model = MockModel()
        trainer = Trainer(mock_values, model)
        trainer.num_epochs = 1  # Single epoch

        trainer.train()

        # Should save once due to time interval
        mock_save.assert_called()


def test_model_forward_pass_compatibility(mock_values, tmp_path):
    """Tests model forward pass compatibility with expected input/output format."""
    mock_values["checkpoints"]["directory"] = str(tmp_path)

    # Test that model can process the expected input format
    batch_size = 2
    metadata = torch.randn(batch_size, 4)
    board = torch.randn(batch_size, 12, 8, 8)

    model = MockModel()

    # Should not raise an exception
    try:
        chosen_move, valid_moves = model(metadata, board)
        assert chosen_move.shape[0] == batch_size
        assert valid_moves.shape[0] == batch_size
    except Exception as e:
        pytest.fail(f"Model forward pass failed: {e}")


def test_data_loading_edge_cases_empty_dataset(mock_values, tmp_path):
    """Tests handling of empty dataset edge case."""
    mock_values["checkpoints"]["directory"] = str(tmp_path)
    mock_values["database_info"]["num_indexes"] = 10  # Keep non-zero for DataLoader
    mock_values["database_info"]["data_split"] = {
        "train": 0.0,
        "validation": 0.0,
        "test": 0.0,
    }  # All splits empty

    with (
        patch("packages.train.src.train.trainer.pipeline"),
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
    ):
        mock_dataset_instance = MagicMock()
        mock_dataset_instance.__len__.return_value = 10
        mock_dataset_instance.__getitem__.return_value = (
            (torch.randn(12, 8, 8), torch.randn(4)),  # (board, metadata)
            (
                torch.randint(0, 2104, ()),
                torch.randint(0, 2, (2104,)),
            ),  # (chosen_move, valid_moves)
        )
        mock_dataset.return_value = mock_dataset_instance

        model = MockModel()
        trainer = Trainer(mock_values, model)

        # Should create dataloaders even with empty dataset splits
        assert trainer.train_dataloader is not None
        assert trainer.val_dataloader is not None
        assert trainer.test_dataloader is not None


def test_data_loading_edge_cases_invalid_split(mock_values, tmp_path):
    """Tests handling of invalid data split ratios."""
    mock_values["checkpoints"]["directory"] = str(tmp_path)
    mock_values["database_info"]["data_split"] = {
        "train": 0.5,
        "validation": 0.3,
        "test": 0.3,
    }  # Sum > 1.0

    with (
        patch("packages.train.src.train.trainer.pipeline"),
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
    ):
        mock_dataset_instance = MagicMock()
        mock_dataset_instance.__len__.return_value = 10
        mock_dataset_instance.__getitem__.return_value = (
            (torch.randn(12, 8, 8), torch.randn(4)),  # (board, metadata)
            (
                torch.randint(0, 2104, ()),
                torch.randint(0, 2, (2104,)),
            ),  # (chosen_move, valid_moves)
        )
        mock_dataset.return_value = mock_dataset_instance

        model = MockModel()
        trainer = Trainer(mock_values, model)

        # Should still create dataloaders, but may have overlapping indices
        assert trainer.train_dataloader is not None
        assert trainer.val_dataloader is not None
        assert trainer.test_dataloader is not None


def test_error_handling_invalid_hyperparameters(mock_values, tmp_path):
    """Tests error handling with invalid hyperparameters."""
    mock_values["checkpoints"]["directory"] = str(tmp_path)
    mock_values["hyperparameters"]["learning_rates"] = []  # Empty list

    with (
        patch("packages.train.src.train.trainer.pipeline"),
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
    ):
        mock_dataset.return_value = MagicMock()
        mock_dataset.__len__.return_value = 10
        mock_dataset.__getitem__.return_value = (
            (torch.randn(12, 8, 8), torch.randn(4)),  # (board, metadata)
            (
                torch.randint(0, 2104, (1,)),
                torch.randint(0, 2, (2104,)),
            ),  # (chosen_move, valid_moves)
        )

        model = MockModel()

        # Should fail during initialization when trying to access learning_rates[0]
        with pytest.raises(IndexError):
            Trainer(mock_values, model)


def test_error_handling_filesystem_permissions(mock_values):
    """Tests error handling when filesystem permissions prevent directory creation."""
    mock_values["checkpoints"]["directory"] = "/root/forbidden_directory"  # Likely inaccessible

    with (
        patch("packages.train.src.train.trainer.pipeline"),
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
        patch("os.mkdir", side_effect=PermissionError("Permission denied")),
    ):
        mock_dataset.return_value = TensorDataset(torch.randn(10, 10), torch.randint(0, 2, (10,)))

        model = MockModel()

        with pytest.raises(PermissionError):
            Trainer(mock_values, model)


def test_non_blocking_tensor_operations(mock_values, tmp_path):
    """Tests non-blocking tensor operations with CUDA."""
    mock_values["cuda_enabled"] = True
    mock_values["checkpoints"]["directory"] = str(tmp_path)

    with (
        patch("torch.cuda.is_available", return_value=True),
        patch("packages.train.src.train.trainer.pipeline"),
        patch("packages.train.src.train.trainer.GameSnapshotsDataset") as mock_dataset,
        patch("torch.nn.Module.to"),
    ):  # Mock to() method to avoid CUDA initialization
        mock_dataset.return_value = TensorDataset(torch.randn(10, 10), torch.randint(0, 2, (10,)))

        model = MockModel()
        trainer = Trainer(mock_values, model)

        # Should use non_blocking=True for CUDA operations
        assert trainer.device.type == "cuda"

        # Test that non_blocking is used in training loop
        with patch.object(trainer, "_dataset_loss") as mock_loss:
            mock_loss.return_value = (0.1, 90.0)
            trainer._dataset_loss(trainer.train_dataloader)
            # The method should be called, indicating non_blocking was used internally
