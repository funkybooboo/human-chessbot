# Play Package

Interactive chess application with multiple engines and dual interfaces (GUI/CLI).

## Features

- **Engines**: Stockfish, LCZero, Random bot, Human player
- **Interfaces**: Tkinter GUI and CLI
- **Time Controls**: Per-player timers with timeout detection
- **Game Recording**: Automatic PGN export with metadata
- **Visual Feedback**: Move highlighting, material count
- **Statistics**: Win/loss tracking

## Quick Start

```bash
# GUI (default)
python -m packages.play.src.main

# CLI
python -m packages.play.src.main --ui cli

# Custom settings
python -m packages.play.src.main --time-limit 300 --save-dir ~/games
```

## Engine Setup

**Stockfish** (recommended):
```bash
# Linux
sudo apt install stockfish

# macOS
brew install stockfish
```

**LCZero**: See [docs/engine_setup.md](docs/engine_setup.md) for setup.

## Run Tests

```bash
pytest packages/play/tests/ -v
pytest packages/play/tests/ --cov=packages.play --cov-report=html
```

## Structure

```
play/
├── src/
│   ├── main.py          # Application entry point
│   ├── game.py          # Game logic and state
│   ├── engines/         # Chess engine implementations
│   └── ui/              # GUI and CLI interfaces
└── tests/               # 73 tests
```

## Documentation

- [Engine Setup Guide](docs/engine_setup.md)
- [Testing Guide](docs/testing.md)
