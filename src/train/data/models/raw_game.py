from dataclasses import dataclass, field
from typing import Optional
import hashlib

@dataclass
class RawGame:
    id: Optional[int] = None           # DB primary key
    file_id: Optional[int] = None      # Foreign key to file_metadata
    pgn: str = ""
    processed: bool = False            # Tracks if snapshots have been generated
    pgn_hash: str = field(init=False)  # automatically computed from pgn

    def __post_init__(self):
        # Compute SHA-256 hash of the PGN
        self.pgn_hash = hashlib.sha256(self.pgn.encode("utf-8")).hexdigest()
