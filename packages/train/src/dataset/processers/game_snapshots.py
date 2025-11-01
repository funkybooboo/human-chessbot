import hashlib
from collections.abc import Iterator
from io import StringIO

import chess
import chess.pgn

from packages.train.src.dataset.models.game_snapshot import GameSnapshot
from packages.train.src.dataset.models.raw_game import RawGame


def raw_game_to_snapshots(raw_game: RawGame) -> Iterator[GameSnapshot]:
    """
    Convert a RawGame into multiple GameSnapshot objects, one per move.
    Each snapshot has a unique hash to prevent duplicates.
    """
    pgn_io = StringIO(raw_game.pgn)
    game = chess.pgn.read_game(pgn_io)
    if game is None:
        return  # skip invalid PGNs

    date_time = game.headers.get("UTCDate", "") + game.headers.get("UTCTime", "")

    white_elo = _safe_int(game.headers.get("WhiteElo"))
    black_elo = _safe_int(game.headers.get("BlackElo"))
    result = game.headers.get("Result", "*")

    board = game.board()
    move_number = 1

    for move in game.mainline_moves():
        turn = "w" if board.turn == chess.WHITE else "b"
        san_move = board.san(move)
        board.push(move)

        fen = board.fen()
        board_hash = _compute_board_hash(white_elo, black_elo, fen, turn, san_move, date_time)

        yield GameSnapshot(
            raw_game_id=raw_game.id if raw_game.id is not None else 0,  # link back to raw game
            move_number=move_number,
            turn=turn,
            move=san_move,
            fen=fen,
            board_hash=board_hash,
            white_elo=white_elo,
            black_elo=black_elo,
            result=result,
        )

        move_number += 1


def _compute_board_hash(
    white_elo: int | None, black_elo: int | None, fen: str, turn: str, move: str, date_time: str
) -> str:
    """Compute a SHA-256 hash of the player elos, FEN, turn, move, and date_time"""
    data = f"{white_elo}-{black_elo}-{fen}-{turn}-{move}-{date_time}".encode()
    return hashlib.sha256(data).hexdigest()


def _safe_int(val: str | None) -> int | None:
    """Convert a string to int, return None if conversion fails."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
