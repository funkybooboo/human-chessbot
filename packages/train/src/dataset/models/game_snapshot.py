from dataclasses import dataclass


@dataclass
class GameSnapshot:
    raw_game_id: int
    move_number: int
    turn: str  # 'w' for white, 'b' for black
    move: str  # move in SAN notation
    fen: str  # FEN string representation of the board
    white_elo: int | None
    black_elo: int | None
    result: str  # '1-0', '0-1', '1/2-1/2', or '*'
