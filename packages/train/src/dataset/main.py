"""
Main entry point for populating the training dataset database.

This script fills:
1. Game snapshots
2. Legal moves

Usage:
    python -m packages.train.src.dataset.main
"""

from packages.train.src.dataset.fillers.fill_legal_moves import fill_database_with_legal_moves
from packages.train.src.dataset.fillers.fill_snapshots import fill_database_with_snapshots


def main():
    """Fill all dataset tables in the correct order."""
    print("Starting database population process...")

    # Fill snapshots first (since they may be referenced by other tables)
    print("Filling game snapshots...")
    fill_database_with_snapshots()

    # Then fill legal moves
    print("Filling legal moves...")
    fill_database_with_legal_moves()

    print("Database population complete.")


if __name__ == "__main__":
    main()
