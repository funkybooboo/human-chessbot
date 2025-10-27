# Testing Guide

Comprehensive testing practices for the play package.

## Running Tests

```bash
pytest packages/play/tests/ -v                              # All tests
pytest packages/play/tests/ --cov=packages/play/src --cov-report=html  # With coverage
pytest packages/play/tests/player/test_player.py::TestPlayer::test_initialization  # Specific test
pytest -k "test_player"                                     # By pattern
pytest -m "not slow"                                        # Exclude slow tests
```

## Test Structure

```
packages/play/tests/
├── conftest.py          # Shared fixtures
├── player/              # Player tests
├── game/                # Game logic tests
└── ui/                  # UI tests
```

## Writing Tests

### Basic Example

```python
import pytest
from packages.play.src.player.player import Player, PlayerConfig

class TestPlayer:
    @pytest.fixture
    def player_config(self):
        return PlayerConfig(name="Test", color=True)

    def test_initialization(self, player_config):
        player = Player(player_config)
        assert player.config.name == "Test"
```

### Parametrized Tests

```python
@pytest.mark.parametrize("move_uci,expected_san", [
    ("e2e4", "e4"),
    ("d2d4", "d4"),
    ("g1f3", "Nf3"),
])
def test_move_notation(move_uci, expected_san):
    board = chess.Board()
    move = chess.Move.from_uci(move_uci)
    assert board.san(move) == expected_san
```

### Mocking

```python
from unittest.mock import patch

def test_with_mock():
    with patch('builtins.input', return_value='e2e4'):
        # Test code
        pass
```

## Test Markers

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.slow          # Slow test
```

## Coverage Targets

- **Overall**: 80%+
- **Critical paths**: 90%+ (game logic, player classes)
- **UI code**: 60%+

View coverage report:
```bash
pytest --cov=packages/play/src --cov-report=html
open htmlcov/index.html
```

## Best Practices

1. **One concept per test** - Keep focused
2. **Descriptive names** - Explain what's being tested
3. **Arrange-Act-Assert** - Clear structure
4. **Use fixtures** - Share setup code
5. **Mock external dependencies** - Network, filesystem, time
6. **Test edge cases** - Empty inputs, boundaries, errors
7. **Keep tests fast** - Mock slow operations

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Run from project root: `pytest packages/play/tests/` |
| GUI tests fail | Skip with: `pytest -k "not gui"` |
| Slow execution | Skip slow tests: `pytest -m "not slow"` |

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Real Python Testing Guide](https://realpython.com/pytest-python-testing/)
