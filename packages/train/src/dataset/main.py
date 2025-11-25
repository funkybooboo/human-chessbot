"""
Main entry point for populating the training dataset database.

This script fills:
1. Game snapshots and statistics
2. Legal moves

Usage:
    python -m packages.train.src.dataset.main
"""

from packages.train.src.dataset.pipeline import pipeline


def main():
    pipeline()


if __name__ == "__main__":
    main()
