import chess
import chess.pgn
import sys
import os
import zstandard as zstd
import io
from typing import TextIO, Optional
from pydantic import BaseModel, field_validator


class PGNToCSVConfig(BaseModel):
    source_path: str
    destination_path: str
    verbose: bool = False

    @field_validator("source_path", mode="before")
    def validate_source_path(cls, v: str) -> str:
        if not os.path.exists(v):
            raise ValueError(f"Source file not found: {v}")
        return v

    @field_validator("destination_path", mode="before")
    def validate_destination_path(cls, v: str) -> str:
        if not v.endswith(".csv"):
            raise ValueError("Destination path must end with .csv")
        return v


class GameMetadata(BaseModel):
    white_elo: str
    black_elo: str
    is_black: bool


class BoardState(BaseModel):
    board: list[int]  # Board is a list of integers representing the piece positions
    move: str


def convert_pgn_to_csv(config: PGNToCSVConfig) -> None:
    """
    Converts a PGN file (optionally compressed with Zstandard) to a CSV file representing
    board states and moves.

    Args:
        config (PGNToCSVConfig): Configuration object with source, destination paths, and verbose flag.
    """
    if config.verbose:
        print(f"[INFO] Reading PGN from: {config.source_path}")
        print(f"[INFO] Writing CSV to: {config.destination_path}")

    if config.source_path.endswith(".zst"):
        with open(config.source_path, 'rb') as compressed:
            dctx = zstd.ZstdDecompressor()
            stream_reader = dctx.stream_reader(compressed)
            text_stream = io.TextIOWrapper(stream_reader, encoding='utf-8')

            _process_pgn_stream(text_stream, config)
    else:
        with open(config.source_path, "r", encoding="utf-8") as pgn_file:
            _process_pgn_stream(pgn_file, config)


def _process_pgn_stream(pgn_stream: TextIO, config: PGNToCSVConfig) -> None:
    """
    Processes a text stream containing PGN data and writes parsed game states to CSV.

    Args:
        pgn_stream (TextIO): A text stream of PGN data (could be from decompressed .zst or plain .pgn).
        config (PGNToCSVConfig): Configuration object with destination path and verbose flag.
    """
    header = "white_elo,black_elo,blacks_move,"
    for letter in "ABCDEFGH":
        for num in range(1, 9):
            header += f"{letter}{num},"
    header += "selected_move\n"

    with open(config.destination_path, "w", encoding="utf-8") as csv_file:
        csv_file.write(header)

        game_counter = 0
        pgn: Optional[chess.pgn.Game] = chess.pgn.read_game(pgn_stream)
        while pgn is not None:
            game_counter += 1

            if config.verbose and game_counter % 100 == 0:
                print(f"[INFO] Processing game #{game_counter}")

            white_elo = pgn.headers.get("WhiteElo", "0")
            black_elo = pgn.headers.get("BlackElo", "0")
            board = pgn.board()
            is_black = False

            for move in pgn.mainline_moves():
                row = _convert_board_to_row(board.fen(), GameMetadata(white_elo=white_elo, black_elo=black_elo, is_black=is_black), move.uci())
                csv_file.write(row)
                board.push(move)
                is_black = not is_black

            pgn = chess.pgn.read_game(pgn_stream)

        if config.verbose:
            print(f"[DONE] Processed {game_counter} games.")


def _convert_board_to_row(fen: str, metadata: GameMetadata, move: str) -> str:
    """
    Converts a FEN string and game metadata into a CSV row string.

    Args:
        fen (str): Forsyth-Edwards Notation string representing the board state.
        metadata (GameMetadata): Metadata object containing player ratings and move info.
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

    return f"{metadata.white_elo},{metadata.black_elo},{int(metadata.is_black)},{','.join(map(str, board))},{move}\n"


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python src/pgn_to_csv.py <source_pgn_path> <destination_csv_path> [--verbose]")
        sys.exit(1)

    source: str = sys.argv[1]
    destination: str = sys.argv[2]
    verbose_flag: bool = len(sys.argv) == 4 and sys.argv[3] == "--verbose"

    config = PGNToCSVConfig(source_path=source, destination_path=destination, verbose=verbose_flag)
    convert_pgn_to_csv(config)


if __name__ == "__main__":
    main()
