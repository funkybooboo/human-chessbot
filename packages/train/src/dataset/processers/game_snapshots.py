from collections.abc import Iterator
from io import StringIO

import chess
import chess.pgn

from packages.train.src.dataset.models.game_snapshot import GameSnapshot
from packages.train.src.dataset.models.raw_game import RawGame


def raw_game_to_snapshots(raw_game: RawGame) -> Iterator[GameSnapshot]:
    """
    Convert a RawGame into multiple GameSnapshot objects, one per move.
    """
    pgn_io = StringIO(raw_game.pgn)
    game = chess.pgn.read_game(pgn_io)
    if game is None:
        return  # skip invalid PGNs

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

        yield GameSnapshot(
            raw_game_id=raw_game.id if raw_game.id is not None else 0,  # link back to raw game
            move_number=move_number,
            turn=turn,
            move=san_move,
            fen=fen,
            white_elo=white_elo,
            black_elo=black_elo,
            result=result,
        )

        move_number += 1


def _safe_int(val: str | None) -> int | None:
    """Convert a string to int, return None if conversion fails."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
