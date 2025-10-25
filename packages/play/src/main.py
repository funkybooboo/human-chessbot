"""Main entry point for the chess application."""

import argparse
import logging
import random
from pathlib import Path

from packages.play.src.game.game import Game, GameConfig
from packages.play.src.player.lc0_bot_player import Lc0BotPlayer, Lc0BotPlayerConfig
from packages.play.src.player.stockfish_bot_player import StockfishPlayer, StockfishPlayerConfig
from packages.play.src.ui.cli import Cli
from packages.play.src.ui.gui import Gui

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_default_save_dir() -> str:
    """Get default save directory for game PGN files.

    Returns:
        Path to save directory (creates if doesn't exist).
    """
    # Use user's home directory + project data folder
    save_dir = Path.home() / "chess_games" / "pgn"
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
        default=600.0,
        help="Time limit per player in seconds (default: 600)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(args.log_level)

    # Determine save directory
    save_dir = args.save_dir if args.save_dir else get_default_save_dir()

    # Create players (randomly assign colors)
    if random.choice([True, False]):
        logger.info("Creating players: Leela (White) vs Stockfish (Black)")
        white = Lc0BotPlayer(config=Lc0BotPlayerConfig(name="Leela", color=True, time_limit=1.0))
        black = StockfishPlayer(
            config=StockfishPlayerConfig(
                name="Stockfish", color=False, skill_level=10, time_limit=0.5
            )
        )
    else:
        logger.info("Creating players: Stockfish (White) vs Leela (Black)")
        white = StockfishPlayer(
            config=StockfishPlayerConfig(
                name="Stockfish", color=True, skill_level=10, time_limit=0.5
            )
        )
        black = Lc0BotPlayer(config=Lc0BotPlayerConfig(name="Leela", color=False, time_limit=1.0))

    # Create game
    game = Game(white, black, config=GameConfig(save_dir=save_dir, time_limit=args.time_limit))

    # Create and run UI
    if args.ui == "gui":
        logger.info("Starting GUI")
        ui = Gui(game)
    else:
        logger.info("Starting CLI")
        ui = Cli(game)

    game.ui = ui

    try:
        ui.run()
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    finally:
        # Cleanup engines
        for player in [white, black]:
            if hasattr(player, "close"):
                player.close()
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()
