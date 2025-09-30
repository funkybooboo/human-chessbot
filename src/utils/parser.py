import chess
import chess.pgn
import sys


def convert_to_csv(file_path: str):
    """
    Converts a PGN chess file to a CSV file containing board states after each move.

    Each row in the CSV contains the white and black ELO ratings, a flag indicating if the move was made by black,
    and the board state encoded as integers for each square.

    Args:
        file_path (str): Path to the PGN file to be converted.
    """

    print(file_path)
    pgn = open(file_path)

    # create the header for the csv file
    header = "white_elo,black_elo,blacks_move,"

    for letter in "ABCDEFGH":
        for num in range(1, 9):
            header += f"{letter}{num},"

    # add target (selected move to end)
    header += "selected_move\n"

    csv_name = file_path.split(".")[0] + ".csv"
    with open(csv_name, mode="w") as csv:
        csv.write(f"{header}")

        current_game = chess.pgn.read_game(pgn)

        while current_game is not None:
            # get game info
            elo = (current_game.headers["WhiteElo"], current_game.headers["BlackElo"])
            board = current_game.board()
            is_black = False

            # loop through moves and save board states to csv
            for move in current_game.mainline_moves():
                # convert current board to row
                row = convert_board_to_row(board.fen(), elo, is_black, move.uci())

                # save to csv
                csv.write(row)

                # move to next board
                board.push(move)
                is_black = not is_black  # toggle every move

            current_game = chess.pgn.read_game(pgn)


def convert_board_to_row(fen: str, elo: tuple, is_black: bool, move: str) -> str:
    """
    Converts a FEN string and game metadata into a CSV row.

    The board is encoded as a sequence of integers representing pieces and empty squares.
    The row includes ELO ratings, a flag for black's move, and the board state.

    Args:
        fen (str): FEN string representing the board state.
        elo (tuple): Tuple containing white and black ELO ratings.
        is_black (bool): True if the move was made by black, False otherwise.
        move (str): UCI Chess notation for player selected move from current board state

    Returns:
        str: A CSV-formatted string representing the board state and metadata.
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

    board = []
    for char in fen:  # skip line splits
        if char == "/":
            continue
        # digits indicate sequences of empty spaces so we simply make the next 'n' spaces 0
        elif char.isdigit():
            board.extend([0] * int(char))
        else:
            board.append(piece_map.get(char, 0))

    return f"{','.join(elo)},{int(is_black)},{','.join([str(piece) for piece in board])}{move}\n"


if __name__ == "__main__":
    print(sys.argv)

    # get file_path
    path = sys.argv[1]
    convert_to_csv(path)
