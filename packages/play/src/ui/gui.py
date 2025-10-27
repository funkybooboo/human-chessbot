"""Graphical user interface for chess games using Tkinter."""

import os
import sys
import tkinter as tk
import urllib.request

import chess
from PIL import Image, ImageTk
from pydantic import BaseModel, Field

from packages.play.src.constants import (
    COLOR_BOARD_DARK,
    COLOR_BOARD_LIGHT,
    COLOR_HIGHLIGHT_CAPTURE_SQUARE,
    COLOR_HIGHLIGHT_ILLEGAL,
    COLOR_HIGHLIGHT_LAST_MOVE,
    COLOR_HIGHLIGHT_LEGAL,
    COLOR_HIGHLIGHT_SELECTED,
    GUI_BASE_URL,
    GUI_HIGHLIGHT_CAPTURE_SQUARE,
    GUI_HIGHLIGHT_ILLEGAL_MOVE,
    GUI_HIGHLIGHT_LAST_MOVE,
    GUI_HIGHLIGHT_LEGAL_MOVES,
    GUI_HIGHLIGHT_SELECTED,
    GUI_IMAGE_DIR,
    GUI_TILE_SIZE,
    GUI_WINDOW_HEIGHT,
    GUI_WINDOW_WIDTH,
)
from packages.play.src.game.game import Game
from packages.play.src.player.human_player import HumanPlayer
from packages.play.src.ui.ui import Ui

# Mapping from piece symbols to image filenames
PIECE_CODES: dict[str, str] = {
    "P": "wp",
    "R": "wr",
    "N": "wn",
    "B": "wb",
    "Q": "wq",
    "K": "wk",
    "p": "bp",
    "r": "br",
    "n": "bn",
    "b": "bb",
    "q": "bq",
    "k": "bk",
}


class GuiConfig(BaseModel):
    """Configuration for GUI appearance and behavior.

    Attributes:
        window_width: Initial window width in pixels
        window_height: Initial window height in pixels
        highlight_legal_moves: Show legal move highlights
        highlight_last_move: Highlight the last move made
        highlight_selected: Highlight the selected square
        highlight_illegal_move: Flash red on illegal move attempts
        highlight_capture_square: Highlight capture squares in gold
        tile_size: Initial tile size in pixels (will resize with window)
        image_dir: Directory to cache piece images
        base_url: URL to download piece images from
    """

    window_width: int = Field(default=GUI_WINDOW_WIDTH, gt=0)
    window_height: int = Field(default=GUI_WINDOW_HEIGHT, gt=0)
    highlight_legal_moves: bool = Field(default=GUI_HIGHLIGHT_LEGAL_MOVES)
    highlight_last_move: bool = Field(default=GUI_HIGHLIGHT_LAST_MOVE)
    highlight_selected: bool = Field(default=GUI_HIGHLIGHT_SELECTED)
    highlight_illegal_move: bool = Field(default=GUI_HIGHLIGHT_ILLEGAL_MOVE)
    highlight_capture_square: bool = Field(default=GUI_HIGHLIGHT_CAPTURE_SQUARE)
    tile_size: int = Field(default=GUI_TILE_SIZE, gt=0)
    image_dir: str = Field(default=GUI_IMAGE_DIR)
    base_url: str = Field(default=GUI_BASE_URL)


