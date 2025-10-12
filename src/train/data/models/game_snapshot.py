from dataclasses import dataclass
from typing import Optional, List

@dataclass
class GameSnapshot:
    raw_game_id: int
    move_number: int
    turn: str
    move: str
    board: List[int]          # 64 integers
    board_hash: str           # hash of board + turn + move
    white_player: str
    black_player: str
    white_elo: Optional[int]
    black_elo: Optional[int]
    result: str
