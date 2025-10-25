# Train Package

ML training data pipeline for chess. Fetches Lichess games, processes PGN into board snapshots for model training.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Fill database with game snapshots
python -m src.dataset.fill_snapshots

# Visualize ELO distribution
python -m src.dataset.plotter
```

## Run Tests

```bash
# All tests
pytest tests/dataset/

# With coverage
pytest tests/dataset/ --cov=dataset --cov-report=html

# Specific module
pytest tests/dataset/models/
```

## Structure

```
train/
├── src/
│   └── dataset/           # ETL pipeline for Lichess data
│       ├── models/        # Data classes
│       ├── repositories/  # Database (SQLite)
│       ├── requesters/    # Lichess API
│       ├── processers/    # PGN transformers
│       └── fill_snapshots.py  # Main pipeline
├── tests/dataset/         # 133+ tests
└── docs/                  # Detailed documentation
```

## Database

- **Location**: `./database.sqlite3`
- **Tables**: `files_metadata`, `raw_games`, `game_snapshots`
- **Snapshots**: Board state (64 squares) + metadata per move

## Documentation

See [docs/readme.md](docs/readme.md) for:
- Architecture details
- Usage examples
- Test documentation
- Refactoring history
