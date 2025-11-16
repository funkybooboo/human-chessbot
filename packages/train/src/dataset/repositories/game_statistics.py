import sqlite3
from collections.abc import Iterator

from packages.train.src.constants import DB_FILE
from packages.train.src.dataset.models.game_statistics import GameStatistics

_TABLE_NAME = "game_statistics"


def create_game_statistics_table():
    """Create the 'game_statistics' table if it does not exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute(
        f"""
    CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_game_id INTEGER UNIQUE NOT NULL,
        event TEXT,
        site TEXT,
        date TEXT,
        round TEXT,
        white TEXT,
        black TEXT,
        result TEXT,
        white_elo INTEGER,
        black_elo INTEGER,
        white_rating_diff INTEGER,
        black_rating_diff INTEGER,
        time_control TEXT,
        eco TEXT,
        opening TEXT,
        termination TEXT,
        utc_date TEXT,
        utc_time TEXT,
        variant TEXT,
        lichess_url TEXT,
        total_moves INTEGER,
        FOREIGN KEY(raw_game_id) REFERENCES raw_games(id)
    )
    """
    )
    conn.commit()
    conn.close()


def game_statistics_table_exists() -> bool:
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


def save_game_statistics(stats: GameStatistics):
    """Insert a single GameStatistics record."""
    with sqlite3.connect(DB_FILE, isolation_level=None) as conn:
        c = conn.cursor()

        # Check if statistics already exist for this raw_game_id
        c.execute(f"SELECT id FROM {_TABLE_NAME} WHERE raw_game_id = ?", (stats.raw_game_id,))
        existing = c.fetchone()
        
        if existing:
            # Skip if already exists
            stats.id = existing[0]
            return

        # Insert new statistics
        c.execute(
            f"""
        INSERT INTO {_TABLE_NAME} (
            raw_game_id, event, site, date, round, white, black, result,
            white_elo, black_elo, white_rating_diff, black_rating_diff,
            time_control, eco, opening, termination, utc_date, utc_time,
            variant, lichess_url, total_moves
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
            (
                stats.raw_game_id,
                stats.event,
                stats.site,
                stats.date,
                stats.round,
                stats.white,
                stats.black,
                stats.result,
                stats.white_elo,
                stats.black_elo,
                stats.white_rating_diff,
                stats.black_rating_diff,
                stats.time_control,
                stats.eco,
                stats.opening,
                stats.termination,
                stats.utc_date,
                stats.utc_time,
                stats.variant,
                stats.lichess_url,
                stats.total_moves,
            ),
        )
        stats.id = c.lastrowid


def save_game_statistics_batch(stats_list: list[GameStatistics]):
    """
    Insert multiple GameStatistics in a single transaction for better performance.
    """
    if not stats_list:
        return

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()

        # Prepare data for batch insert
        data = [
            (
                stats.raw_game_id,
                stats.event,
                stats.site,
                stats.date,
                stats.round,
                stats.white,
                stats.black,
                stats.result,
                stats.white_elo,
                stats.black_elo,
                stats.white_rating_diff,
                stats.black_rating_diff,
                stats.time_control,
                stats.eco,
                stats.opening,
                stats.termination,
                stats.utc_date,
                stats.utc_time,
                stats.variant,
                stats.lichess_url,
                stats.total_moves,
            )
            for stats in stats_list
        ]

        # Batch insert all statistics (ignore duplicates)
        c.executemany(
            f"""
            INSERT OR IGNORE INTO {_TABLE_NAME} (
                raw_game_id, event, site, date, round, white, black, result,
                white_elo, black_elo, white_rating_diff, black_rating_diff,
                time_control, eco, opening, termination, utc_date, utc_time,
                variant, lichess_url, total_moves
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data,
        )
        conn.commit()


def count_game_statistics() -> int:
    """Return the total number of game statistics currently in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute(f"SELECT COUNT(*) FROM {_TABLE_NAME}")
        result = c.fetchone()
        count = result[0] if result else 0
    finally:
        conn.close()
    return count


def fetch_game_statistics_by_raw_game_id(raw_game_id: int) -> GameStatistics | None:
    """Fetch statistics for a specific raw game."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(f"SELECT * FROM {_TABLE_NAME} WHERE raw_game_id = ?", (raw_game_id,))
        row = c.fetchone()
        if row:
            return _row_to_game_statistics(row)
        return None


def fetch_games_by_opening(eco: str) -> Iterator[GameStatistics]:
    """Fetch all games with a specific ECO code."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(f"SELECT * FROM {_TABLE_NAME} WHERE eco = ?", (eco,))
        for row in c:
            yield _row_to_game_statistics(row)


def fetch_games_by_time_control(time_control: str) -> Iterator[GameStatistics]:
    """Fetch all games with a specific time control."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(f"SELECT * FROM {_TABLE_NAME} WHERE time_control = ?", (time_control,))
        for row in c:
            yield _row_to_game_statistics(row)


def _row_to_game_statistics(row: tuple) -> GameStatistics:
    """Convert a DB row to a GameStatistics object."""
    return GameStatistics(
        id=row[0],
        raw_game_id=row[1],
        event=row[2],
        site=row[3],
        date=row[4],
        round=row[5],
        white=row[6],
        black=row[7],
        result=row[8],
        white_elo=row[9],
        black_elo=row[10],
        white_rating_diff=row[11],
        black_rating_diff=row[12],
        time_control=row[13],
        eco=row[14],
        opening=row[15],
        termination=row[16],
        utc_date=row[17],
        utc_time=row[18],
        variant=row[19],
        lichess_url=row[20],
        total_moves=row[21],
    )
