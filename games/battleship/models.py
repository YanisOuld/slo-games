"""Pure Battleship data types. No pygame here: data and rules, not rendering.

Convention: cells are (x, y) = (column, row), both 0..SIZE-1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

SIZE = 10
FLEET: tuple[tuple[str, int], ...] = (
    ("Porte-avions", 5),
    ("Croiseur", 4),
    ("Destroyer", 3),
    ("Sous-marin", 3),
    ("Torpilleur", 2),
)

Cell = tuple[int, int]


class ShotResult(Enum):
    MISS = "miss"
    HIT = "hit"
    SUNK = "sunk"


class CellState(Enum):
    """What the shooter knows about a cell of the opponent's grid."""

    UNKNOWN = 0
    MISS = 1
    HIT = 2    # hit, ship not sunk yet
    SUNK = 3   # part of a sunk ship (revealed)


class Phase(Enum):
    PLACEMENT = "placement"
    BATTLE = "battle"
    OVER = "over"


class Level(Enum):
    EASY = "Facile"
    MEDIUM = "Moyen"
    HARD = "Difficile"

    def next(self) -> "Level":
        members = list(Level)
        return members[(members.index(self) + 1) % len(members)]


@dataclass
class Ship:
    name: str
    size: int
    x: int = -1          # bow cell; -1 = not placed
    y: int = -1
    horizontal: bool = True
    hits: set[Cell] = field(default_factory=set)

    @property
    def placed(self) -> bool:
        return self.x >= 0

    @property
    def sunk(self) -> bool:
        return len(self.hits) == self.size

    def cells(self) -> list[Cell]:
        return cells_of(self.x, self.y, self.size, self.horizontal)


def cells_of(x: int, y: int, size: int, horizontal: bool) -> list[Cell]:
    return [(x + i, y) if horizontal else (x, y + i) for i in range(size)]


@dataclass(frozen=True)
class Shot:
    x: int
    y: int
    result: ShotResult
    ship: int | None = None   # index of the ship hit, if any


@dataclass
class TargetView:
    """Everything a shooter is allowed to know: its shots so far, and which ship
    sizes are still afloat (a sunk ship is announced, as in the real game)."""

    states: list[list[CellState]]   # [x][y]
    remaining: list[int]            # sizes of ships not sunk yet

    def unknown_cells(self) -> list[Cell]:
        return [(x, y) for x in range(SIZE) for y in range(SIZE) if self.states[x][y] is CellState.UNKNOWN]


@dataclass
class SideStats:
    shots: int = 0
    hits: int = 0

    @property
    def accuracy(self) -> float:
        return self.hits / self.shots if self.shots else 0.0
