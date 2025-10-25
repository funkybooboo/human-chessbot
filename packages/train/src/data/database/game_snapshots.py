import sqlite3
from collections.abc import Iterable

from packages.train.src.data.database.config import DB_FILE
from packages.train.src.data.models.game_snapshot import GameSnapshot

_TABLE_NAME = "game_snapshots"


def create_game_snapshots_table():
    """Create the 'game_snapshots' table if it does not exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 64 board columns + metadata + unique hash
    board_columns = ",\n".join([f"square_{i} INTEGER" for i in range(64)])

    c.execute(
        f"""
    CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_game_id INTEGER,
        move_number INTEGER,
        turn TEXT,
        move TEXT,
        {board_columns},
        board_hash TEXT NOT NULL UNIQUE,
        white_player TEXT,
        black_player TEXT,
        white_elo INTEGER,
        black_elo INTEGER,
        result TEXT,
        FOREIGN KEY(raw_game_id) REFERENCES raw_games(id)
    )
    """
    )
    conn.commit()
    conn.close()


def game_snapshots_table_exists() -> bool:
    """Return True if the table exists."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute(
            f"""
        SELECT name FROM sqlite_master WHERE type='table' AND name='{_TABLE_NAME}';
        """
        )
        exists = c.fetchone() is not None
    finally:
        conn.close()
    return exists


def save_snapshot(snapshot: GameSnapshot):
    """Insert a single GameSnapshot if it doesn't already exist (by board_hash)."""
    with sqlite3.connect(DB_FILE, isolation_level=None) as conn:
        c = conn.cursor()

        # Skip if snapshot already exists
        c.execute(f"SELECT 1 FROM {_TABLE_NAME} WHERE board_hash = ?", (snapshot.board_hash,))
        if c.fetchone():
            return

        # Insert
        board_values = tuple(snapshot.board)
        c.execute(
            f"""
        INSERT INTO {_TABLE_NAME} (
            raw_game_id, move_number, turn, move,
            {', '.join([f'square_{i}' for i in range(64)])},
            board_hash, white_player, black_player, white_elo, black_elo, result
        ) VALUES (
            ?, ?, ?, ?, {', '.join(['?'] * 64)}, ?, ?, ?, ?, ?, ?
        )
        """,
            (
                snapshot.raw_game_id,
                snapshot.move_number,
                snapshot.turn,
                snapshot.move,
                *board_values,
                snapshot.board_hash,
                snapshot.white_player,
                snapshot.black_player,
                snapshot.white_elo,
                snapshot.black_elo,
                snapshot.result,
            ),
        )


def save_snapshots(snapshots: Iterable[GameSnapshot]):
    """Insert multiple snapshots one by one."""
    for snapshot in snapshots:
        save_snapshot(snapshot)


def count_snapshots() -> int:
    """Return the total number of snapshots currently in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM game_snapshots")
        count = c.fetchone()[0]
    finally:
        conn.close()
    return count


def _row_to_snapshot(row: tuple) -> GameSnapshot:
    """Convert a DB row to a GameSnapshot object."""
    board = list(row[5:69])  # 64 squares
    return GameSnapshot(
        raw_game_id=row[1],
        move_number=row[2],
        turn=row[3],
        move=row[4],
        board=board,
        board_hash=row[69],
        white_player=row[70],
        black_player=row[71],
        white_elo=row[72],
        black_elo=row[73],
        result=row[74],
    )
