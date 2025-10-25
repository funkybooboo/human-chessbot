# Convert Package

Data conversion utilities for chess data formats, providing tools to transform chess game records between different formats.

## Features

### PGN File Combination
Combine multiple PGN (Portable Game Notation) files into a single file with proper formatting.

**Features:**
- Combines two PGN files while maintaining proper game separation
- Validates input files exist before processing
- Automatically creates output directories if needed
- Optional deletion of original files after combining
- Preserves game order and formatting

**Usage:**
```python
from packages.convert.src.combine_pgn_files import PGNCombineConfig, combine_pgn_files

config = PGNCombineConfig(
    pgn1_path="game1.pgn",
    pgn2_path="game2.pgn",
    output_path="combined.pgn",
    delete_old=False
)
combine_pgn_files(config)
```

**CLI:**
```bash
python -m packages.convert.src.combine_pgn_files game1.pgn game2.pgn output.pgn [--delete-old]
```

### PGN to CSV Conversion
Convert PGN files to CSV format for machine learning and data analysis.

**Features:**
- Converts PGN games to CSV with board positions and moves
- Supports Zstandard (.zst) compressed PGN files
- Extracts player Elo ratings
- Tracks move turn (white/black)
- Represents board state as 64 integers (one per square)
- Verbose mode for progress tracking

**Board Representation:**
Each square is represented by an integer:
- 0 = empty square
- White pieces: P=1, N=2, B=3, R=4, Q=5, K=6
- Black pieces: p=7, n=8, b=9, r=10, q=11, k=12

**CSV Format:**
```
white_elo,black_elo,blacks_move,A1,A2,...,H8,selected_move
2000,1950,0,4,1,0,...,10,e2e4
```

**Usage:**
```python
from packages.convert.src.pgn_to_csv import PGNToCSVConfig, convert_pgn_to_csv

config = PGNToCSVConfig(
    source_path="games.pgn",
    destination_path="games.csv",
    verbose=True
)
convert_pgn_to_csv(config)
```

**CLI:**
```bash
python -m packages.convert.src.pgn_to_csv games.pgn games.csv [--verbose]
```

## Installation

Ensure you have the required dependencies:

```bash
pip install chess pydantic zstandard
```

Or install the entire project:

```bash
pip install -e .
```

## Structure

```
convert/
├── src/
│   ├── __init__.py                # Package exports
│   ├── combine_pgn_files.py       # PGN combination utility
│   └── pgn_to_csv.py              # PGN to CSV converter
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration
│   ├── test_combine_pgn_files.py  # Tests for PGN combination
│   └── test_pgn_to_csv.py         # Tests for CSV conversion
├── docs/                           # Additional documentation
└── README.md
```

## Testing

The package has comprehensive test coverage (88% overall):

```bash
# Run all tests
pytest packages/convert/tests/ -v

# Run with coverage report
pytest packages/convert/tests/ --cov=packages/convert/src --cov-report=term

# Run specific test file
pytest packages/convert/tests/test_combine_pgn_files.py -v
```

**Test Statistics:**
- 28 total tests
- 10 tests for PGN combination
- 18 tests for PGN to CSV conversion
- 100% pass rate

## Development

### Code Quality

The codebase follows strict quality standards enforced by pre-commit hooks:

```bash
# Install pre-commit hooks (from project root)
pre-commit install

# Run manually on convert package
pre-commit run --files packages/convert/**/*

# Or run specific tools
ruff check packages/convert/
black packages/convert/
isort packages/convert/
mypy packages/convert/src/
```

### Code Style

- Line length: 100 characters
- Python version: 3.11+
- Type hints required
- Docstrings for all public functions/classes
- Follows PEP 8 with Black formatting

## Examples

### Combining Multiple Tournament Files

```python
from pathlib import Path
from packages.convert.src.combine_pgn_files import PGNCombineConfig, combine_pgn_files

# Combine tournament rounds
config = PGNCombineConfig(
    pgn1_path=Path("tournament_round1.pgn"),
    pgn2_path=Path("tournament_round2.pgn"),
    output_path=Path("tournament_complete.pgn")
)
combine_pgn_files(config)
```

### Converting Games for ML Training

```python
from packages.convert.src.pgn_to_csv import PGNToCSVConfig, convert_pgn_to_csv

# Convert large compressed file to CSV
config = PGNToCSVConfig(
    source_path="lichess_games.pgn.zst",
    destination_path="training_data.csv",
    verbose=True  # Show progress
)
convert_pgn_to_csv(config)
```

## API Reference

### PGNCombineConfig

Configuration for combining PGN files.

**Attributes:**
- `pgn1_path: Path` - Path to first PGN file
- `pgn2_path: Path` - Path to second PGN file
- `output_path: Path` - Output file path
- `delete_old: bool` - Delete originals after combining (default: False)

### PGNToCSVConfig

Configuration for PGN to CSV conversion.

**Attributes:**
- `source_path: Path` - Source PGN file (.pgn or .zst)
- `destination_path: Path` - Destination CSV file
- `verbose: bool` - Print progress (default: False)

### GameMetadata

Metadata for a chess game.

**Attributes:**
- `white_elo: str` - White player's Elo rating
- `black_elo: str` - Black player's Elo rating
- `is_black: bool` - True if current move is black's

## Contributing

When contributing to this package:

1. Install pre-commit hooks (`pre-commit install`)
2. Write tests for new features
3. Maintain or improve test coverage
4. Follow the existing code style (enforced by pre-commit)
5. Update documentation
6. Run the full test suite before submitting
7. Pre-commit hooks will run automatically on commit

## License

Part of the Human Chess Bot project.
