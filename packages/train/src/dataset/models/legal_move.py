from dataclasses import dataclass


@dataclass(frozen=True)
class LegalMove:
    move: str
    types: list[str]
