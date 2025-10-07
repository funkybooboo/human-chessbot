import tkinter as tk
from PIL import Image, ImageTk
import chess
import os
import urllib.request
import sys
from typing import Optional, Dict, List, Tuple

from pydantic import BaseModel

from src.play.player.human_player import HumanPlayer
from src.play.ui.ui import Ui
from src.play.game.game import Game

ENABLE_HIGHLIGHT_LEGAL_MOVES = True
ENABLE_HIGHLIGHT_LAST_MOVE = True
ENABLE_HIGHLIGHT_SELECTED = True
ENABLE_HIGHLIGHT_ILLEGAL_MOVE = True
ENABLE_HIGHLIGHT_CAPTURE_SQUARE = True

COLOR_BOARD_LIGHT = "#F0D9B5"
COLOR_BOARD_DARK = "#B58863"
COLOR_HIGHLIGHT_LEGAL = "#A9D18E"
COLOR_HIGHLIGHT_ILLEGAL = "#FF6666"
COLOR_HIGHLIGHT_LAST_MOVE = "#FBFFB8"
COLOR_HIGHLIGHT_SELECTED = "#FFFF00"
COLOR_HIGHLIGHT_CAPTURE_SQUARE = "#FFD700"

PIECE_CODES = { 'P': 'wp', 'R': 'wr', 'N': 'wn', 'B': 'wb', 'Q': 'wq', 'K': 'wk', 'p': 'bp', 'r': 'br', 'n': 'bn', 'b': 'bb', 'q': 'bq', 'k': 'bk', }


class GuiConfig(BaseModel):
    window_width: int = 1300
    window_height: int = 1000
    highlight_legal_moves: bool = True
    highlight_last_move: bool = True
    highlight_selected: bool = True
    highlight_illegal_move: bool = True
    highlight_capture_square: bool = True
    tile_size: int = 64
    image_dir: str = "images"
    base_url: str = "https://images.chesscomfiles.com/chess-themes/pieces/neo/150/"


