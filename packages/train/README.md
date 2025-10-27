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

### Models (`src/models/`)
ML model prototypes (in development):
- `random_forest.ipynb` - Random forest classifier
- `ann.ipynb` - Artificial neural network

## Usage

```bash
# Run dataset pipeline
python -m packages.train.src.dataset.main

# Access models in Jupyter
jupyter lab packages/train/src/models/
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
│   └── models/            # ML model notebooks
└── tests/                 # Test suite
```
