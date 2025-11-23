"""Evaluate random move selection as a baseline for predicting human moves.

This module loads board snapshots from the database, randomly selects a legal move
for each position, and compares it against the actual move played by the human.
"""

import random
import sqlite3

import chess

from packages.train.src.constants import DB_FILE


def load_snapshots(limit: int | None = None) -> list[tuple[str, str]]:
    """Load board snapshots from the database.

    Args:
        limit: Maximum number of snapshots to load. None for all.

    Returns:
        List of tuples (fen, actual_move_san).
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    query = "SELECT fen, move FROM game_snapshots"
    if limit is not None:
        query += f" LIMIT {limit}"

    c.execute(query)
    rows = c.fetchall()
    conn.close()

    return [(row[0], row[1]) for row in rows]


def get_random_move(board: chess.Board) -> chess.Move | None:
    """Select a random legal move from the given board position.

    Args:
        board: Chess board in the current position.

    Returns:
        A randomly selected legal move, or None if no legal moves exist.
    """
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
    return random.choice(legal_moves)


def evaluate_random_baseline(
    snapshots: list[tuple[str, str]],
    verbose: bool = False,
) -> dict[str, float | int]:
    """Evaluate random move selection accuracy against human moves.

    Args:
        snapshots: List of (fen, actual_move_san) tuples.
        verbose: If True, print progress updates.

    Returns:
        Dictionary with evaluation results:
        - total: Total number of positions evaluated
        - correct: Number of positions where random move matched human move
        - accuracy: Percentage of correct predictions
        - avg_legal_moves: Average number of legal moves per position
    """
    total = 0
    correct = 0
    total_legal_moves = 0
    skipped = 0

    for i, (fen, actual_move_san) in enumerate(snapshots):
        try:
            board = chess.Board(fen)
            legal_moves = list(board.legal_moves)

            if not legal_moves:
                skipped += 1
                continue

            total_legal_moves += len(legal_moves)

            # Pick a random move
            random_move = random.choice(legal_moves)
            random_move_san = board.san(random_move)

            # Compare with actual move
            if random_move_san == actual_move_san:
                correct += 1

            total += 1

            if verbose and (i + 1) % 10000 == 0:
                current_accuracy = (correct / total * 100) if total > 0 else 0
                print(f"Processed {i + 1} positions... Current accuracy: {current_accuracy:.2f}%")

        except Exception as e:
            if verbose:
                print(f"Error processing position {i}: {e}")
            skipped += 1
            continue

    accuracy = (correct / total * 100) if total > 0 else 0
    avg_legal_moves = total_legal_moves / total if total > 0 else 0

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "avg_legal_moves": avg_legal_moves,
        "skipped": skipped,
    }


def calculate_theoretical_accuracy(snapshots: list[tuple[str, str]]) -> float:
    """Calculate theoretical random accuracy based on average legal moves.

    The theoretical accuracy of random guessing is 1/N where N is the average
    number of legal moves per position.

    Args:
        snapshots: List of (fen, actual_move_san) tuples.

    Returns:
        Theoretical accuracy percentage.
    """
    total_legal_moves = 0
    count = 0

    for fen, _ in snapshots:
        try:
            board = chess.Board(fen)
            legal_moves = list(board.legal_moves)
            if legal_moves:
                total_legal_moves += len(legal_moves)
                count += 1
        except Exception:
            continue

    if count == 0:
        return 0.0

    avg_legal_moves = total_legal_moves / count
    return (1 / avg_legal_moves) * 100


def main():
    """Run the random move evaluation."""
    print("=" * 60)
    print("Random Move Baseline Evaluation")
    print("=" * 60)
    print()

    # Load snapshots
    print("Loading board snapshots from database...")
    snapshots = load_snapshots()
    print(f"Loaded {len(snapshots)} snapshots")
    print()

    if not snapshots:
        print("No snapshots found in database. Exiting.")
        return

    # Run evaluation
    print("Evaluating random move selection...")
    print("-" * 40)

    results = evaluate_random_baseline(snapshots, verbose=True)

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total positions evaluated: {results['total']:,}")
    print(f"Positions skipped (errors): {results['skipped']:,}")
    print(f"Correct predictions: {results['correct']:,}")
    print(f"Random move accuracy: {results['accuracy']:.2f}%")
    print(f"Average legal moves per position: {results['avg_legal_moves']:.1f}")
    print()

    # Theoretical accuracy
    theoretical = 100 / results["avg_legal_moves"] if results["avg_legal_moves"] > 0 else 0
    print(f"Theoretical random accuracy (1/avg_moves): {theoretical:.2f}%")
    print()
    print("Note: Random accuracy should be close to 1/N where N is the")
    print("average number of legal moves. Any model should beat this baseline.")


if __name__ == "__main__":
    main()
