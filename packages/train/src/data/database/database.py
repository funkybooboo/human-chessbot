import sqlite3
from collections.abc import Callable

from packages.train.src.data.database.config import DB_FILE
from packages.train.src.data.database.files_metadata import create_files_metadata_table
from packages.train.src.data.database.game_snapshots import create_game_snapshots_table
from packages.train.src.data.database.raw_games import create_raw_games_table

# List of functions that create tables in the database
TABLE_CREATORS: list[Callable[[], None]] = [
    create_files_metadata_table,
    create_raw_games_table,
    create_game_snapshots_table,
]


def initialize_database() -> None:
    """
    Creates the SQLite database and the tables if they don't exist.
    """
    # Connecting ensures the file exists
    with sqlite3.connect(DB_FILE):
        pass

    # Initialize tables
    for table_creator in TABLE_CREATORS:
        table_creator()
