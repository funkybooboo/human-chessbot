import sqlite3
from collections.abc import Iterable, Iterator

from packages.train.src.data.database.config import DB_FILE, is_database_initialized
from packages.train.src.data.models.file_metadata import FileMetadata

_TABLE_NAME: str = "files_metadata"


def create_files_metadata_table():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
        CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            filename TEXT,
            games INTEGER,
            size_gb REAL,
            processed INTEGER DEFAULT 0
        )
        """
        )
        conn.commit()


def files_metadata_exist() -> bool:
    """Return True if the 'files_metadata' table has any rows."""
    if not is_database_initialized():
        return False

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM files_metadata LIMIT 1;")
        has_rows = cursor.fetchone() is not None
    finally:
        conn.close()
    return has_rows


def save_file_metadata(file: FileMetadata) -> None:
    """
    Save a single FileMetadata object into the database.
    Skips if a file with the same URL already exists.
    Updates the object's `id` after insertion.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM {_TABLE_NAME} WHERE url = ?", (file.url,))
        row = cursor.fetchone()
        if row:
            file.id = row[0]  # assign existing id
            return

        cursor.execute(
            f"""
            INSERT INTO {_TABLE_NAME} (url, filename, games, size_gb, processed)
            VALUES (?, ?, ?, ?, ?)
            """,
            (file.url, file.filename, file.games, file.size_gb, int(file.processed)),
        )
        file.id = cursor.lastrowid  # assign new id
        conn.commit()


def save_files_metadata(files: Iterable[FileMetadata]) -> None:
    """
    Save an iterable of FileMetadata objects into the database.
    Calls `save_file_metadata` for each file.
    """
    for file in files:
        save_file_metadata(file)


def mark_file_as_processed(file: FileMetadata) -> None:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {_TABLE_NAME} SET processed = 1 WHERE url = ?", (file.url,))
        file.processed = True
        conn.commit()


def fetch_all_files_metadata() -> Iterator[FileMetadata]:
    """Yield all FileMetadata objects in the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, url, filename, games, size_gb, processed FROM {_TABLE_NAME}")
        for row in cursor:
            yield _row_to_file_metadata(row)


def fetch_files_metadata_under_size(max_gb: float) -> Iterator[FileMetadata]:
    """Yield FileMetadata objects with size less than max_gb."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, url, filename, games, size_gb, processed FROM {_TABLE_NAME} WHERE size_gb < ?",
            (max_gb,),
        )
        for row in cursor:
            yield _row_to_file_metadata(row)


def _row_to_file_metadata(row: tuple) -> FileMetadata:
    return FileMetadata(
        id=row[0],
        url=row[1],
        filename=row[2],
        games=row[3],
        size_gb=row[4],
        processed=bool(row[5]),  # Convert 0/1 to boolean
    )
