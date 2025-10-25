# Play Package

Interactive chess application with multiple engine support and dual user interfaces (GUI and CLI).

## Features

- **Multiple Engines**: Stockfish, LCZero (Leela Chess Zero), Random bot, Human player
- **Dual Interfaces**: Graphical (Tkinter) and Command-line
- **Time Controls**: Configurable per-player timers with timeout detection
- **Game Recording**: Automatic PGN export with metadata and move history
- **Visual Feedback**: Move highlighting (legal moves, last move, selected piece), material count display
- **Statistics**: Win/loss tracking for each player
- **Move Validation**: Legal move checking in both interfaces
- **Drag-and-Drop**: GUI supports intuitive drag-and-drop move input
- **Piece Images**: High-quality piece images from chess.com (cached locally)

## Installation

### Requirements

```bash
pip install chess pydantic pillow
```

### Optional: Chess Engines

For AI opponents, install one or more chess engines:

**Stockfish** (recommended):
```bash
# Linux
sudo apt install stockfish

# macOS
brew install stockfish

# Verify installation
which stockfish
```

**LCZero** (advanced):
- Requires separate installation and neural network weights
- See [docs/engine_setup.md](docs/engine_setup.md) for detailed setup

## Usage

### Running the Application

```bash
# GUI (default)
python -m packages.play.src.main

# CLI
python -m packages.play.src.main --ui cli

# Custom settings
python -m packages.play.src.main --ui gui --time-limit 300 --save-dir ~/my_games

# Show all options
python -m packages.play.src.main --help
```

### Command-Line Options

```
--ui {gui,cli}         Interface type (default: gui)
--save-dir PATH        Directory for PGN files (default: ~/chess_games/pgn)
--time-limit SECONDS   Time per player in seconds (default: 600)
--log-level LEVEL      Logging level: DEBUG, INFO, WARNING, ERROR
```

## How It Works

The application randomly assigns Stockfish and LCZero (if available) to play against each other, alternating colors between games. The game:

1. Initializes players with default configurations
2. Creates a game instance with time controls
3. Launches the selected UI (GUI or CLI)
4. Manages the game loop with automatic move execution for bots
5. Saves completed games to PGN format

## Architecture

### Game Module (`src/game/`)

**game.py**:
- `GameConfig`: Configuration for game settings (save directory, time limit)
- `Game`: Main game controller managing board state, players, timers, and move history
  - `apply_move()`: Apply moves and track captures
  - `update_timer()`: Manage time controls and detect timeouts
  - `get_scores()`: Calculate material scores
  - `is_over()`: Check for game end conditions
  - `save_game()`: Export to PGN format

**Piece Values**: Pawn=1, Knight=3, Bishop=3, Rook=5, Queen=9, King=0

### Player Module (`src/player/`)

**player.py**: Abstract base class defining player interface
- `PlayerConfig`: Configuration with name, color, wins, losses
- `Player`: Abstract class with `get_move(board)` method

**Implementations**:
- `HumanPlayer`: Receives moves from UI interaction
- `RandomBotPlayer`: Selects random legal moves
- `StockfishPlayer`: Integrates Stockfish UCI engine (configurable skill level 0-20)
- `Lc0BotPlayer`: Integrates LCZero neural network engine

### UI Module (`src/ui/`)

**ui.py**: Abstract base class for user interfaces
- `run()`: Start game loop
- `display_board()`: Render board state
- `show_message()`: Display messages
- `update_scores()`: Update material count
- `update_move_list()`: Add moves to history
- `reset_ui()`: Reset display

**Implementations**:
- `Cli`: Terminal-based interface with ASCII board, UCI move input
- `Gui`: Tkinter-based graphical interface with drag-and-drop, piece images, move highlighting

## Testing

### Running Tests

