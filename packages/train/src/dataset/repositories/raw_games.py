import sqlite3
from collections.abc import Iterator

from packages.train.src.constants import DB_FILE
from packages.train.src.dataset.models.raw_game import RawGame

_TABLE_NAME = "raw_games"


def create_raw_games_table():
    """Create the 'raw_games' table if it does not exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        f"""
    CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER,
        pgn TEXT NOT NULL,
        processed INTEGER DEFAULT 0,
        FOREIGN KEY(file_id) REFERENCES files_metadata(id)
    )
    """
    )
    conn.commit()
    conn.close()


def raw_games_table_exists() -> bool:
    """Return True if the table exists in the database."""
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


def save_raw_game(game: RawGame):
    """Insert a single RawGame into the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(
        f"""
    INSERT INTO {_TABLE_NAME} (file_id, pgn, processed)
    VALUES (?, ?, ?)
    """,
        (game.file_id, game.pgn, int(getattr(game, "processed", 0))),
    )
    conn.commit()
    conn.close()


def save_raw_games(games: list[RawGame]):
    """Insert multiple RawGame objects."""
    for game in games:
        save_raw_game(game)


def save_raw_games_batch(games: list[RawGame]):
    """
    Insert multiple RawGame objects in a single transaction for better performance.
    """
    if not games:
        return

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        # Prepare data for batch insert
        data = [
            (
                game.file_id,
                game.pgn,
                int(getattr(game, "processed", 0)),
            )
            for game in games
        ]

        # Batch insert all games
        c.executemany(
            f"""
            INSERT INTO {_TABLE_NAME} (file_id, pgn, processed)
            VALUES (?, ?, ?)
            """,
            data,
        )
        conn.commit()


def mark_raw_game_as_processed(game: RawGame):
    """Mark a RawGame as processed in the DB."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"UPDATE {_TABLE_NAME} SET processed = 1 WHERE id = ?", (game.id,))
    conn.commit()
    conn.close()
    game.processed = True


def fetch_raw_games(file_id: int | None = None) -> list[RawGame]:
    """Fetch all raw games, optionally filtered by file_id."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        if file_id is not None:
            c.execute(
                f"SELECT id, file_id, pgn, processed FROM {_TABLE_NAME} WHERE file_id = ?",
                (file_id,),
            )
        else:
            c.execute(f"SELECT id, file_id, pgn, processed FROM {_TABLE_NAME}")
        rows = c.fetchall()
    finally:
        conn.close()
    return [_row_to_raw_game(row) for row in rows]


def fetch_unprocessed_raw_games(file_id: int | None = None) -> Iterator[RawGame]:
    """Yield RawGame objects that have not yet been processed into snapshots."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        if file_id is not None:
            c.execute(
                f"SELECT id, file_id, pgn, processed FROM {_TABLE_NAME} WHERE file_id = ? AND processed = 0",
                (file_id,),
            )
        else:
            c.execute(
                f"SELECT id, file_id, pgn, processed FROM {_TABLE_NAME} WHERE processed = 0"
            )
        rows = c.fetchall()
    finally:
        conn.close()
    for row in rows:
        yield _row_to_raw_game(row)


def _row_to_raw_game(row: tuple) -> RawGame:
    """Convert a database row tuple into a RawGame object."""
    return RawGame(id=row[0], file_id=row[1], pgn=row[2], processed=bool(row[3]))
