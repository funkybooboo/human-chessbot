"""Module for converting PGN files to CSV format.

This module provides functionality to convert chess games stored in PGN format
(with optional Zstandard compression) into CSV files where each row represents
a board position and the move made from that position.
"""

import argparse
import io
from pathlib import Path
from typing import TextIO

import chess.pgn
import zstandard as zstd
from pydantic import BaseModel, field_validator


class PGNToCSVConfig(BaseModel):
    """Configuration for PGN to CSV conversion.

    Attributes:
        source_path: Path to the source PGN file (.pgn or .zst compressed).
        destination_path: Path where the CSV file will be saved.
        verbose: If True, print progress information during conversion.
    """

    source_path: Path
    destination_path: Path
    verbose: bool = False

    @field_validator("source_path", mode="before")
    @classmethod
    def validate_source_path(cls, v: str | Path) -> Path:
        """Validate that source file exists."""
        path = Path(v)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")
        return path

    @field_validator("destination_path", mode="before")
    @classmethod
    def validate_destination_path(cls, v: str | Path) -> Path:
        """Validate that destination path ends with .csv and ensure directory exists."""
        path = Path(v)
        if path.suffix != ".csv":
            raise ValueError("Destination path must end with .csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


class GameMetadata(BaseModel):
    """Metadata for a chess game.

    Attributes:
        white_elo: Elo rating of the white player.
        black_elo: Elo rating of the black player.
        is_black: True if the current move is by the black player.
    """

    white_elo: str
    black_elo: str
    is_black: bool


def convert_pgn_to_csv(config: PGNToCSVConfig) -> None:
    """Convert a PGN file to CSV format.

    Converts a PGN file (optionally compressed with Zstandard) to a CSV file where each
    row represents a board position and the move made from that position.

    Args:
        config: Configuration object with source, destination paths, and verbose flag.

    Raises:
        FileNotFoundError: If source file doesn't exist.
        IOError: If there's an error reading or writing files.
    """
    if config.verbose:
        print(f"[INFO] Reading PGN from: {config.source_path}")
        print(f"[INFO] Writing CSV to: {config.destination_path}")

    # Handle Zstandard compressed files
    if config.source_path.suffix == ".zst":
        with open(config.source_path, "rb") as compressed:
            dctx = zstd.ZstdDecompressor()
            stream_reader = dctx.stream_reader(compressed)
            text_stream = io.TextIOWrapper(stream_reader, encoding="utf-8")
            _process_pgn_stream(text_stream, config)
    else:
        with open(config.source_path, encoding="utf-8") as pgn_file:
            _process_pgn_stream(pgn_file, config)


def _process_pgn_stream(pgn_stream: TextIO, config: PGNToCSVConfig) -> None:
    """Process a text stream containing PGN data and write parsed game states to CSV.

    Args:
        pgn_stream: A text stream of PGN data (from decompressed .zst or plain .pgn).
        config: Configuration object with destination path and verbose flag.
    """
    # Build CSV header with all board squares (A1-H8) plus metadata
    header_parts = ["white_elo", "black_elo", "blacks_move"]
    for letter in "ABCDEFGH":
        for num in range(1, 9):
            header_parts.append(f"{letter}{num}")
    header_parts.append("selected_move")
    header = ",".join(header_parts) + "\n"

    with open(config.destination_path, "w", encoding="utf-8") as csv_file:
        csv_file.write(header)

        game_counter = 0
        pgn = chess.pgn.read_game(pgn_stream)

        while pgn is not None:
            game_counter += 1

            if config.verbose and game_counter % 100 == 0:
                print(f"[INFO] Processing game #{game_counter}")

            # Extract game metadata
            white_elo = pgn.headers.get("WhiteElo", "0")
            black_elo = pgn.headers.get("BlackElo", "0")
            board = pgn.board()
            is_black = False

            # Process each move in the game
            for move in pgn.mainline_moves():
                metadata = GameMetadata(white_elo=white_elo, black_elo=black_elo, is_black=is_black)
                row = _convert_board_to_row(board.fen(), metadata, move.uci())
                csv_file.write(row)
                board.push(move)
                is_black = not is_black

            pgn = chess.pgn.read_game(pgn_stream)

        if config.verbose:
            print(f"[DONE] Processed {game_counter} games.")


def _convert_board_to_row(fen: str, metadata: GameMetadata, move: str) -> str:
    """Convert a FEN string and game metadata into a CSV row string.

    The board is represented as 64 integers where:
    - 0 = empty square
    - White pieces: P=1, N=2, B=3, R=4, Q=5, K=6
    - Black pieces: p=7, n=8, b=9, r=10, q=11, k=12

    Args:
        fen: Forsyth-Edwards Notation string representing the board state.
        metadata: Metadata object containing player ratings and move info.
        move: The move in UCI notation.

    Returns:
        A CSV row string representing the board state and move.
    """
    piece_map = {
        "P": 1,
        "N": 2,
        "B": 3,
        "R": 4,
        "Q": 5,
        "K": 6,
        "p": 7,
        "n": 8,
        "b": 9,
        "r": 10,
        "q": 11,
        "k": 12,
    }

    # Parse FEN board position (first part before space)
    board_position = fen.split()[0]
    board = []
    for char in board_position:
        if char == "/":
            continue
        elif char.isdigit():
            # Digit represents empty squares
            board.extend([0] * int(char))
        else:
            # Letter represents a piece
            board.append(piece_map.get(char, 0))

    # Build CSV row: metadata + board positions + move
    board_str = ",".join(map(str, board))
    return (
        f"{metadata.white_elo},{metadata.black_elo},{int(metadata.is_black)},{board_str},{move}\n"
    )


def main() -> None:
    """CLI entry point for converting PGN to CSV."""
    parser = argparse.ArgumentParser(
        description="Convert PGN files to CSV format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source", type=str, help="Path to source PGN file (.pgn or .zst)")
    parser.add_argument("destination", type=str, help="Path to destination CSV file")
    parser.add_argument("--verbose", action="store_true", help="Print progress information")

    args = parser.parse_args()

    config = PGNToCSVConfig(
        source_path=args.source,
        destination_path=args.destination,
        verbose=args.verbose,
    )
    convert_pgn_to_csv(config)


if __name__ == "__main__":
    main()