```bash
# Run all tests
pytest packages/play/tests/ -v

# Run with coverage
pytest packages/play/tests/ --cov=packages/play/src --cov-report=term

# Run specific test file
pytest packages/play/tests/game/test_game.py -v

# Run specific test
pytest packages/play/tests/game/test_game.py::TestGame::test_apply_move -v
```

### Test Statistics

- **Total Tests**: 73
- **Pass Rate**: 100%
- **Coverage**: 100% for tested modules (game, player implementations, UI base classes)

**Test Breakdown**:
- Game logic: 29 tests
- Players: 21 tests
- UI: 23 tests

### Test Coverage by Module

| Module | Coverage |
|--------|----------|
| game.py | 100% |
| player.py | 100% |
| human_player.py | 100% |
| random_bot_player.py | 100% |
| cli.py | 59% (core functionality tested) |
| ui.py | 100% |
| main.py | 0% (entry point, requires manual testing) |
| gui.py | 0% (requires GUI environment) |
| stockfish_bot_player.py | 0% (requires external binary) |
| lc0_bot_player.py | 0% (requires external binary) |

## Package Structure

```
play/
├── src/
│   ├── main.py                      # Application entry point
│   ├── game/
│   │   ├── __init__.py
│   │   └── game.py                  # Game logic and state management
│   ├── player/
│   │   ├── __init__.py
│   │   ├── player.py                # Abstract player base class
│   │   ├── human_player.py          # Human player implementation
│   │   ├── random_bot_player.py     # Random move bot
│   │   ├── stockfish_bot_player.py  # Stockfish engine integration
│   │   └── lc0_bot_player.py        # LCZero engine integration
│   └── ui/
│       ├── __init__.py
│       ├── ui.py                    # Abstract UI base class
│       ├── cli.py                   # Command-line interface
│       └── gui.py                   # Graphical interface (Tkinter)
├── tests/
│   ├── conftest.py                  # Pytest configuration and fixtures
│   ├── game/
│   │   └── test_game.py             # Game logic tests
│   ├── player/
│   │   ├── test_player.py           # Base player tests
│   │   ├── test_human_player.py     # Human player tests
│   │   └── test_random_bot_player.py # Random bot tests
│   └── ui/
│       ├── test_ui.py               # Base UI tests
│       └── test_cli.py              # CLI tests
├── docs/
│   ├── engine_setup.md              # Engine installation guide
│   └── testing.md                   # Testing documentation
└── README.md
```

## Development

### Code Quality

The codebase follows strict quality standards enforced by pre-commit hooks:

```bash
# Install pre-commit hooks (from project root)
pre-commit install

# Run manually on play package
pre-commit run --files packages/play/**/*

# Or run specific tools
black packages/play/
ruff check packages/play/ --fix
isort packages/play/
mypy packages/play/src/
```

### Code Style

- Line length: 100 characters
- Python version: 3.11+
- Type hints required for all functions
- Docstrings for all public classes and methods
- Follows PEP 8 with Black formatting

## Troubleshooting

### Engine Not Found

If you see "Stockfish not found" or "LC0 not found":
1. Verify installation: `which stockfish` or `which lc0`
2. Ensure the binary is in your PATH
3. See [docs/engine_setup.md](docs/engine_setup.md) for setup help

### GUI Issues

- **Tkinter not available**: Install python3-tk package
  ```bash
  # Linux
  sudo apt install python3-tk

  # macOS (usually pre-installed)
  brew install python-tk@3.11
  ```

### Permission Errors

- Check write permissions for save directory
- Default: `~/chess_games/pgn/`
- Use `--save-dir` flag to specify custom location

## Contributing

When contributing to this package:

1. Install pre-commit hooks (`pre-commit install`)
2. Write tests for new features
3. Maintain test coverage above 90% for core modules
4. Follow existing code style (enforced by pre-commit)
5. Update documentation
6. Run the full test suite before submitting
7. Pre-commit hooks will run automatically on commit

## License

Part of the Human Chess Bot project.
