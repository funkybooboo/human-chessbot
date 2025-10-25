"""
Utility script to populate the 'legal_moves' table with all geometrically valid chess moves.

Usage:
    python -m packages.train.src.dataset.utils.fill_legal_moves
"""

import logging

from packages.train.src.dataset.processers.legal_moves import get_legal_moves
from packages.train.src.dataset.repositories.database import initialize_database
from packages.train.src.dataset.repositories.legal_move import count_legal_moves, save_legal_moves

logger = logging.getLogger(__name__)


def fill_database_with_legal_moves():
    """Generate and insert all legal chess moves into the database."""
    logger.info("Creating legal_moves table if it does not exist...")
    initialize_database()

    logger.info("Generating all possible legal moves...")
    moves = list(get_legal_moves())  # consume iterator for counting
    logger.info("Generated %d legal moves.", len(moves))

    logger.info("Saving moves to the database...")
    save_legal_moves(moves)

    total = count_legal_moves()
    logger.info("Done. Database now contains %d legal moves.", total)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    fill_database_with_legal_moves()