class Gui(Ui):
    def __init__(self, game: Game, config: GuiConfig = GuiConfig()) -> None:
        super().__init__(game)
        self.config = config

        # Tk root
        self.root: tk.Tk = tk.Tk()
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.root.title("Chess GUI")

        # Game reference
        self.game: Game = game
        self.board: chess.Board = game.board
        self.image_dir: str = self.config.image_dir
        self.current_player: HumanPlayer = self.game.current_player

        # GUI state
        self.tile_size: int = self.config.tile_size
        self.piece_images_raw: Dict[str, Image] = {}
        self.piece_images_scaled: Dict[str, ImageTk.PhotoImage] = {}
        self.selected_square: Optional[int] = None
        self.legal_moves: List[chess.Move] = []
        self.illegal_dest: Optional[int] = None

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
        self.turn_label: tk.Label = tk.Label(self.sidebar, text="", font=("Arial", 14, "bold"), bg="#EEE")
        self.turn_label.pack(pady=(10, 10))

        # Player stats
        self._setup_player_stats()

        # Move list
        tk.Label(self.sidebar, text="Moves", font=("Arial", 12, "bold"), bg="#EEE").pack()
        self.move_listbox: tk.Listbox = tk.Listbox(self.sidebar, font=("Consolas", 10), width=25, height=20)
        self.move_listbox.pack(padx=10, pady=5, fill="both", expand=True)

        # Buttons
        self.save_button: tk.Button = tk.Button(self.sidebar, text="Save Game", command=self._save_game)
        self.save_button.pack(pady=10, fill="x")
        self.new_game_button: tk.Button = tk.Button(self.sidebar, text="New Game", command=self._reset_game,
                                                   bg="#55AAFF", fg="white")
        self.new_game_button.pack(pady=(0, 5), fill="x")
        self.quit_button: tk.Button = tk.Button(self.sidebar, text="Quit", command=self._quit_game,
                                                bg="#FF5555", fg="white")
        self.quit_button.pack(pady=(5, 10), fill="x")

        # Game over / play again
        self.game_over_label: tk.Label = tk.Label(self.sidebar, text="", font=("Arial", 12, "bold"), bg="#EEE", fg="red")
        self.game_over_label.pack(pady=5)
        self.play_again_button: tk.Button = tk.Button(self.sidebar, text="Play Again", command=self._reset_game)
        self.play_again_button.pack(pady=10, fill="x")
        self.play_again_button.pack_forget()

        # Load images
        os.makedirs(self.image_dir, exist_ok=True)
        self._download_and_load_images()

    def run(self) -> None:
        """Start game loop"""
        self._update_turn_label()
        self.root.after(100, self._game_loop)
        self.root.mainloop()

    # ================= Player Stats =================
    def _setup_player_stats(self) -> None:
        """Setup player statistics display"""
        black_frame: tk.Frame = tk.Frame(self.sidebar, bg="#EEE")
        black_frame.pack(pady=(0, 10))
        tk.Label(black_frame, text="Black:", font=("Arial", 12, "bold"), bg="#EEE").pack(side="left")
        self.black_name_label: tk.Label = tk.Label(black_frame, text=self.game.black_player.config.name,
                                                   font=("Arial", 12, "bold"), bg="#EEE")
        self.black_name_label.pack(side="left", padx=(5, 10))
        self.black_score_label: tk.Label = tk.Label(black_frame, text="Score: 0", font=("Arial", 10), bg="#EEE")
        self.black_score_label.pack(side="left")
        self.black_stats: tk.Label = tk.Label(self.sidebar, text="Wins: 0  Losses: 0", font=("Arial", 10), bg="#EEE")
        self.black_stats.pack(pady=(0, 10))

        white_frame: tk.Frame = tk.Frame(self.sidebar, bg="#EEE")
        white_frame.pack(pady=(0, 10))
        tk.Label(white_frame, text="White:", font=("Arial", 12, "bold"), bg="#EEE").pack(side="left")
        self.white_name_label: tk.Label = tk.Label(white_frame, text=self.game.white_player.config.name,
                                                   font=("Arial", 12, "bold"), bg="#EEE")
        self.white_name_label.pack(side="left", padx=(5, 10))
        self.white_score_label: tk.Label = tk.Label(white_frame, text="Score: 0", font=("Arial", 10), bg="#EEE")
        self.white_score_label.pack(side="left")
        self.white_stats: tk.Label = tk.Label(self.sidebar, text="Wins: 0  Losses: 0", font=("Arial", 10), bg="#EEE")
        self.white_stats.pack(pady=(0, 20))

        self.white_timer_label: tk.Label = tk.Label(white_frame, text="10:00", font=("Arial", 12), bg="#EEE")
        self.white_timer_label.pack(side="left", padx=(5, 0))

        self.black_timer_label: tk.Label = tk.Label(black_frame, text="10:00", font=("Arial", 12), bg="#EEE")
        self.black_timer_label.pack(side="left", padx=(5, 0))

    # ================= UI Interface =================
    def display_board(self) -> None:
        """Display the board"""
        self._draw_board()

    def update_scores(self, white_score: int, black_score: int) -> None:
        """Update the player scores"""
        self.white_score_label.config(text=f"Score: {white_score}")
        self.black_score_label.config(text=f"Score: {black_score}")

    def update_move_list(self, san_move: str) -> None:
        """Update the move list"""
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

    def _update_timers(self) -> bool:
        """Update game timers"""
        timeout_winner = self.game.update_timer()

        # Format mm:ss
        w_min, w_sec = divmod(max(0, int(self.game.white_time_left)), 60)
        b_min, b_sec = divmod(max(0, int(self.game.black_time_left)), 60)
        self.white_timer_label.config(text=f"{w_min:02}:{w_sec:02}")
        self.black_timer_label.config(text=f"{b_min:02}:{b_sec:02}")

        if timeout_winner:
            self.game_over_label.config(text=f"Game Over: {timeout_winner.config.name} won on time!")
            return True
        return False

    def reset_ui(self) -> None:
        """Reset UI components"""
        self.move_listbox.delete(0, tk.END)
        self.game_over_label.config(text="")
        self.play_again_button.pack_forget()
        self.selected_square = None
        self.legal_moves = []
        self.illegal_dest = None

    def show_message(self, message: str) -> None:
        """Display messages"""
        print("GUI Message:", message)

    # ================= Board Drawing =================
    def _square_to_xy(self, square: int) -> Tuple[int, int]:
        """Convert square index to x, y coordinates"""
        col = chess.square_file(square)
        row = 7 - chess.square_rank(square)
        return col * self.tile_size, row * self.tile_size

    def _draw_board(self) -> None:
        """Draw the chessboard on the GUI"""
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
            self.canvas.create_rectangle(x, y, x + self.tile_size, y + self.tile_size, fill=color, outline="")

        # Highlights
        if self.config.highlight_last_move and self.game.last_move:
            for sq in (self.game.last_move.from_square, self.game.last_move.to_square):
                x, y = self._square_to_xy(sq)
                self.canvas.create_rectangle(x, y, x + self.tile_size, y + self.tile_size,
                                             fill=COLOR_HIGHLIGHT_LAST_MOVE, outline="")

        if self.config.highlight_capture_square and self.game.capture_square is not None:
            x, y = self._square_to_xy(self.game.capture_square)
            self.canvas.create_rectangle(x, y, x + self.tile_size, y + self.tile_size,
                                         fill=COLOR_HIGHLIGHT_CAPTURE_SQUARE, outline="")

        if self.config.highlight_illegal_move and self.illegal_dest is not None:
            x, y = self._square_to_xy(self.illegal_dest)
            self.canvas.create_rectangle(x, y, x + self.tile_size, y + self.tile_size,
                                         fill=COLOR_HIGHLIGHT_ILLEGAL, outline="")
            self.illegal_dest = None

        if self.selected_square is not None:
            if self.config.highlight_selected:
                x0, y0 = self._square_to_xy(self.selected_square)
                self.canvas.create_rectangle(x0, y0, x0 + self.tile_size, y0 + self.tile_size,
                                             fill=COLOR_HIGHLIGHT_SELECTED, outline="")
            if self.config.highlight_legal_moves:
                for move in self.legal_moves:
                    x, y = self._square_to_xy(move.to_square)
                    self.canvas.create_rectangle(x, y, x + self.tile_size, y + self.tile_size,
                                                 fill=COLOR_HIGHLIGHT_LEGAL, outline="")

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
                winner, loser = self.game.white_player, self.game.black_player
            elif result == "0-1":
                winner, loser = self.game.black_player, self.game.white_player
            else:
                winner = loser = None

            if winner:
                winner.record_win()
                loser.record_loss()
                self.game_over_label.config(text=f"Game Over: {winner.config.name} won!")
            else:
                self.game_over_label.config(text="Game Over: Draw!")

            self.white_stats.config(text=f"Wins: {self.game.white_player.config.wins}  Losses: {self.game.white_player.config.losses}")
            self.black_stats.config(text=f"Wins: {self.game.black_player.config.wins}  Losses: {self.game.black_player.config.losses}")
            self.play_again_button.pack()
            self._save_game()

    # ================= Image Loading =================
    def _download_and_load_images(self) -> None:
        os.makedirs(self.image_dir, exist_ok=True)
        for sym, code in PIECE_CODES.items():
            path = os.path.join(self.image_dir, f"{code}.png")
            if not os.path.exists(path):
                try:
                    urllib.request.urlretrieve(self.config.base_url + f"{code}.png", path)
                except Exception as e:
                    print(f"Failed to download {code}.png: {e}")
                    continue
            try:
                img = Image.open(path).convert("RGBA")
                self.piece_images_raw[sym] = img
            except Exception as e:
                print(f"Failed to load {code}.png: {e}")

    def _scale_images(self) -> None:
        """Scale images for chess pieces"""
        resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        self.piece_images_scaled = {
            sym: ImageTk.PhotoImage(img.resize((self.tile_size, self.tile_size), resample))
            for sym, img in self.piece_images_raw.items()
        }

    # ================= Event Handling =================
    def _on_resize(self, event: tk.Event) -> None:
        self._draw_board()

    def _on_click(self, event: tk.Event) -> None:
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

    # ================= Game Loop =================
    def _update_turn_label(self) -> None:
        """Update the turn label"""
        if self.game.is_over():
            self.turn_label.config(text="")
        else:
            color_text = "White" if self.board.turn else "Black"
            player_name = self.game.white_player.config.name if self.board.turn else self.game.black_player.config.name
            self.turn_label.config(text=f"{color_text}'s turn — {player_name}")

    def _game_loop(self) -> None:
        """Main game loop to handle moves and updates"""
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
        self.root.after_id = self.root.after(100, self._game_loop)

    # ================= Utility =================
    def _save_game(self) -> None:
        """Save the current game"""
        filename = self.game.save_game()
        print(f"Game saved to {filename}")

    def _reset_game(self) -> None:
        """Reset the game state and UI"""
        self.game.reset()
        self.reset_ui()
        self._update_turn_label()
        self._draw_board()

    def _quit_game(self) -> None:
        """Quit the game"""
        for player in [self.game.white_player, self.game.black_player]:
            if hasattr(player, "stop"):
                try:
                    player.stop()
                except:
                    pass
            if hasattr(player, "close"):
                try:
                    player.close()
                except:
                    pass
        if hasattr(self, "after_id"):
            self.root.after_cancel(self.after_id)
        self.root.destroy()
        sys.exit(0)
