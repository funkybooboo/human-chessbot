import sqlite3

from src.train.data.database.config import DB_FILE
from src.train.data.models.game import RawGame
from typing import List, Optional, Tuple


_TABLE_NAME = "raw_games"


def create_games_table():
    """Create the 'games' table if it does not exist, with unique PGN hash."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS raw_games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER,
        pgn TEXT NOT NULL,
        pgn_hash TEXT NOT NULL UNIQUE,
        FOREIGN KEY(file_id) REFERENCES files_metadata(id)
    )
    """)
    conn.commit()
    conn.close()


def games_table_exists() -> bool:
    """Return True if the 'games' table exists in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='games';
        """)
        exists = c.fetchone() is not None
    finally:
        conn.close()
    return exists


def fetch_file_ids_in_db() -> set[int]:
    """
    Return a set of file_ids that already have games stored in the database.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("SELECT DISTINCT file_id FROM games")
        rows = c.fetchall()
    finally:
        conn.close()
    return {row[0] for row in rows if row[0] is not None}


def save_games(games: List[RawGame]):
    """Insert multiple Game objects, skipping duplicates by pgn_hash."""
    for game in games:
        save_game(game)


def save_game(game: RawGame):
    """Insert a single RawGame into the database if it doesn’t already exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM games WHERE pgn_hash = ?", (game.pgn_hash,))
    if c.fetchone():
        conn.close()
        return  # skip duplicate

    c.execute("""
    INSERT INTO games (file_id, pgn, pgn_hash)
    VALUES (?, ?, ?)
    """, (game.file_id, game.pgn, game.pgn_hash))
    conn.commit()
    conn.close()


def fetch_games(file_id: Optional[int] = None) -> List[RawGame]:
    """
    Fetch games from the database.
    If file_id is provided, fetch only games from that file.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        if file_id is not None:
            c.execute("""
            SELECT id, file_id, pgn, white, black, result, date
            FROM games WHERE file_id = ?
            """, (file_id,))
        else:
            c.execute("""
            SELECT id, file_id, pgn, white, black, result, date
            FROM games
            """)
        rows = c.fetchall()
    finally:
        conn.close()

    return [_row_to_game(row) for row in rows]


def _row_to_game(row: Tuple) -> RawGame:
    """
    Convert a database row tuple into a Game object.
    Expects row in order: (id, file_id, pgn, white, black, result, date)
    """
    return RawGame(
        id=row[0],
        file_id=row[1],
        pgn=row[2],
    )
