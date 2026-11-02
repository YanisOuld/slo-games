"""Pure Minesweeper data types. No pygame here: data and rules, not rendering."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Difficulty(Enum):
    # value = (label, columns, rows, mines)
    EASY = ("Facile", 9, 9, 10)
    MEDIUM = ("Moyen", 16, 16, 40)
    HARD = ("Difficile", 24, 16, 75)

    def __init__(self, label: str, cols: int, rows: int, mines: int) -> None:
        self.label = label
        self.cols = cols
        self.rows = rows
        self.mines = mines

    def next(self) -> "Difficulty":
        members = list(Difficulty)
        return members[(members.index(self) + 1) % len(members)]


class Status(Enum):
    READY = "ready"      # no click yet: mines are placed on the first reveal
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


@dataclass(frozen=True, order=True)
class Coord:
    x: int  # column
    y: int  # row


@dataclass
class Cell:
    mine: bool = False
    adjacent: int = 0  # mines among the 8 neighbours
    revealed: bool = False
    flagged: bool = False


@dataclass(frozen=True)
class Move:
    """A suggested move. flag=True means "this is a mine", else "reveal this"."""

    coord: Coord
    flag: bool
    certain: bool        # proven by logic, or just the best guess
    risk: float = 0.0    # estimated probability that revealing it hits a mine


@dataclass
class Statistics:
    mines_left: int  # mines minus flags placed (can go negative with wrong flags)
    revealed: int
    safe_total: int
