import sqlite3
from collections.abc import Iterable, Iterator

from packages.train.src.constants import DB_FILE
from packages.train.src.dataset.models.file_metadata import FileMetadata
from packages.train.src.dataset.repositories.db_utils import is_database_initialized

_TABLE_NAME: str = "files_metadata"


def ensure_metadata_exists() -> None:
    """Fetch and save Lichess file metadata if not already in database."""
    if not files_metadata_exist():
        from packages.train.src.dataset.requesters.file_metadata import fetch_files_metadata

        print("Fetching file metadata from Lichess...")
        save_files_metadata(fetch_files_metadata())
        print("Metadata saved.")
    else:
        print("File metadata already exists.")


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
    """Check if files_metadata table has any rows."""
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
    """Save FileMetadata to database (skips duplicates by URL)."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM {_TABLE_NAME} WHERE url = ?", (file.url,))
        row = cursor.fetchone()
        if row:
            file.id = row[0]
            return

        cursor.execute(
            f"""
            INSERT INTO {_TABLE_NAME} (url, filename, games, size_gb, processed)
            VALUES (?, ?, ?, ?, ?)
            """,
            (file.url, file.filename, file.games, file.size_gb, int(file.processed)),
        )
        file.id = cursor.lastrowid
        conn.commit()


def save_files_metadata(files: Iterable[FileMetadata]) -> None:
    """Save multiple FileMetadata objects to database."""
    for file in files:
        save_file_metadata(file)


def mark_file_as_processed(file: FileMetadata) -> None:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {_TABLE_NAME} SET processed = 1 WHERE url = ?", (file.url,))
        file.processed = True
        conn.commit()


def fetch_all_files_metadata() -> Iterator[FileMetadata]:
    """Fetch all FileMetadata from database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, url, filename, games, size_gb, processed FROM {_TABLE_NAME}")
        for row in cursor:
            yield _row_to_file_metadata(row)


def fetch_files_metadata_under_size(max_gb: float) -> Iterator[FileMetadata]:
    """Fetch FileMetadata for files smaller than max_gb."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, url, filename, games, size_gb, processed FROM {_TABLE_NAME} WHERE size_gb < ?",
            (max_gb,),
        )
        for row in cursor:
            yield _row_to_file_metadata(row)


def fetch_file_metadata_by_filename(filename: str) -> FileMetadata | None:
    """Fetch FileMetadata by filename (returns None if not found)."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, url, filename, games, size_gb, processed FROM {_TABLE_NAME} WHERE filename = ?",
            (filename,),
        )
        row = cursor.fetchone()
        if row:
            return _row_to_file_metadata(row)
        return None


def _row_to_file_metadata(row: tuple) -> FileMetadata:
    return FileMetadata(
        id=row[0],
        url=row[1],
        filename=row[2],
        games=row[3],
        size_gb=row[4],
        processed=bool(row[5]),  # Convert 0/1 to boolean
    )
