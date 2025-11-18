# Train Package

ML training pipeline and dataset ETL for chess AI models.

## Components

### Dataset Pipeline (`src/dataset/`)

ETL pipeline for Lichess game data:

- **Requesters**: Fetch Lichess game data and metadata
- **Repositories**: Database storage layer (SQLite)
- **Processers**: Transform games into training snapshots
- **Loaders**: Load game snapshots and legal moves for training
- **Plotter**: Visualization utilities for dataset analysis

### Training (`src/train/`)

Neural network training with hyperparameter search:

- `trainer.py` - Model training orchestration
- `main.py` - Training entry point with JSON config
- `analysis.py` - Training metrics analysis

### Models (`src/models/`)

Neural network model definitions:

- `neural_network.py` - PyTorch neural network architecture

## Usage

```bash
# Run dataset pipeline
python -m packages.train.src.dataset.main

# Train neural network model
python -m packages.train.src.train.main path/to/config.json
```

## Testing

```bash
pytest packages/train/tests/ -v
pytest packages/train/tests/ --cov=packages.train --cov-report=html
```

## Structure

```
train/
├── src/
│   ├── dataset/           # Lichess data ETL pipeline
│   │   ├── requesters/    # Data fetching
│   │   ├── repositories/  # Database layer
│   │   ├── processers/    # Data transformation
│   │   ├── loaders/       # Training data loaders
│   │   └── plotter.py     # Visualization
│   ├── train/             # Model training processors
│   └── models/            # Pytorch models
└── tests/                 # Test suite
```

## Training with `packages.train.src.train.main`

This package provides a training entrypoint that performs random search over hyperparameters and trains the neural network model.

### Quick start

From the project root, run:

```bash
python -m packages.train.src.train.main exampleConfig.json
```

- Replace `exampleConfig.json` with the path to your own config.
- The module will validate the path, load the JSON, and start random search for the specified number of iterations.

### Configuration schema

The training entrypoint takes a single argument: the path to a JSON configuration file with the following schema:

```json
{
  "num_iterations": 5,
  "hyperparameters": {
    "learning_rates": [0.01, 0.001, 0.0005, 0.0001],
    "decay_rates": [0, 0.1, 1e-4, 1e-6],
    "betas": [0.8, 0.9, 0.95, 0.9999],
    "momentums": [0.5, 0.9, 0.95, 0.99],
    "num_epochs": 100,
    "batch_size": 128,
    "num_workers": 4
  },
  "database_info": {
    "num_indexes": 10000,
    "max_size_gb": 10,
    "data_split": {"train": 0.8, "validation": 0.1, "test": 0.1}
  },
  "checkpoints": {
    "directory": "runs/",
    "auto_save_interval": 100
  }
}
```

### Field descriptions

- `cuda_enabled` (bool, optional): If true and a CUDA-capable GPU is available, training will use the model to speedup training process.
- `num_iterations` (int): Number of random hyperparameter configurations to try. For each iteration, one value is sampled from each list in `hyperparameters` and trained for `num_epochs`.

- `hyperparameters` (object):
  - `learning_rates` (list[float]): Candidate learning rates for Adam (`lr`).
  - `decay_rates` (list[float]): Candidate weight decay values for Adam (`weight_decay`).
  - `betas` (list[float]): Candidate values for Adam's first beta parameter (`beta1`).
  - `momentums` (list[float]): Candidate values for Adam's second beta parameter (`beta2`).
  - `num_epochs` (int): Training epochs per trial.
  - `batch_size` (int): Batch size for DataLoader.
  - `num_workers` (int): Number of worker processes for DataLoader.

- `database_info` (object):
  - `num_indexes` (int): Total number of snapshot rows to ensure in the local database. The dataset is split sequentially into train/val/test ranges of this size.
  - `max_size_gb` (int): Upper bound passed to the dataset filler to cap DB size on disk.
  - `data_split` (object): Fractions for dataset splits. Keys: `train`, `validation`, `test`. Should sum to 1.0.

- `checkpoints` (object):
  - `directory` (string): Base directory where training artifacts are written. The trainer will create subfolders `trained_models/` and `check_points/` within this directory. Tip: keep a trailing slash (e.g., `runs/`).
  - `auto_save_interval` (int): Autosave interval in seconds. During training, the model is autosaved to a model specific `checkpoints/` whenever this many seconds have elapsed.

### What the trainer does

- Initializes a `NeuralNetwork` model (`packages/train/src/models/neural_network.py`).
- Builds `DataLoader`s for train/validation/test using `GameSnapshotsDataset` according to `database_info` and `data_split`.
- For each random-search iteration:
  - Samples a configuration: `learning_rate`, `decay_rate`, `beta` (`beta1`), and `momentum` (`beta2`).
  - Trains for `num_epochs` with Adam using those values.
  - Autosaves periodically according to `auto_save_interval`.
  - Evaluates on the validation split and tracks the best configuration by lowest validation loss.

### Outputs and directory layout

Given `checkpoints.directory = runs/`, the trainer creates:

```
runs/
├── check_points/
│   └── del_lr{lr}_decay{decay}_beta{beta}_momentum{momentum}/
│       ├── <timestamp>.pth          # autosaved weights
        └── epoch_<num>.pth          # end of epoch checkpoint
└── trained_models/
    └── del_lr{lr}_decay{decay}_beta{beta}_momentum{momentum}/
        ├── <timestamp>.pth          # final end of run save
        └── saves.csv                # metrics log per save
```

- Model name encodes the active hyperparameters for that run.
- `saves.csv` columns: `version_name,learning_rate,decay_rate,beta,momentum,train_loss,train_accuracy,val_loss,val_accuracy`.
- Console logs include per-save metrics and a final summary of the best hyperparameters found.

### Tips

- Start with small `num_iterations` and `num_epochs` to validate pipelines and data access.
- Keep `learning_rates` on a log scale (e.g., 1e-2 to 1e-4). Combine with small `weight_decay` candidates.
- Ensure `data_split` fractions sum to 1.0 and `num_indexes` is large enough to cover meaningful train/val/test sets.
- If you run from a different working directory, pass an absolute path to the config file.
