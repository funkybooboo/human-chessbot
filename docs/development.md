# Development Guide

## Quick Start

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install

# Verify
pytest packages/*/tests/ -v  # Should pass 101 tests
```

## Project Structure

```
the_human_chess_bot/
├── packages/
│   ├── play/       # Chess game application
│   ├── convert/    # Data conversion utilities
│   └── train/      # ML training (planned)
├── docs/           # Documentation
└── pyproject.toml  # Configuration
```

## Development Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, then commit (pre-commit hooks run automatically)
git add .
git commit -m "Add feature X"

# If hooks fail, they auto-fix issues - review and commit again
git add .
git commit -m "Add feature X"
```

## Tools

### Pre-commit Hooks

Automatically run on commit. Manual usage:

```bash
pre-commit run --all-files              # Run all hooks
pre-commit run --files path/to/file.py  # Run on specific files
pre-commit autoupdate                   # Update hook versions
```

### Testing

```bash
pytest packages/*/tests/ -v                  # All tests
pytest packages/play/tests/ -v               # Specific package
pytest --cov=packages --cov-report=html      # With coverage
pytest -vv --tb=long                         # Verbose debugging
pytest -s tests/path/test.py::test_function  # Specific test
```

Target coverage: 80%+ overall, 90%+ for critical paths.

### Linting & Formatting

```bash
ruff check packages/           # Lint
ruff check --fix packages/     # Lint with auto-fix
black packages/                # Format
isort packages/                # Sort imports
mypy packages/                 # Type check
```

## Code Style

**Line length:** 100 characters
**Python version:** 3.11+
**Type hints:** Required
**Docstrings:** Required for public APIs

### Import Order

```python
# Standard library
import logging
from typing import Optional

# Third-party
import chess
from pydantic import BaseModel

# Local
from packages.play.src.game.game import Game
```

### Docstring Format

```python
def apply_move(self, move: chess.Move) -> str:
    """Apply a move to the board.

    Args:
        move: The chess move to apply.

    Returns:
        The move in SAN notation.

    Raises:
        ValueError: If move is illegal.
    """
```

### Error Handling

Use specific exceptions:

```python
try:
    engine.quit()
except EngineTerminatedError as e:
    logger.warning(f"Engine already closed: {e}")
```

## Common Tasks

### Add Dependency

```toml
# Edit pyproject.toml
dependencies = [
    "newpackage>=1.0.0",
]
```

```bash
pip install -e ".[dev]"
```

### Add Module

1. Create module file with docstrings and type hints
2. Write tests
3. Update package README

### Add Package

```bash
mkdir -p packages/mypackage/{src/mypackage,tests,docs}
touch packages/mypackage/README.md
```

## Troubleshooting

### Import Errors

```bash
pip install -e ".[dev]"
```

### Test Failures

```bash
rm -rf .pytest_cache
pip install -e ".[dev]"
pytest
```

### Formatting Conflicts

```bash
pre-commit run --all-files
```

## Resources

- [Black](https://black.readthedocs.io/)
- [Ruff](https://docs.astral.sh/ruff/)
- [mypy](http://mypy-lang.org/)
- [pytest](https://docs.pytest.org/)
- [Pre-commit](https://pre-commit.com/)
