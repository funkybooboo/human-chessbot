import sqlite3
from pathlib import Path

DB_FILE = "./database.sqlite3"


def is_database_initialized() -> bool:
    """Return True if the database has the main tables."""
    if not Path(DB_FILE).exists():
        return False

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Check if 'files_metadata' table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='files_metadata';"
        )
        table_exists = cursor.fetchone() is not None
    finally:
        conn.close()
    return table_exists
