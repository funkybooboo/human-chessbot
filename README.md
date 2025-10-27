# The Human Chess Bot

Chess application suite with multiple engines, data processing tools, and ML training utilities.

## Features

- Interactive chess game (GUI and CLI)
- Multiple chess engines (Stockfish, LCZero, Random bot)
- PGN file processing and conversion to CSV
- Lichess data pipeline for ML training
- Time controls and automatic game recording

## Quick Start

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/the_human_chess_bot.git
cd the_human_chess_bot
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
pre-commit install

# Run chess application
python -m packages.play.src.main
```

## Project Structure

```
the_human_chess_bot/
├── packages/
│   ├── play/          # Chess game application
│   ├── convert/       # PGN conversion utilities
│   └── train/         # ML training and dataset pipeline
├── docs/              # Development documentation
└── pyproject.toml
```

## Packages

### [Play](packages/play/README.md)
Interactive chess game with Stockfish, LCZero, and random bot support.

### [Convert](packages/convert/README.md)
PGN file combination and conversion to CSV for ML training.

### [Train](packages/train/README.md)
ML training pipeline and Lichess dataset ETL (in development).

## Development

**Requirements**: Python 3.11+, optional: Stockfish/LCZero engines

### Running Tests

```bash
pytest packages/*/tests/ -v                          # All tests
pytest packages/play/tests/ -v                       # Specific package
pytest packages/*/tests/ --cov=packages --cov-report=html  # With coverage
```

### Code Quality

Pre-commit hooks run automatically on commit (ruff, black, isort, mypy). Run manually:

```bash
pre-commit run --all-files  # All hooks
ruff check packages/        # Lint only
black packages/             # Format only
mypy packages/              # Type check only
```

### Contributing

1. Fork repository and create feature branch
2. Install: `pip install -e ".[dev]" && pre-commit install`
3. Make changes and write tests
4. Ensure hooks and tests pass
5. Submit pull request

**Guidelines**: Write tests for new features, follow existing code style, update docs as needed.

## Documentation

- [Development Guide](docs/development.md) - Detailed setup and workflow
- [Play Package](packages/play/README.md) - Chess game documentation
- [Convert Package](packages/convert/README.md) - Data conversion tools
- [Train Package](packages/train/README.md) - ML training pipeline
