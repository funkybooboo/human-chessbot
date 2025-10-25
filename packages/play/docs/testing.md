# Testing Guide

## Running Tests

```bash
# All tests
pytest packages/play/tests/ -v

# With coverage
pytest packages/play/tests/ --cov=packages/play/src --cov-report=html

# Specific test
pytest packages/play/tests/player/test_player.py::TestPlayer::test_initialization

# By pattern
pytest -k "test_player"

# Exclude slow tests
pytest -m "not slow"
```

## Test Structure

```
packages/play/tests/
├── conftest.py          # Shared fixtures
├── player/
│   ├── test_player.py
│   ├── test_human_player.py
│   └── test_random_bot_player.py
├── game/
│   └── test_game.py
└── ui/
    ├── test_ui.py
    └── test_cli.py
```

## Writing Tests

### Example

```python
import pytest
from packages.play.src.player.player import Player, PlayerConfig


class TestPlayer:
    """Tests for Player class."""

    @pytest.fixture
    def player_config(self):
        """Create a player configuration."""
        return PlayerConfig(name="Test", color=True)

    def test_initialization(self, player_config):
        """Test player initialization."""
        player = Player(player_config)
        assert player.config.name == "Test"

    def test_record_win(self, player_config):
        """Test recording wins."""
        player = Player(player_config)
        player.record_win()
        assert player.config.wins == 1
```

### Parametrized Tests

```python
@pytest.mark.parametrize("move_uci,expected_san", [
    ("e2e4", "e4"),
    ("d2d4", "d4"),
    ("g1f3", "Nf3"),
])
def test_move_notation(move_uci, expected_san):
    """Test move notation conversion."""
    board = chess.Board()
    move = chess.Move.from_uci(move_uci)
    assert board.san(move) == expected_san
```

### Mocking

```python
from unittest.mock import patch

def test_with_mock():
    """Test using a mock."""
    with patch('builtins.input', return_value='e2e4'):
        # Test code here
        pass
```

## Test Markers

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.slow          # Slow test
```

## Coverage Goals

- **Overall**: 80%+
- **Critical paths**: 90%+ (game logic, player classes)
- **UI code**: 60%+

View coverage:
```bash
pytest --cov=packages/play/src --cov-report=html
open htmlcov/index.html
```

## Best Practices

1. **One concept per test** - Keep tests focused
2. **Descriptive names** - Test name explains what it tests
3. **Arrange-Act-Assert** - Clear test structure
4. **Use fixtures** - Share setup code
5. **Mock external deps** - Network, filesystem, time
6. **Test edge cases** - Empty inputs, boundaries, errors
7. **Keep tests fast** - Use small data, mock slow operations

## Troubleshooting

### Import errors
Run from project root: `pytest packages/play/tests/`

### GUI tests fail
Skip with: `pytest -k "not gui"`

### Slow execution
Skip slow tests: `pytest -m "not slow"`

## Resources

- [pytest](https://docs.pytest.org/)
- [Python Testing](https://realpython.com/pytest-python-testing/)
