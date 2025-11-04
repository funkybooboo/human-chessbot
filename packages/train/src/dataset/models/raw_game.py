from dataclasses import dataclass


@dataclass
class RawGame:
    id: int | None = None  # DB primary key
    file_id: int | None = None  # Foreign key to file_metadata
    pgn: str = ""
    processed: bool = False  # Tracks if snapshots have been generated
