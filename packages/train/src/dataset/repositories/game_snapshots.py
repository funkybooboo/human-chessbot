import sqlite3
from collections.abc import Iterable

from packages.train.src.constants import DB_FILE
from packages.train.src.dataset.models.game_snapshot import GameSnapshot

_TABLE_NAME = "game_snapshots"


def create_game_snapshots_table():
    """Create the 'game_snapshots' table if it does not exist.

    Note: white_elo, black_elo, and result are stored in game_statistics table.
    Join with game_statistics using raw_game_id to get this data.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(
        f"""
    CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_game_id INTEGER,
        move_number INTEGER,
        turn TEXT,
        move TEXT,
        fen TEXT,
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
    """Insert a single GameSnapshot."""
    with sqlite3.connect(DB_FILE, isolation_level=None) as conn:
        c = conn.cursor()

        # Insert
        c.execute(
            f"""
        INSERT INTO {_TABLE_NAME} (
            raw_game_id, move_number, turn, move, fen
        ) VALUES (
            ?, ?, ?, ?, ?
        )
        """,
            (
                snapshot.raw_game_id,
                snapshot.move_number,
                snapshot.turn,
                snapshot.move,
                snapshot.fen,
            ),
        )


def save_snapshots(snapshots: Iterable[GameSnapshot]):
    """Insert multiple snapshots one by one."""
    for snapshot in snapshots:
        save_snapshot(snapshot)


def save_snapshots_batch(snapshots: list[GameSnapshot]):
    """
    Insert multiple snapshots in a single transaction for better performance.
    """
    if not snapshots:
        return

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        # Prepare data for batch insert
        data = [
            (
                snapshot.raw_game_id,
                snapshot.move_number,
                snapshot.turn,
                snapshot.move,
                snapshot.fen,
            )
            for snapshot in snapshots
        ]

        # Batch insert all snapshots
        c.executemany(
            f"""
            INSERT INTO {_TABLE_NAME} (
                raw_game_id, move_number, turn, move, fen
            ) VALUES (?, ?, ?, ?, ?)
            """,
            data,
        )
        conn.commit()


def count_snapshots() -> int:
    """Return the total number of snapshots currently in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM game_snapshots")
        result = c.fetchone()
        count = result[0] if result else 0
    finally:
        conn.close()
    return count


def _row_to_snapshot(row: tuple) -> GameSnapshot:
    """Convert a DB row to a GameSnapshot object."""
    return GameSnapshot(
        raw_game_id=row[1],
        move_number=row[2],
        turn=row[3],
        move=row[4],
        fen=row[5],
    )
