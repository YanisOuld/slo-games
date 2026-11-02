"""Pure billiards data types. No pygame here: data and rules, not rendering."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Group(Enum):
    SOLIDS = "Pleines"    # 1-7
    STRIPES = "Rayées"    # 9-15

    def numbers(self) -> range:
        return range(1, 8) if self is Group.SOLIDS else range(9, 16)

    def other(self) -> "Group":
        return Group.STRIPES if self is Group.SOLIDS else Group.SOLIDS

    @staticmethod
    def of(number: int) -> "Group | None":
        if 1 <= number <= 7:
            return Group.SOLIDS
        if 9 <= number <= 15:
            return Group.STRIPES
        return None


class Phase(Enum):
    AIMING = "aiming"     # waiting for the shooter (may also place the cue ball)
    ROLLING = "rolling"   # balls in motion
    OVER = "over"


class Mode(Enum):
    VS_AI = "vs IA"
    TWO_PLAYERS = "2 joueurs"

    def next(self) -> "Mode":
        return Mode.TWO_PLAYERS if self is Mode.VS_AI else Mode.VS_AI


class Level(Enum):
    EASY = "Facile"
    MEDIUM = "Moyen"
    HARD = "Difficile"

    def next(self) -> "Level":
        members = list(Level)
        return members[(members.index(self) + 1) % len(members)]


@dataclass
class Player:
    name: str
    group: Group | None = None


@dataclass(frozen=True)
class ShotOutcome:
    """Plain-language result of a shot, for the message bar."""

    text: str
    kind: str   # "info" | "success" | "error"
