# Dataset Module

Data pipeline for fetching Lichess games, storing in SQLite, and loading for PyTorch training.

## Structure

```
dataset/
  models/        - Data classes (FileMetadata, RawGame, GameSnapshot, GameStatistics, LegalMove)
  repositories/  - SQLite CRUD operations
  requesters/    - Lichess API fetching
  processers/    - PGN parsing and move generation
  fillers/       - Database population scripts
  loaders/       - PyTorch Dataset classes
  plotter.py     - ELO distribution plotting
```

## Data Flow

```
+----------------+      +----------------+      +----------------+      +------------------+
|  Lichess API   |----->| files_metadata |----->|   raw_games    |----->|  game_snapshots  |
| (counts.txt)   |      |     table      |      |     table      |      |      table       |
+----------------+      +----------------+      +-------+--------+      +------------------+
                                                        |
                                                        v
                                                +----------------+
                                                | game_statistics|
                                                |     table      |
                                                +----------------+
```

## Table Relationships

```
+----------------+         +----------------+         +------------------+
| files_metadata |----+    |   raw_games    |----+    |  game_snapshots  |
+----------------+    |    +----------------+    |    +------------------+
| id (PK)        |    |    | id (PK)        |    |    | id (PK)          |
| url            |    +--->| file_id (FK)   |    +--->| raw_game_id (FK) |
| filename       |         | pgn            |    |    | move_number      |
| games          |         | processed      |    |    | turn             |
| size_gb        |         +----------------+    |    | move             |
| processed      |                               |    | fen              |
+----------------+                               |    +------------------+
                                                 |
                                                 |    +------------------+
                                                 |    | game_statistics  |
                                                 |    +------------------+
                                                 |    | id (PK)          |
                                                 +--->| raw_game_id (FK) |
                                                      | white_elo        |
                                                      | black_elo        |
                                                      | result           |
                                                      | opening, eco ... |
                                                      +------------------+
```

## Usage

### Initialize Database

```python
from packages.train.src.dataset.repositories.database import initialize_database
initialize_database()
```

### Populate Legal Moves

```bash
python -m packages.train.src.dataset.fillers.fill_legal_moves
```

### Process Games into Snapshots

```python
from packages.train.src.dataset.processers.game_snapshots import SnapshotBatchProcessor
from packages.train.src.dataset.repositories.raw_games import fetch_unprocessed_raw_games

processor = SnapshotBatchProcessor(batch_size=1000)
processor.process_games(fetch_unprocessed_raw_games())
```

### Load for Training

```python
from torch.utils.data import DataLoader
from packages.train.src.dataset.loaders.game_snapshots import GameSnapshotsDataset

dataset = GameSnapshotsDataset(start_index=0, num_indexes=100000)
loader = DataLoader(dataset, batch_size=64, shuffle=True)

for labels, move_idx in loader:
    # labels: (batch, 772) - [elo_2, turn_2, board_768]
    # move_idx: (batch,) - index into legal_moves
    pass
```

### Plot ELO Distribution

```bash
python -m packages.train.src.dataset.plotter --bins 50 -o elo_dist.png
```

## Board Encoding

```
Input: FEN string "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

Output: 772-dimensional tensor

+-------+-------+-------+-----------+
| ELO   | Turn  | Board | Total     |
+-------+-------+-------+-----------+
|   2   |   2   |  768  |    772    |
+-------+-------+-------+-----------+

Board (768 = 8 x 8 x 12):
  - Channels 0-5:  White pieces (P, N, B, R, Q, K)
  - Channels 6-11: Black pieces (p, n, b, r, q, k)

ELO: Z-normalized (mean=1638.43, std=185.80)
Turn: One-hot [white, black]
```

## Configuration

Set via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| DB_FILE | database.sqlite3 | SQLite database path |
| MIN_ELO | 600 | Minimum ELO filter |
| MAX_ELO | 1900 | Maximum ELO filter |
| DEFAULT_BATCH_SIZE | 1000 | DB write batch size |
