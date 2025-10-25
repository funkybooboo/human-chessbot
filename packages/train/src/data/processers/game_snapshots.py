import hashlib
from collections.abc import Iterator
from io import StringIO

import chess
import chess.pgn

from packages.train.src.data.models.game_snapshot import GameSnapshot
from packages.train.src.data.models.raw_game import RawGame

PIECE_TO_INT = {
    "P": 1,
    "N": 2,
    "B": 3,
    "R": 4,
    "Q": 5,
    "K": 6,  # white pieces
    "p": -1,
    "n": -2,
    "b": -3,
    "r": -4,
    "q": -5,
    "k": -6,  # black pieces
    None: 0,  # empty square
}


def raw_game_to_snapshots(raw_game: RawGame) -> Iterator[GameSnapshot]:
    """
    Convert a RawGame into multiple GameSnapshot objects, one per move.
    Each snapshot has a unique hash to prevent duplicates.
    """
    pgn_io = StringIO(raw_game.pgn)
    game = chess.pgn.read_game(pgn_io)
    if game is None:
        return  # skip invalid PGNs

    white_player = game.headers.get("White", "Unknown")
    black_player = game.headers.get("Black", "Unknown")
    white_elo = _safe_int(game.headers.get("WhiteElo"))
    black_elo = _safe_int(game.headers.get("BlackElo"))
    result = game.headers.get("Result", "*")

    board = game.board()
    move_number = 1

    for move in game.mainline_moves():
        turn = "w" if board.turn == chess.WHITE else "b"
        san_move = board.san(move)
        board.push(move)

        board_array = [_piece_to_int(board.piece_at(i)) for i in range(64)]
        board_hash = _compute_board_hash(board_array, turn, san_move)

        yield GameSnapshot(
            raw_game_id=raw_game.id,  # link back to raw game
            move_number=move_number,
            turn=turn,
            move=san_move,
            board=board_array,
            board_hash=board_hash,
            white_player=white_player,
            black_player=black_player,
            white_elo=white_elo,
            black_elo=black_elo,
            result=result,
        )

        move_number += 1


def _compute_board_hash(board_array: list[int], turn: str, move: str) -> str:
    """Compute a SHA-256 hash of the board state, turn, and move."""
    data = f"{board_array}-{turn}-{move}".encode()
    return hashlib.sha256(data).hexdigest()


def _safe_int(val: str | None) -> int | None:
    """Convert a string to int, return None if conversion fails."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _piece_to_int(piece: chess.Piece | None) -> int:
    """Convert a chess piece to its integer representation."""
    if piece is None:
        return 0
    return PIECE_TO_INT[piece.symbol()]
