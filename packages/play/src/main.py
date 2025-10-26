"""Main entry point for the chess application."""

import argparse
import random
from pathlib import Path

from packages.play.src.constants import (
    GAME_SAVE_DIR,
    GAME_TIME_LIMIT,
    LC0_TIME_LIMIT,
    STOCKFISH_SKILL_LEVEL,
    STOCKFISH_TIME_LIMIT,
)
from packages.play.src.game.game import Game, GameConfig
from packages.play.src.player.lc0_bot_player import Lc0BotPlayer, Lc0BotPlayerConfig
from packages.play.src.player.stockfish_bot_player import StockfishPlayer, StockfishPlayerConfig
from packages.play.src.ui.cli import Cli
from packages.play.src.ui.gui import Gui
from packages.play.src.ui.ui import Ui


def get_default_save_dir() -> str:
    """Get default save directory for game PGN files.

    Returns:
        Path to save directory (creates if doesn't exist).
    """
    # Use configured save directory
    save_dir = Path(GAME_SAVE_DIR)
    save_dir.mkdir(parents=True, exist_ok=True)
    return str(save_dir)


def main():
    """Run the chess application.

    Randomly selects Stockfish vs LCZero with alternating colors.
    Uses GUI by default.
    """
    parser = argparse.ArgumentParser(description="Chess Bot Game")
    parser.add_argument(
        "--ui", choices=["gui", "cli"], default="gui", help="User interface to use (default: gui)"
    )
    parser.add_argument(
        "--save-dir",
        type=str,
        default=None,
        help=f"Directory to save PGN files (default: {get_default_save_dir()})",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=GAME_TIME_LIMIT,
        help=f"Time limit per player in seconds (default: {GAME_TIME_LIMIT})",
    )

    args = parser.parse_args()

    # Determine save directory
    save_dir = args.save_dir if args.save_dir else get_default_save_dir()

    # Create players (randomly assign colors)
    white: Lc0BotPlayer | StockfishPlayer
    black: Lc0BotPlayer | StockfishPlayer
    if random.choice([True, False]):
        print("Creating players: Leela (White) vs Stockfish (Black)")
        white = Lc0BotPlayer(
            config=Lc0BotPlayerConfig(name="Leela", color=True, time_limit=LC0_TIME_LIMIT)
        )
        black = StockfishPlayer(
            config=StockfishPlayerConfig(
                name="Stockfish",
                color=False,
                skill_level=STOCKFISH_SKILL_LEVEL,
                time_limit=STOCKFISH_TIME_LIMIT,
            )
        )
    else:
        print("Creating players: Stockfish (White) vs Leela (Black)")
        white = StockfishPlayer(
            config=StockfishPlayerConfig(
                name="Stockfish",
                color=True,
                skill_level=STOCKFISH_SKILL_LEVEL,
                time_limit=STOCKFISH_TIME_LIMIT,
            )
        )
        black = Lc0BotPlayer(
            config=Lc0BotPlayerConfig(name="Leela", color=False, time_limit=LC0_TIME_LIMIT)
        )

    # Create game
    game = Game(white, black, config=GameConfig(save_dir=save_dir, time_limit=args.time_limit))

    # Create and run UI
    ui: Ui
    if args.ui == "gui":
        print("Starting GUI")
        ui = Gui(game)
    else:
        print("Starting CLI")
        ui = Cli(game)

    game.ui = ui

    try:
        ui.run()
    except KeyboardInterrupt:
        print("Game interrupted by user")
    finally:
        # Cleanup engines
        for player in [white, black]:
            if hasattr(player, "close"):
                player.close()
        print("Application shutdown complete")


if __name__ == "__main__":
    main()
