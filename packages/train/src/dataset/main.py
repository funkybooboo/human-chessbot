"""
Main entry point for populating the training dataset database.

This script fills:
1. Game snapshots
2. Legal moves

Usage:
    python -m packages.train.src.dataset.fill_database
"""

import logging

from packages.train.src.dataset.fill_legal_moves import fill_database_with_legal_moves
from packages.train.src.dataset.fill_snapshots import fill_database_with_snapshots

logger = logging.getLogger(__name__)


def main():
    """Fill all dataset tables in the correct order."""
    logger.info("Starting database population process...")

    # Fill snapshots first (since they may be referenced by other tables)
    logger.info("Filling game snapshots...")
    fill_database_with_snapshots()

    # Then fill legal moves
    logger.info("Filling legal moves...")
    fill_database_with_legal_moves()

    logger.info("Database population complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    main()
