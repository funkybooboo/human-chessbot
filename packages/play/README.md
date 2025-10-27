# Play Package

Interactive chess application with multiple engines and interfaces.

## Features

- **Engines**: Stockfish, LCZero, Random bot, Human player
- **Interfaces**: Tkinter GUI and CLI
- **Time Controls**: Per-player timers with timeout detection
- **Game Recording**: Automatic PGN export with metadata
- **Visual Features**: Move highlighting, material count, win/loss tracking

## Usage

```bash
python -m packages.play.src.main              # GUI (default)
python -m packages.play.src.main --ui cli     # CLI
python -m packages.play.src.main --time-limit 300 --save-dir ~/games
```

## Engine Setup

**Stockfish** (recommended):
```bash
sudo apt install stockfish  # Linux
brew install stockfish      # macOS
```

**LCZero**: See [docs/engine_setup.md](docs/engine_setup.md)

## Testing

```bash
pytest packages/play/tests/ -v
pytest packages/play/tests/ --cov=packages.play --cov-report=html
```

## Structure

```
play/
├── src/
│   ├── main.py      # Entry point
│   ├── game/        # Game logic and state
│   ├── player/      # Player implementations (human, bots)
│   └── ui/          # GUI and CLI
└── tests/           # Test suite
```

## Documentation

- [Engine Setup Guide](docs/engine_setup.md) - Stockfish and LCZero installation
- [Testing Guide](docs/testing.md) - Testing best practices
