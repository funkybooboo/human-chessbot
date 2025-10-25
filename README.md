# The Human Chess Bot

A comprehensive chess application suite featuring multiple chess engines, data conversion tools, and machine learning training utilities.

## Features

- Interactive chess game with GUI and CLI interfaces
- Multiple chess engines (Stockfish, LCZero, Random bot)
- PGN file conversion and processing utilities
- Time controls and game recording
- Comprehensive test coverage (101 tests, 100% passing)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/the_human_chess_bot.git
cd the_human_chess_bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the project with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running the Chess Application

```bash
# GUI (default)
python -m packages.play.src.main

# CLI
python -m packages.play.src.main --ui cli

# With custom settings
python -m packages.play.src.main --time-limit 300 --save-dir ~/my_games
```

## Project Structure

```
the_human_chess_bot/
├── packages/
│   ├── play/          # Chess game application
│   ├── convert/       # Data conversion utilities
│   └── train/         # ML training tools (planned)
├── docs/              # Project-wide documentation
├── pyproject.toml     # Project configuration
└── README.md
```

## Packages

### Play Package
Interactive chess application with multiple engines and dual interfaces.
- 73 tests, 100% passing
- [Documentation](packages/play/README.md)

### Convert Package
Data conversion utilities for chess formats (PGN to CSV, file combination).
- 28 tests, 100% passing
- [Documentation](packages/convert/README.md)

### Train Package (Coming Soon)
Machine learning training pipeline for chess AI.
- [Documentation](packages/train/README.md)

## Development

### Running Tests

```bash
# All tests
pytest packages/*/tests/ -v

# Specific package
pytest packages/play/tests/ -v
pytest packages/convert/tests/ -v

# With coverage
pytest packages/*/tests/ --cov=packages --cov-report=html
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality before commits:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Hooks will now run automatically on git commit
# To run manually:
pre-commit run --all-files
```

**Included hooks**:
- **ruff**: Fast Python linter with auto-fix
- **ruff-format**: Fast Python formatter
- **black**: Code formatter
- **isort**: Import sorter
- **mypy**: Type checker
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **check-yaml/json/toml**: Validate config files
- **check-merge-conflict**: Detect merge conflicts
- **debug-statements**: Detect debug statements

### Manual Code Quality Checks

```bash
# Format code
black packages/
isort packages/
ruff format packages/

# Lint
ruff check packages/

# Type check
mypy packages/ --ignore-missing-imports

# Run all checks manually
pre-commit run --all-files

# Run tests
pytest packages/*/tests/ -v
```

## Requirements

- Python 3.11 or higher
- Dependencies listed in `pyproject.toml`
- Optional: Stockfish and/or LCZero chess engines

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install pre-commit hooks (`pre-commit install`)
4. Make your changes
5. Run tests (`pytest packages/*/tests/ -v`)
6. Commit your changes (pre-commit hooks will run automatically)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Contribution Guidelines

- Write tests for new features (maintain >90% coverage)
- Follow existing code style (Black, isort, ruff)
- Update documentation as needed
- Ensure pre-commit hooks pass before committing
- All tests must pass

## Documentation

- [Play Package Documentation](packages/play/README.md)
- [Convert Package Documentation](packages/convert/README.md)

## License

This project is part of the Human Chess Bot suite.
