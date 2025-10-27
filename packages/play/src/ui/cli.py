"""Command-line interface for chess games."""

import time

import chess
from pydantic import BaseModel, Field

from packages.play.src.constants import CLI_LOOP_INTERVAL
from packages.play.src.game.game import Game
from packages.play.src.player.human_player import HumanPlayer
from packages.play.src.ui.ui import Ui


class CliConfig(BaseModel):
    """CLI configuration.

    Attributes:
        loop_interval: Seconds between game loop iterations
    """

    loop_interval: float = Field(
        default=CLI_LOOP_INTERVAL, gt=0, description="Seconds between game loop iterations"
    )


class Cli(Ui):
    """Command-line interface for chess games.

    Displays the board in ASCII format and accepts moves via text input.
    Suitable for terminal-based play and bot vs bot matches.
    """

    def __init__(self, game: Game, config: CliConfig = CliConfig()) -> None:
        """Initialize CLI interface.

        Args:
            game: Chess game to display
            config: CLI configuration
        """
        super().__init__(game)
        self.config: CliConfig = config
        self.move_history: list[str] = []
        print("CLI initialized")

    def run(self) -> None:
        """Start the CLI game loop."""
        print("Starting CLI game loop")
        self._game_loop()

    def reset_ui(self) -> None:
        """Reset move history and display."""
        self.move_history = []
        print("\n" + "=" * 50)
        print("GAME RESET")
        print("=" * 50 + "\n")
        print("UI reset")

    def display_board(self) -> None:
        """Display the board in ASCII format."""
        print("\n" + str(self.game.board) + "\n")

    def show_message(self, message: str) -> None:
        """Display a message to the user.

        Args:
            message: Message to display
        """
        print(f"\n>>> {message}\n")

    def update_scores(self, white_score: float, black_score: float) -> None:
        """Display current material scores.

        Args:
            white_score: White's material score
            black_score: Black's material score
        """
        print(f"Material - White: {white_score:.0f}  Black: {black_score:.0f}")

    def update_move_list(self, move_san: str) -> None:
        """Add move to history and display it.

        Args:
            move_san: Move in SAN format
        """
        self.move_history.append(move_san)
        move_num = len(self.move_history)
        player = "White" if (move_num % 2 == 1) else "Black"
        print(f"Move {(move_num + 1) // 2}: {move_san} ({player})")

    def _prompt_move(self, player: HumanPlayer) -> chess.Move | None:
        """Prompt human player for a legal move via text input.

        Args:
            player: Human player to prompt

        Returns:
            A legal chess move
        """
        legal_moves = list(self.game.board.legal_moves)
        print(f"\n{len(legal_moves)} legal moves available")

        while True:
            move_str = input(f"{player.config.name}'s move (UCI format, e.g., e2e4): ").strip()

            if not move_str:
                continue

            try:
                move = chess.Move.from_uci(move_str)
                if move in legal_moves:
                    return move
                print(f"Illegal move! '{move_str}' is not legal in this position.")
            except ValueError as e:
                print(f"Invalid move format: {e}. Use UCI format (e.g., e2e4, e7e8q)")

    def _game_loop(self) -> None:
        """Main game loop for CLI."""
        self.reset_ui()
        self.display_board()

        while not self.game.is_over():
            current_player = self.game.current_player

            # Get move from current player
            if isinstance(current_player, HumanPlayer):
                move = self._prompt_move(current_player)
            else:
                print(f"\n{current_player.config.name} is thinking...")
                move = current_player.get_move(self.game.board)

            # Apply move if available
            if move:
                move_san = self.game.apply_move(move)
                self.update_move_list(move_san)
                self.display_board()
                white_score, black_score = self.game.get_scores()
                self.update_scores(white_score, black_score)

            # Update and display timers
            timeout_winner = self.game.update_timer()
            print(
                f"Time - White: {self.game.white_time_left:.1f}s  Black: {self.game.black_time_left:.1f}s"
            )

            if timeout_winner:
                self.show_message(f"Game Over: {timeout_winner.config.name} wins on time!")
                break

            time.sleep(self.config.loop_interval)

        # Display game result
        result = self.game.result()
        print("\n" + "=" * 50)
        if result == "1-0":
            print(f"WHITE WINS! {self.game.white_player.config.name} victorious!")
        elif result == "0-1":
            print(f"BLACK WINS! {self.game.black_player.config.name} victorious!")
        elif result == "1/2-1/2":
            print("DRAW!")
        else:
            print("Game ended.")
        print("=" * 50 + "\n")

        # Save game
        filename = self.game.save_game()
        print(f"Game saved to: {filename}")
