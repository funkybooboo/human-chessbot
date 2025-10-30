# Chess Engine Setup

Setup guide for Stockfish and LCZero chess engines.

## Stockfish

### Installation

```bash
sudo apt install stockfish  # Linux (Debian/Ubuntu)
brew install stockfish      # macOS
# Windows: Download from stockfishchess.org and add to PATH
```

Verify: Run `stockfish` (type `quit` to exit)

### Configuration

```python
from packages.play.src.player.stockfish_bot_player import StockfishPlayer, StockfishPlayerConfig

player = StockfishPlayer(
    config=StockfishPlayerConfig(
        name="Stockfish",
        color=True,
        skill_level=10,  # 0-20 (20 = strongest)
        time_limit=0.5   # Seconds per move
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

Verify: Run `lc0` (type `quit` to exit)

### Configuration

```python
from packages.play.src.player.lc0_bot_player import Lc0BotPlayer, Lc0BotPlayerConfig

player = Lc0BotPlayer(
    config=Lc0BotPlayerConfig(
        name="Leela",
        color=False,
        time_limit=1.0  # Seconds per move
    )
)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Engine not found | Verify `stockfish` or `lc0` runs in terminal; check PATH |
| LCZero network missing | Ensure `.pb.gz` file in `~/.local/share/lc0/networks/` |
| Slow performance | Increase `time_limit` or lower Stockfish `skill_level` |
| Path not updated | Restart terminal after PATH changes |

## Engine Comparison

| Feature | Stockfish | LCZero |
|---------|-----------|---------|
| **Style** | Tactical, deep calculation | Positional, strategic |
| **Strengths** | Tactics, endgames | Positional play, creativity |
| **Hardware** | CPU-based | CPU/GPU (GPU optional) |
| **Best for** | Tactical analysis | Strategic learning |

## Resources

- [Stockfish GitHub](https://github.com/official-stockfish/Stockfish)
- [LCZero Wiki](https://lczero.org/dev/wiki/)
- [UCI Protocol Spec](http://wbec-ridderkerk.nl/html/UCIProtocol.html)
