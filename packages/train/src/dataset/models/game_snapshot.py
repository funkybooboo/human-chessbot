from dataclasses import dataclass


@dataclass
class GameSnapshot:
    raw_game_id: int
    move_number: int
    turn: str  # 'w' for white, 'b' for black
    move: str  # move in SAN notation
    fen: str  # FEN string representation of the board
    # Note: white_elo, black_elo, and result are stored in game_statistics table
