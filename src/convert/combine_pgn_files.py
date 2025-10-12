import argparse
import os
from pathlib import Path
from typing import Union
from pydantic import BaseModel, field_validator


class PGNCombineConfig(BaseModel):
    pgn1_path: Union[str, Path]
    pgn2_path: Union[str, Path]
    output_path: Union[str, Path]
    delete_old: bool = False

    # Validate that input files exist
    @field_validator("pgn1_path", "pgn2_path", mode="before")
    def validate_file_exists(cls, v: Union[str, Path]) -> Path:
        path = Path(v)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        return path

    # Ensure output directory exists
    @field_validator("output_path", mode="before")
    def ensure_output_dir_exists(cls, v: Union[str, Path]) -> Path:
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


def combine_pgn_files(config: PGNCombineConfig) -> None:
    """
    Combines two PGN files into one and optionally deletes the originals.
    """
    with open(config.pgn1_path, "r", encoding="utf-8") as f1, open(config.pgn2_path, "r", encoding="utf-8") as f2:
        content1: str = f1.read().strip()
        content2: str = f2.read().strip()

    combined: str = content1 + "\n\n" + content2 + "\n"

    with open(config.output_path, "w", encoding="utf-8") as out:
        out.write(combined)

    print(f"Combined PGNs saved to: {config.output_path}")

    if config.delete_old:
        os.remove(config.pgn1_path)
        os.remove(config.pgn2_path)
        print("Original files deleted.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine two PGN files into one.")
    parser.add_argument("pgn1", type=str, help="Path to first PGN file")
    parser.add_argument("pgn2", type=str, help="Path to second PGN file")
    parser.add_argument("output", type=str, help="Path to output combined PGN file")
    parser.add_argument("--delete-old", action="store_true", help="Delete original PGN files after combining")

    args = parser.parse_args()

    config = PGNCombineConfig(
        pgn1_path=args.pgn1,
        pgn2_path=args.pgn2,
        output_path=args.output,
        delete_old=args.delete_old
    )

    combine_pgn_files(config)


if __name__ == "__main__":
    main()
