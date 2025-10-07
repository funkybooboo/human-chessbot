import chess
import chess.pgn
import sys
import os
import zstandard as zstd
import io
from typing import TextIO, Tuple, Optional


def convert_pgn_to_csv(source_path: str, destination_path: str, verbose: bool = False) -> None:
    """
    Converts a PGN file (optionally compressed with Zstandard) to a CSV file representing
    board states and moves.

    Args:
        source_path (str): Path to the source PGN file (.pgn or .pgn.zst).
        destination_path (str): Path where the output CSV file will be saved.
        verbose (bool): If True, print detailed processing information.
    """
    if verbose:
        print(f"[INFO] Reading PGN from: {source_path}")
        print(f"[INFO] Writing CSV to: {destination_path}")

    if source_path.endswith(".zst"):
        with open(source_path, 'rb') as compressed:
            dctx = zstd.ZstdDecompressor()
            stream_reader = dctx.stream_reader(compressed)
            text_stream = io.TextIOWrapper(stream_reader, encoding='utf-8')

            _process_pgn_stream(text_stream, destination_path, verbose)
    else:
        with open(source_path, "r", encoding="utf-8") as pgn_file:
            _process_pgn_stream(pgn_file, destination_path, verbose)


def _process_pgn_stream(pgn_stream: TextIO, destination_path: str, verbose: bool = False) -> None:
    """
    Processes a text stream containing PGN data and writes parsed game states to CSV.

    Args:
        pgn_stream (TextIO): A text stream of PGN data (could be from decompressed .zst or plain .pgn).
        destination_path (str): Output CSV file path.
        verbose (bool): If True, print detailed processing information.
    """
    header = "white_elo,black_elo,blacks_move,"
    for letter in "ABCDEFGH":
        for num in range(1, 9):
            header += f"{letter}{num},"
    header += "selected_move\n"

    with open(destination_path, "w", encoding="utf-8") as csv_file:
        csv_file.write(header)

        game_counter = 0
        pgn: Optional[chess.pgn.Game] = chess.pgn.read_game(pgn_stream)
        while pgn is not None:
            game_counter += 1

            if verbose and game_counter % 100 == 0:
                print(f"[INFO] Processing game #{game_counter}")

            white_elo = pgn.headers.get("WhiteElo", "0")
            black_elo = pgn.headers.get("BlackElo", "0")
            board = pgn.board()
            is_black = False

            for move in pgn.mainline_moves():
                row = _convert_board_to_row(board.fen(), (white_elo, black_elo), is_black, move.uci())
                csv_file.write(row)
                board.push(move)
                is_black = not is_black

            pgn = chess.pgn.read_game(pgn_stream)

        if verbose:
            print(f"[DONE] Processed {game_counter} games.")


def _convert_board_to_row(fen: str, elo: Tuple[str, str], is_black: bool, move: str) -> str:
    """
    Converts a FEN string and game metadata into a CSV row string.

    Args:
        fen (str): Forsyth-Edwards Notation string representing the board state.
        elo (Tuple[str, str]): Tuple of white and black player ELO ratings as strings.
        is_black (bool): True if the current move is made by Black, False otherwise.
        move (str): The move in UCI notation.

    Returns:
        str: A CSV row representing the board state and move.
    """
    piece_map = {
        "P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6,
        "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12,
    }

    board_position = fen.split()[0]
    board = []
    for char in board_position:
        if char == "/":
            continue
        elif char.isdigit():
            board.extend([0] * int(char))
        else:
            board.append(piece_map.get(char, 0))

    return f"{elo[0]},{elo[1]},{int(is_black)},{','.join(map(str, board))},{move}\n"


if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python src/pgn_to_csv.py <source_pgn_path> <destination_csv_path> [--verbose]")
        sys.exit(1)

    source: str = sys.argv[1]
    destination: str = sys.argv[2]
    verbose_flag = len(sys.argv) == 4 and sys.argv[3] == "--verbose"

    if not os.path.exists(source):
        print(f"[ERROR] Source file not found: {source}")
        sys.exit(1)

    convert_pgn_to_csv(source, destination, verbose_flag)
