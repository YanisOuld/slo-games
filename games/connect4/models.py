"""Pure Connect Four data types. No pygame here: data and rules, not rendering."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Piece(Enum):
    NONE = 0
    RED = 1
    YELLOW = 2

    def other(self) -> "Piece":
        return {Piece.RED: Piece.YELLOW, Piece.YELLOW: Piece.RED}.get(self, Piece.NONE)

    @property
    def label(self) -> str:
        return {Piece.RED: "Rouge", Piece.YELLOW: "Jaune"}.get(self, "")


class Mode(Enum):
    VS_AI = "vs IA"
    TWO_PLAYERS = "2 joueurs"

    def next(self) -> "Mode":
        return Mode.TWO_PLAYERS if self is Mode.VS_AI else Mode.VS_AI


class Level(Enum):
    # value = (label, search depth in plies)
    EASY = ("Facile", 1)
    MEDIUM = ("Moyen", 3)
    HARD = ("Difficile", 6)

    def __init__(self, label: str, depth: int) -> None:
        self.label = label
        self.depth = depth

    def next(self) -> "Level":
        members = list(Level)
        return members[(members.index(self) + 1) % len(members)]


@dataclass
class Score:
    red: int = 0
    yellow: int = 0
    draws: int = 0
