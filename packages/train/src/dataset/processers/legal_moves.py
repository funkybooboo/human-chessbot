from collections.abc import Iterator

from packages.train.src.dataset.models.legal_move import LegalMove


def get_legal_moves() -> Iterator[LegalMove]:
    """
    Yields all moves that are geometrically valid for any chess piece
    (king, queen, rook, bishop, knight, pawn) at any stage of the game,
    including pawn promotions (to Q, R, B, N).

    Each yielded value is a LegalMove(move: str, types: List[str]).
    """
    files = "ABCDEFGH"
    ranks = "12345678"

    def to_square(x: int, y: int) -> str:
        return files[x] + ranks[y]

    moves: dict[str, set[str]] = {}

    for fx in range(8):
        for fy in range(8):
            start = to_square(fx, fy)

            for tx in range(8):
                for ty in range(8):
                    if (fx, fy) == (tx, ty):
                        continue
                    dx, dy = tx - fx, ty - fy
                    move = start + to_square(tx, ty)

                    def add(piece: str, m: str = move):
                        moves.setdefault(m, set()).add(piece)

                    # Pawn-like moves (both directions)
                    if (abs(dx) == 0 and abs(dy) in (1, 2)) or (abs(dx) == 1 and abs(dy) == 1):
                        add("pawn")

                        # Add promotion variants if reaching last rank
                        if ty in (0, 7):  # rank 1 or 8
                            for promo in "QRBN":
                                add("pawn", start + to_square(tx, ty) + promo)

                    # Knight
                    if (abs(dx), abs(dy)) in {(1, 2), (2, 1)}:
                        add("knight")
                    # Bishop
                    if abs(dx) == abs(dy):
                        add("bishop")
                    # Rook
                    if dx == 0 or dy == 0:
                        add("rook")
                    # Queen
                    if abs(dx) == abs(dy) or dx == 0 or dy == 0:
                        add("queen")
                    # King
                    if abs(dx) <= 1 and abs(dy) <= 1:
                        add("king")

    # Yield sorted moves lazily instead of returning all at once
    for m, t in sorted(moves.items()):
        yield LegalMove(move=m, types=sorted(t))


if __name__ == "__main__":
    # Turn iterator into a list if you need to count
    moves = list(get_legal_moves())
    print(len(moves))
    print([m for m in moves if m.move.startswith("A7")][:12])
