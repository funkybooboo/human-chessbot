# Chess Engine Setup

## Stockfish

### Installation

```bash
# Linux (Debian/Ubuntu)
sudo apt install stockfish

# macOS
brew install stockfish

# Windows: Download from stockfishchess.org and add to PATH
```

Verify: `stockfish` (type `quit` to exit)

### Usage

```python
from packages.play.src.player.stockfish_bot_player import StockfishPlayer, StockfishPlayerConfig

player = StockfishPlayer(
    config=StockfishPlayerConfig(
        name="Stockfish",
        color=True,
        skill_level=10,  # 0-20
        time_limit=0.5   # seconds per move
    )
)
```

## LCZero

### Installation

1. **Download binary** from [lczero.org/play/download](https://lczero.org/play/download/)

2. **Install binary**:
   ```bash
   # Linux/macOS
   chmod +x lc0
   mv lc0 ~/bin/
   export PATH="$HOME/bin:$PATH"

   # Windows: Add lc0.exe directory to PATH
   ```

3. **Download neural network** from [bestnets](https://lczero.org/play/networks/bestnets/):
   ```bash
   mkdir -p ~/.local/share/lc0/networks
   cp latest.pb.gz ~/.local/share/lc0/networks/
   ```

Verify: `lc0` (type `quit` to exit)

### Usage

```python
from packages.play.src.player.lc0_bot_player import Lc0BotPlayer, Lc0BotPlayerConfig

player = Lc0BotPlayer(
    config=Lc0BotPlayerConfig(
        name="Leela",
        color=False,
        time_limit=1.0
    )
)
```

## Troubleshooting

### Engine not found
- Verify: `stockfish` or `lc0` in terminal
- Check engine directory is in PATH
- Restart terminal after PATH changes

### LCZero network not found
- Verify network file in `~/.local/share/lc0/networks/`
- File format: `.pb.gz` or `.pb`
- Try downloading a different network

### Performance issues
- **Stockfish**: Lower skill_level or increase time_limit
- **LCZero**: Use smaller network or increase time_limit

## Engine Comparison

| Feature | Stockfish | LCZero |
|---------|-----------|---------|
| **Style** | Tactical, calculates deep | Positional, strategic |
| **Strengths** | Concrete moves, endgames | Strategic positions, creativity |
| **Resources** | CPU-based, moderate | CPU/GPU, can use GPU acceleration |
| **Best for** | Tactical puzzles, analysis | Positional play, learning strategy |

## Resources

- [Stockfish](https://github.com/official-stockfish/Stockfish)
- [LCZero Wiki](https://lczero.org/dev/wiki/)
- [UCI Protocol](http://wbec-ridderkerk.nl/html/UCIProtocol.html)
