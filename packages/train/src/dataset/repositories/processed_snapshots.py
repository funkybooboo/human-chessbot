import sqlite3

from packages.train.src.constants import DB_FILE
from packages.train.src.dataset.models.processed_snapshot import ProcessedSnapshot

_TABLE_NAME = "processed_snapshots"


def create_processed_snapshots_table():
    """Create the 'processed_snapshots' table if it does not exist.

    This table caches processed game_snapshots data to avoid
    processing the same row twice.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(
        f"""
    CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
        snapshot_id INTEGER PRIMARY KEY,
        board BLOB NOT NULL,
        metadata BLOB NOT NULL,
        chosen_move INTEGER NOT NULL,
        valid_moves BLOB NOT NULL,
        FOREIGN KEY(snapshot_id) REFERENCES game_snapshots(id)
    )
    """
    )
    conn.commit()
    conn.close()


def save_processed_snapshots(data: list[tuple[int, bytes, bytes, int, bytes]]):
    """Save multiple processed snapshots in a single transaction.

    Args:
        data: List of (snapshot_id, board_bytes, metadata_bytes, chosen_move, valid_moves_bytes)
    """
    if not data:
        return

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.executemany(
            f"INSERT OR IGNORE INTO {_TABLE_NAME} (snapshot_id, board, metadata, chosen_move, valid_moves) VALUES (?, ?, ?, ?, ?)",
            data,
        )
        conn.commit()


def get_processed_snapshots_batch(
    snapshot_ids: list[int],
) -> dict[int, ProcessedSnapshot]:
    """Fetch multiple processed snapshots in a single query.

    Args:
        snapshot_ids: List of snapshot IDs to look up

    Returns:
        Dict mapping snapshot_id -> ProcessedSnapshot object
    """
    if not snapshot_ids:
        return {}

    with sqlite3.connect(DB_FILE) as conn:
        placeholders = ",".join("?" * len(snapshot_ids))
        c = conn.cursor()
        c.execute(
            f"SELECT snapshot_id, board, metadata, chosen_move, valid_moves FROM {_TABLE_NAME} WHERE snapshot_id IN ({placeholders})",
            snapshot_ids,
        )
        raw_data = {row[0]: (row[1], row[2], row[3], row[4]) for row in c.fetchall()}

    return {
        snapshot_id: ProcessedSnapshot.from_bytes(snapshot_id, *data)
        for snapshot_id, data in raw_data.items()
    }


def count_processed_snapshots() -> int:
    """Get the total number of processed snapshots in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute(f"SELECT COUNT(*) FROM {_TABLE_NAME}")
        result = c.fetchone()
        return result[0] if result else 0
    finally:
        conn.close()


def get_total_snapshots() -> int:
    """Get the total number of snapshots in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM game_snapshots")
        result = c.fetchone()
        return result[0] if result else 0
    finally:
        conn.close()


def get_raw_snapshots_batch(offset: int, batch_size: int) -> list[tuple]:
    """Get a batch of raw snapshot data for processing.

    Args:
        offset: Starting offset for the query
        batch_size: Number of rows to fetch

    Returns:
        List of tuples: (id, fen, move, turn, white_elo, black_elo, result)
    """
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT gs.id, gs.fen, gs.move, gs.turn,
                   gst.white_elo, gst.black_elo, gst.result
            FROM game_snapshots gs
            JOIN game_statistics gst ON gs.raw_game_id = gst.raw_game_id
            ORDER BY gs.id
            LIMIT ? OFFSET ?
            """,
            (batch_size, offset),
        )
        return cur.fetchall()
