import random
from src.play.player.lc0_bot_player import Lc0BotPlayer, Lc0BotPlayerConfig
from src.play.player.stockfish_bot_player import StockfishPlayer, StockfishPlayerConfig
from src.play.player.human_player import HumanPlayer
from src.play.game.game import Game, GameConfig
from src.play.ui.cli import Cli
from src.play.ui.gui import Gui


def main():
    if random.choice([True, False]):
        white = Lc0BotPlayer(config=Lc0BotPlayerConfig(name="Leela", color=True, time_limit=1.0))
        black = StockfishPlayer(config=StockfishPlayerConfig(name="Stockfish", color=False, skill_level=10, time_limit=0.5))
    else:
        white = StockfishPlayer(config=StockfishPlayerConfig(name="Stockfish", color=True, skill_level=10, time_limit=0.5))
        black = Lc0BotPlayer(config=Lc0BotPlayerConfig(name="Leela", color=False, time_limit=1.0))

    game = Game(white, black, config=GameConfig(save_dir="/home/nate/projects/cs6640_project/data/pgn", time_limit=600))

    ui = Gui(game)
    game.ui = ui
    ui.run()


if __name__ == "__main__":
    main()
