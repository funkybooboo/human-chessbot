"""
Utility script to populate the 'legal_moves' table with all geometrically valid chess moves.

Usage:
    python -m packages.dataset.src.utils.fill_legal_moves
"""

from packages.train.src.dataset.processers.legal_moves import get_legal_moves
from packages.train.src.dataset.repositories.database import initialize_database
from packages.train.src.dataset.repositories.legal_move import count_legal_moves, save_legal_moves


def fill_database_with_legal_moves():
    """Generate and insert all legal chess moves into the database."""
    print("Creating legal_moves table if it does not exist...")
    initialize_database()

    print("Generating all possible legal moves...")
    moves = list(get_legal_moves())  # consume iterator for counting
    print(f"Generated {len(moves)} legal moves.")

    print("Saving moves to the database...")
    save_legal_moves(moves)

    total = count_legal_moves()
    print(f"Done. Database now contains {total} legal moves.")


if __name__ == "__main__":
    fill_database_with_legal_moves()
