from dataclasses import dataclass


@dataclass
class FileMetadata:
    url: str
    filename: str
    games: int
    size_gb: float
    id: int | None = None  # DB primary key
    processed: bool = False  # New field
