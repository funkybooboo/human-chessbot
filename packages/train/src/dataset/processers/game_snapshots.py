from collections.abc import Callable, Iterator
from io import StringIO

import chess
import chess.pgn

from packages.train.src.constants import DEFAULT_BATCH_SIZE, DEFAULT_PRINT_INTERVAL
from packages.train.src.dataset.models.game_snapshot import GameSnapshot
from packages.train.src.dataset.models.raw_game import RawGame
from packages.train.src.dataset.processers.game_statistics import extract_statistics_from_raw_game
from packages.train.src.dataset.repositories.game_snapshots import (
    count_snapshots,
    save_snapshots_batch,
)
from packages.train.src.dataset.repositories.game_statistics import save_game_statistics
from packages.train.src.dataset.repositories.raw_games import mark_raw_game_as_processed


def raw_game_to_snapshots(raw_game: RawGame) -> Iterator[GameSnapshot]:
    """Convert a RawGame into GameSnapshot objects (one per move).

    Note: white_elo, black_elo, and result are stored in game_statistics table.
    """
    pgn_io = StringIO(raw_game.pgn)
    game = chess.pgn.read_game(pgn_io)
    if game is None:
        return

    board = game.board()
    move_number = 1

    for move in game.mainline_moves():
        turn = "w" if board.turn == chess.WHITE else "b"
        previous_board = board.copy()
        san_move = board.san(move)
        board.push(move)

        fen = previous_board.fen()

        yield GameSnapshot(
            raw_game_id=raw_game.id if raw_game.id is not None else 0,
            move_number=move_number,
            turn=turn,
            move=san_move,
            fen=fen,
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


class SnapshotBatchProcessor:
    """Processes raw games into snapshots with batching and progress tracking."""

    def __init__(
        self,
        batch_size: int = DEFAULT_BATCH_SIZE,
        print_interval: int = DEFAULT_PRINT_INTERVAL,
    ):
        self.batch_size = batch_size
        self.print_interval = print_interval
        self._batch: list[GameSnapshot] = []
        self._snapshot_count = count_snapshots()
        self._last_print_count = self._snapshot_count

    def process_games(
        self,
        games: Iterator[RawGame],
        should_stop: Callable[[], bool] | None = None,
        filter_game: Callable[[RawGame], bool] | None = None,
    ) -> int:
        """Process games into snapshots and statistics, saving to database in batches.

        Args:
            games: Iterator of RawGame objects
            should_stop: Optional callback to stop processing early
            filter_game: Optional callback to filter games (return True to process)

        Returns:
            Number of games processed
        """
        games_processed = 0

        for game in games:
            if should_stop and should_stop():
                self._flush_batch()
                break

            if filter_game and not filter_game(game):
                continue

            games_processed += 1

            # Extract and save game statistics
            stats = extract_statistics_from_raw_game(game)
            if stats:
                save_game_statistics(stats)

            # Process snapshots
            for snapshot in raw_game_to_snapshots(game):
                self._batch.append(snapshot)
                if len(self._batch) >= self.batch_size:
                    self._flush_batch()

            self._flush_batch()
            mark_raw_game_as_processed(game)

        return games_processed

    def _flush_batch(self) -> None:
        """Save current batch to database and print progress updates."""
        if not self._batch:
            return

        save_snapshots_batch(self._batch)
        self._snapshot_count = count_snapshots()
        self._batch = []

        if (
            self._snapshot_count // self.print_interval
            > self._last_print_count // self.print_interval
        ):
            print(f"{self._snapshot_count} snapshots saved...")
            self._last_print_count = self._snapshot_count

    def get_snapshot_count(self) -> int:
        """Return current total snapshot count in database."""
        return self._snapshot_count