class Gui(Ui):
    """Graphical user interface using Tkinter.

    Provides a visual chess board with drag-and-drop piece movement,
    move highlighting, and game controls.
    """

    def __init__(self, game: Game, config: GuiConfig = GuiConfig()) -> None:
        """Initialize GUI.

        Args:
            game: Chess game to display
            config: GUI configuration
        """
        super().__init__(game)
        self.config: GuiConfig = config

        # Tkinter root window
        self.root: tk.Tk = tk.Tk()
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.root.title("Chess GUI")

        # Game references
        self.board: chess.Board = game.board
        self.image_dir: str = self.config.image_dir
        self.current_player = self.game.current_player

        # GUI state
        self.tile_size: int = self.config.tile_size
        self.piece_images_raw: dict[str, Image.Image] = {}
        self.piece_images_scaled: dict[str, ImageTk.PhotoImage] = {}
        self.selected_square: int | None = None
        self.legal_moves: list[chess.Move] = []
        self.illegal_dest: int | None = None
        self.after_id: str | None = None

        # Layout
        main_frame: tk.Frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        # Chess board
        self.canvas: tk.Canvas = tk.Canvas(main_frame, bg="black")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)

        # Sidebar
        self.sidebar: tk.Frame = tk.Frame(main_frame, width=220, bg="#EEE")
        self.sidebar.pack(side="right", fill="y")

        # Turn label
        self.turn_label: tk.Label = tk.Label(
            self.sidebar, text="", font=("Arial", 14, "bold"), bg="#EEE"
        )
        self.turn_label.pack(pady=(10, 10))

        # Player stats
        self._setup_player_stats()

        # Move list
        tk.Label(self.sidebar, text="Moves", font=("Arial", 12, "bold"), bg="#EEE").pack()
        self.move_listbox: tk.Listbox = tk.Listbox(
            self.sidebar, font=("Consolas", 10), width=25, height=20
        )
        self.move_listbox.pack(padx=10, pady=5, fill="both", expand=True)

        # Buttons
        self.save_button: tk.Button = tk.Button(
            self.sidebar, text="Save Game", command=self._save_game
        )
        self.save_button.pack(pady=10, fill="x")
        self.new_game_button: tk.Button = tk.Button(
            self.sidebar, text="New Game", command=self._reset_game, bg="#55AAFF", fg="white"
        )
        self.new_game_button.pack(pady=(0, 5), fill="x")
        self.quit_button: tk.Button = tk.Button(
            self.sidebar, text="Quit", command=self._quit_game, bg="#FF5555", fg="white"
        )
        self.quit_button.pack(pady=(5, 10), fill="x")

        # Game over / play again
        self.game_over_label: tk.Label = tk.Label(
            self.sidebar, text="", font=("Arial", 12, "bold"), bg="#EEE", fg="red"
        )
        self.game_over_label.pack(pady=5)
        self.play_again_button: tk.Button = tk.Button(
            self.sidebar, text="Play Again", command=self._reset_game
        )
        self.play_again_button.pack(pady=10, fill="x")
        self.play_again_button.pack_forget()

        # Load piece images
        os.makedirs(self.image_dir, exist_ok=True)
        self._download_and_load_images()
        print("GUI initialized")

    def run(self) -> None:
        """Start the GUI and game loop."""
        self._update_turn_label()
        self.root.after(100, self._game_loop)
        print("Starting GUI mainloop")
        self.root.mainloop()

    # ================= UI Interface Implementation =================

    def display_board(self) -> None:
        """Display the board (delegates to _draw_board)."""
        self._draw_board()

    def update_scores(self, white_score: float, black_score: float) -> None:
        """Update the player material scores.

        Args:
            white_score: White's material score
            black_score: Black's material score
        """
        self.white_score_label.config(text=f"Score: {white_score:.0f}")
        self.black_score_label.config(text=f"Score: {black_score:.0f}")

    def update_move_list(self, san_move: str) -> None:
        """Add a move to the move history list.

        Args:
            san_move: Move in SAN format
        """
        if san_move:
            moves = list(self.board.move_stack)
            move_num = len(moves)
            if move_num % 2 == 1:
                self.move_listbox.insert(tk.END, f"{(move_num + 1) // 2}. {san_move}")
            else:
                last_line = self.move_listbox.get(tk.END)
                self.move_listbox.delete(tk.END)
                self.move_listbox.insert(tk.END, f"{last_line} {san_move}")
            self.move_listbox.see(tk.END)

    def reset_ui(self) -> None:
        """Reset UI elements to initial state."""
        self.move_listbox.delete(0, tk.END)
        self.game_over_label.config(text="")
        self.play_again_button.pack_forget()
        self.selected_square = None
        self.legal_moves = []
        self.illegal_dest = None
        print("UI reset")

    def show_message(self, message: str) -> None:
        """Display a message (currently logs to console).

        Args:
            message: Message to display
        """
        print(f"GUI message: {message}")

    # ================= Setup Methods =================

    def _setup_player_stats(self) -> None:
        """Setup player statistics display in sidebar."""
        black_frame: tk.Frame = tk.Frame(self.sidebar, bg="#EEE")
        black_frame.pack(pady=(0, 10))
        tk.Label(black_frame, text="Black:", font=("Arial", 12, "bold"), bg="#EEE").pack(
            side="left"
        )
        self.black_name_label: tk.Label = tk.Label(
            black_frame,
            text=self.game.black_player.config.name,
            font=("Arial", 12, "bold"),
            bg="#EEE",
        )
        self.black_name_label.pack(side="left", padx=(5, 10))
        self.black_score_label: tk.Label = tk.Label(
            black_frame, text="Score: 0", font=("Arial", 10), bg="#EEE"
        )
        self.black_score_label.pack(side="left")
        self.black_stats: tk.Label = tk.Label(
            self.sidebar, text="Wins: 0  Losses: 0", font=("Arial", 10), bg="#EEE"
        )
        self.black_stats.pack(pady=(0, 10))

        white_frame: tk.Frame = tk.Frame(self.sidebar, bg="#EEE")
        white_frame.pack(pady=(0, 10))
        tk.Label(white_frame, text="White:", font=("Arial", 12, "bold"), bg="#EEE").pack(
            side="left"
        )
        self.white_name_label: tk.Label = tk.Label(
            white_frame,
            text=self.game.white_player.config.name,
            font=("Arial", 12, "bold"),
            bg="#EEE",
        )
        self.white_name_label.pack(side="left", padx=(5, 10))
        self.white_score_label: tk.Label = tk.Label(
            white_frame, text="Score: 0", font=("Arial", 10), bg="#EEE"
        )
        self.white_score_label.pack(side="left")
        self.white_stats: tk.Label = tk.Label(
            self.sidebar, text="Wins: 0  Losses: 0", font=("Arial", 10), bg="#EEE"
        )
        self.white_stats.pack(pady=(0, 20))

        self.white_timer_label: tk.Label = tk.Label(
            white_frame, text="10:00", font=("Arial", 12), bg="#EEE"
        )
        self.white_timer_label.pack(side="left", padx=(5, 0))

        self.black_timer_label: tk.Label = tk.Label(
            black_frame, text="10:00", font=("Arial", 12), bg="#EEE"
        )
        self.black_timer_label.pack(side="left", padx=(5, 0))

    # ================= Timer Management =================

    def _update_timers(self) -> bool:
        """Update timer display and check for timeout.

        Returns:
            True if a player timed out, False otherwise
        """
        timeout_winner = self.game.update_timer()

        # Format mm:ss
        w_min, w_sec = divmod(max(0, int(self.game.white_time_left)), 60)
        b_min, b_sec = divmod(max(0, int(self.game.black_time_left)), 60)
        self.white_timer_label.config(text=f"{w_min:02}:{w_sec:02}")
        self.black_timer_label.config(text=f"{b_min:02}:{b_sec:02}")

        if timeout_winner:
            self.game_over_label.config(
                text=f"Game Over: {timeout_winner.config.name} won on time!"
            )
            print(f"{timeout_winner.config.name} won on time")
            return True
        return False

    # ================= Board Drawing =================

    def _square_to_xy(self, square: int) -> tuple[int, int]:
        """Convert chess square index to canvas x,y coordinates.

        Args:
            square: Chess square index (0-63)

        Returns:
            Tuple of (x, y) canvas coordinates
        """
        col = chess.square_file(square)
        row = 7 - chess.square_rank(square)
        return col * self.tile_size, row * self.tile_size

    def _draw_board(self) -> None:
        """Draw the complete chessboard with pieces and highlights."""
        self.canvas.delete("all")
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if width <= 0 or height <= 0:
            return

        self.tile_size = min(width, height) // 8
        self._scale_images()

        # Tiles
        for sq in chess.SQUARES:
            x, y = self._square_to_xy(sq)
            col = chess.square_file(sq)
            row = chess.square_rank(sq)
            color = COLOR_BOARD_LIGHT if (row + col) % 2 == 0 else COLOR_BOARD_DARK
            self.canvas.create_rectangle(
                x, y, x + self.tile_size, y + self.tile_size, fill=color, outline=""
            )

        # Highlights
        if self.config.highlight_last_move and self.game.last_move:
            for sq in (self.game.last_move.from_square, self.game.last_move.to_square):
                x, y = self._square_to_xy(sq)
                self.canvas.create_rectangle(
                    x,
                    y,
                    x + self.tile_size,
                    y + self.tile_size,
                    fill=COLOR_HIGHLIGHT_LAST_MOVE,
                    outline="",
                )

        if self.config.highlight_capture_square and self.game.capture_square is not None:
            x, y = self._square_to_xy(self.game.capture_square)
            self.canvas.create_rectangle(
                x,
                y,
                x + self.tile_size,
                y + self.tile_size,
                fill=COLOR_HIGHLIGHT_CAPTURE_SQUARE,
                outline="",
            )

        if self.config.highlight_illegal_move and self.illegal_dest is not None:
            x, y = self._square_to_xy(self.illegal_dest)
            self.canvas.create_rectangle(
                x,
                y,
                x + self.tile_size,
                y + self.tile_size,
                fill=COLOR_HIGHLIGHT_ILLEGAL,
                outline="",
            )
            self.illegal_dest = None

        if self.selected_square is not None:
            if self.config.highlight_selected:
                x0, y0 = self._square_to_xy(self.selected_square)
                self.canvas.create_rectangle(
                    x0,
                    y0,
                    x0 + self.tile_size,
                    y0 + self.tile_size,
                    fill=COLOR_HIGHLIGHT_SELECTED,
                    outline="",
                )
            if self.config.highlight_legal_moves:
                for move in self.legal_moves:
                    x, y = self._square_to_xy(move.to_square)
                    self.canvas.create_rectangle(
                        x,
                        y,
                        x + self.tile_size,
                        y + self.tile_size,
                        fill=COLOR_HIGHLIGHT_LEGAL,
                        outline="",
                    )

        # Pieces
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                sym = piece.symbol()
                if sym in self.piece_images_scaled:
                    x, y = self._square_to_xy(sq)
                    self.canvas.create_image(x, y, anchor="nw", image=self.piece_images_scaled[sym])

        # Game over
        if self.game.is_over():
            result = self.game.result()
            if result == "1-0":
                winner = self.game.white_player
                loser = self.game.black_player
                winner.record_win()
                loser.record_loss()
                self.game_over_label.config(text=f"Game Over: {winner.config.name} won!")
            elif result == "0-1":
                winner = self.game.black_player
                loser = self.game.white_player
                winner.record_win()
                loser.record_loss()
                self.game_over_label.config(text=f"Game Over: {winner.config.name} won!")
            else:
                self.game_over_label.config(text="Game Over: Draw!")

            self.white_stats.config(
                text=f"Wins: {self.game.white_player.config.wins}  Losses: {self.game.white_player.config.losses}"
            )
            self.black_stats.config(
                text=f"Wins: {self.game.black_player.config.wins}  Losses: {self.game.black_player.config.losses}"
            )
            self.play_again_button.pack()
            self._save_game()

    # ================= Image Loading and Scaling =================

    def _download_and_load_images(self) -> None:
        """Download and load chess piece images from chess.com."""
        os.makedirs(self.image_dir, exist_ok=True)
        for sym, code in PIECE_CODES.items():
            path = os.path.join(self.image_dir, f"{code}.png")
            if not os.path.exists(path):
                try:
                    urllib.request.urlretrieve(self.config.base_url + f"{code}.png", path)
                except Exception as e:
                    print(f"ERROR: Failed to download {code}.png: {e}")
                    continue
            try:
                img = Image.open(path).convert("RGBA")
                self.piece_images_raw[sym] = img
            except Exception as e:
                print(f"ERROR: Failed to load {code}.png: {e}")

    def _scale_images(self) -> None:
        """Scale piece images to current tile size."""
        resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        self.piece_images_scaled = {
            sym: ImageTk.PhotoImage(img.resize((self.tile_size, self.tile_size), resample))
            for sym, img in self.piece_images_raw.items()
        }

    # ================= Event Handlers =================

    def _on_resize(self, event: tk.Event) -> None:  # noqa: ARG002
        """Handle window resize event.

        Args:
            event: Tkinter event object
        """
        self._draw_board()

    def _on_click(self, event: tk.Event) -> None:
        """Handle mouse click on chess board.

        Implements piece selection and move execution for human players.

        Args:
            event: Tkinter mouse event
        """
        if not isinstance(self.current_player, HumanPlayer):
            return

        col = event.x // self.tile_size
        row = 7 - (event.y // self.tile_size)
        square = chess.square(col, row)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.legal_moves = [m for m in self.board.legal_moves if m.from_square == square]
        else:
            move = chess.Move(self.selected_square, square)
            if move not in self.board.legal_moves:
                move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
            if move in self.board.legal_moves:
                self.current_player.pending_move = move
                self.selected_square = None
                self.legal_moves = []
            else:
                self.illegal_dest = square
                self.selected_square = None
                self.legal_moves = []

        self._draw_board()

    # ================= Game Loop and Control =================

    def _update_turn_label(self) -> None:
        """Update the turn indicator label."""
        if self.game.is_over():
            self.turn_label.config(text="")
        else:
            color_text = "White" if self.board.turn else "Black"
            player_name = (
                self.game.white_player.config.name
                if self.board.turn
                else self.game.black_player.config.name
            )
            self.turn_label.config(text=f"{color_text}'s turn — {player_name}")

    def _game_loop(self) -> None:
        """Main game loop executed periodically to update game state."""
        # Always update the timer first
        self._update_timers()

        # Stop if game over or timeout
        if self.game.is_over() or self.game.white_time_left <= 0 or self.game.black_time_left <= 0:
            self._draw_board()
            return

        # Handle player move
        self.current_player = self.game.current_player
        move = self.current_player.get_move(self.board)
        if move:
            move_san = self.game.apply_move(move)
            self.update_move_list(move_san)
            white_score, black_score = self.game.get_scores()
            self.update_scores(white_score, black_score)
            self._draw_board()
            self._update_turn_label()

        # Continue loop
        self.after_id = self.root.after(100, self._game_loop)

    # ================= Utility Methods =================

    def _save_game(self) -> None:
        """Save the current game to PGN file."""
        filename = self.game.save_game()
        print(f"Game saved to {filename}")

    def _reset_game(self) -> None:
        """Reset the game state and UI for a new game."""
        self.game.reset()
        self.reset_ui()
        self._update_turn_label()
        self._draw_board()
        print("Game reset")

    def _quit_game(self) -> None:
        """Clean up and quit the application."""
        # Clean up player engines
        for player in [self.game.white_player, self.game.black_player]:
            if hasattr(player, "stop"):
                try:
                    player.stop()
                except Exception as e:
                    print(f"WARNING: Error stopping player: {e}")
            if hasattr(player, "close"):
                try:
                    player.close()
                except Exception as e:
                    print(f"WARNING: Error closing player: {e}")

        # Cancel pending after events
        if self.after_id:
            self.root.after_cancel(self.after_id)

        print("Quitting GUI")
        self.root.destroy()
        sys.exit(0)
