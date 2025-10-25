"""Module for combining multiple PGN files into a single file."""

import argparse
from pathlib import Path

from pydantic import BaseModel, field_validator


class PGNCombineConfig(BaseModel):
    """Configuration for combining PGN files.

    Attributes:
        pgn1_path: Path to the first PGN file.
        pgn2_path: Path to the second PGN file.
        output_path: Path where the combined PGN file will be saved.
        delete_old: If True, delete original files after combining.
    """

    pgn1_path: Path
    pgn2_path: Path
    output_path: Path
    delete_old: bool = False

    @field_validator("pgn1_path", "pgn2_path", mode="before")
    @classmethod
    def validate_file_exists(cls, v: str | Path) -> Path:
        """Validate that input files exist."""
        path = Path(v)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return path

    @field_validator("output_path", mode="before")
    @classmethod
    def ensure_output_dir_exists(cls, v: str | Path) -> Path:
        """Ensure output directory exists, creating it if necessary."""
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


def combine_pgn_files(config: PGNCombineConfig) -> None:
    """Combine two PGN files into one and optionally delete the originals.

    Args:
        config: Configuration object containing input/output paths and options.

    Raises:
        FileNotFoundError: If either input file doesn't exist.
        IOError: If there's an error reading or writing files.
    """
    # Read both input files
    with open(config.pgn1_path, encoding="utf-8") as f1:
        content1 = f1.read().strip()

    with open(config.pgn2_path, encoding="utf-8") as f2:
        content2 = f2.read().strip()

    # Combine with proper PGN formatting (double newline between games)
    combined = f"{content1}\n\n{content2}\n"

    # Write combined content
    with open(config.output_path, "w", encoding="utf-8") as out:
        out.write(combined)

    print(f"Combined PGNs saved to: {config.output_path}")

    # Optionally delete original files
    if config.delete_old:
        config.pgn1_path.unlink()
        config.pgn2_path.unlink()
        print("Original files deleted.")


def main() -> None:
    """CLI entry point for combining PGN files."""
    parser = argparse.ArgumentParser(
        description="Combine two PGN files into one.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pgn1", type=str, help="Path to first PGN file")
    parser.add_argument("pgn2", type=str, help="Path to second PGN file")
    parser.add_argument("output", type=str, help="Path to output combined PGN file")
    parser.add_argument(
        "--delete-old",
        action="store_true",
        help="Delete original PGN files after combining",
    )

    args = parser.parse_args()

    config = PGNCombineConfig(
        pgn1_path=args.pgn1,
        pgn2_path=args.pgn2,
        output_path=args.output,
        delete_old=args.delete_old,
    )

    combine_pgn_files(config)


if __name__ == "__main__":
    main()
