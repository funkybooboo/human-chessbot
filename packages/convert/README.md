# Convert Package

Utilities for processing and converting chess game data.

## Features

### PGN File Combination
Combine multiple PGN files with proper formatting:

```bash
python -m packages.convert.src.combine_pgn_files game1.pgn game2.pgn output.pgn [--delete-old]
```

### PGN to CSV Conversion
Convert PGN files to CSV for ML training. Supports compressed (.zst) files.

```bash
python -m packages.convert.src.pgn_to_csv input.pgn output.csv [--verbose]
```

**Python API:**
```python
from packages.convert.src.pgn_to_csv import PGNToCSVConfig, convert_pgn_to_csv

config = PGNToCSVConfig(source="games.pgn", destination="games.csv")
convert_pgn_to_csv(config)
```

**Board Encoding:**
- Empty: 0
- White: P=1, N=2, B=3, R=4, Q=5, K=6
- Black: p=7, n=8, b=9, r=10, q=11, k=12

## Testing

```bash
pytest packages/convert/tests/ -v
pytest packages/convert/tests/ --cov=packages.convert --cov-report=html
```

## Structure

```
convert/
├── src/
│   ├── combine_pgn_files.py  # PGN file merger
│   └── pgn_to_csv.py          # PGN to CSV converter
└── tests/                     # Test suite
```
