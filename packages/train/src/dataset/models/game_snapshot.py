from dataclasses import dataclass


@dataclass
class GameSnapshot:
    raw_game_id: int
    move_number: int
    turn: str
    move: str
    fen: str  # FEN string representation of the board
    board_hash: str  # hash of fen + turn + move
    white_player: str
    black_player: str
    white_elo: int | None
    black_elo: int | None
    result: str
