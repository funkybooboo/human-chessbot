# Development Guide

Detailed setup and workflow for contributors.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
pre-commit install
pytest packages/*/tests/ -v  # Verify setup
```

## Project Structure

```
human-chessbot/
├── packages/
│   ├── play/       # Chess game application
│   ├── convert/    # PGN conversion utilities
│   └── train/      # ML training and dataset ETL
├── docs/           # Documentation
└── pyproject.toml  # Project configuration
```

## Workflow

```bash
git checkout -b feature/my-feature  # Create branch
# Make changes
git add .
git commit -m "Add feature X"       # Pre-commit hooks run automatically
# If hooks fail, review changes and recommit
```

## Tools

### Pre-commit Hooks

Auto-run on commit. Manual usage:

```bash
pre-commit run --all-files              # All hooks
pre-commit run --files path/to/file.py  # Specific files
pre-commit autoupdate                   # Update versions
```

### Testing

```bash
pytest packages/*/tests/ -v                  # All tests
pytest packages/play/tests/ -v               # Specific package
pytest --cov=packages --cov-report=html      # With coverage
pytest -k "test_name"                        # By pattern
pytest tests/path/test.py::test_function     # Specific test
```

**Coverage targets**: 80%+ overall, 90%+ for critical paths

### Linting & Formatting

```bash
ruff check packages/        # Lint
ruff check --fix packages/  # Auto-fix
black packages/             # Format
isort packages/             # Sort imports
mypy packages/              # Type check
```

## Code Style

- **Line length**: 100 characters
- **Python**: 3.11+
- **Type hints**: Required for functions
- **Docstrings**: Required for public APIs

### Import Order

```python
# 1. Standard library
import logging
from typing import Optional

# 2. Third-party
import chess
from pydantic import BaseModel

# 3. Local
from packages.play.src.game.game import Game
```

### Docstrings (Google style)

```python
def apply_move(self, move: chess.Move) -> str:
    """Apply a move to the board.

    Args:
        move: Chess move to apply

    Returns:
        Move in SAN notation

    Raises:
        ValueError: If move is illegal
    """
```

## Common Tasks

### Add Dependency

Edit `pyproject.toml` dependencies section, then:
```bash
pip install -e .
```

### Add Module

1. Create module with type hints and docstrings
2. Write tests in `tests/` directory
3. Update package README

### Add Package

```bash
mkdir -p packages/mypackage/{src/mypackage,tests,docs}
touch packages/mypackage/README.md
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | `pip install -e .` |
| Test failures | `rm -rf .pytest_cache && pip install -e .` |
| Formatting conflicts | `pre-commit run --all-files` |
| Type errors | `mypy packages/` to identify issues |

## Resources

- [Black](https://black.readthedocs.io/) - Code formatter
- [Ruff](https://docs.astral.sh/ruff/) - Linter
- [mypy](http://mypy-lang.org/) - Type checker
- [pytest](https://docs.pytest.org/) - Testing framework
- [Pre-commit](https://pre-commit.com/) - Git hooks
