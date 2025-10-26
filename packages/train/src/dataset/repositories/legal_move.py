import sqlite3
from collections.abc import Iterable

from packages.train.src.constants import DB_FILE
from packages.train.src.dataset.models.legal_move import LegalMove

_TABLE_NAME = "legal_moves"


def create_legal_moves_table():
    """Create the 'legal_moves' table if it does not exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move TEXT NOT NULL UNIQUE,
            types TEXT NOT NULL  -- comma-separated list of piece types
        )
        """
    )
    conn.commit()
    conn.close()


def save_legal_move(move: LegalMove):
    """Insert a single LegalMove, ignoring duplicates."""
    with sqlite3.connect(DB_FILE, isolation_level=None) as conn:
        c = conn.cursor()
        c.execute(
            f"""
            INSERT OR IGNORE INTO {_TABLE_NAME} (move, types)
            VALUES (?, ?)
            """,
            (move.move, ",".join(move.types)),
        )


def save_legal_moves(moves: Iterable[LegalMove]):
    """Insert multiple LegalMove objects one by one (ignoring duplicates)."""
    with sqlite3.connect(DB_FILE, isolation_level=None) as conn:
        c = conn.cursor()
        c.executemany(
            f"""
            INSERT OR IGNORE INTO {_TABLE_NAME} (move, types)
            VALUES (?, ?)
            """,
            ((m.move, ",".join(m.types)) for m in moves),
        )


def count_legal_moves() -> int:
    """Return the total number of legal moves currently in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute(f"SELECT COUNT(*) FROM {_TABLE_NAME}")
        result = c.fetchone()
        return result[0] if result else 0
    finally:
        conn.close()


def _row_to_legal_move(row: tuple) -> LegalMove:
    """Convert a DB row to a LegalMove object."""
    return LegalMove(
        move=row[1],
        types=row[2].split(","),
    )


def get_all_legal_moves() -> list[LegalMove]:
    """Return all LegalMove records from the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute(f"SELECT * FROM {_TABLE_NAME}")
        rows = c.fetchall()
        return [_row_to_legal_move(row) for row in rows]
    finally:
        conn.close()
