"""Pure Snake data types. No pygame here: data and rules, not rendering.

Colors live in the view (panels.py); the model only knows coordinates and directions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    # value = (dx, dy) in grid cells. y grows downward, like the screen.
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def opposite(self) -> "Direction":
        dx, dy = self.value
        return Direction((-dx, -dy))


@dataclass(frozen=True)
class Coord:
    # frozen so coords are hashable/comparable: needed for collision and food spawn.
    x: int  # column
    y: int  # row

    def moved(self, direction: Direction) -> "Coord":
        dx, dy = direction.value
        return Coord(self.x + dx, self.y + dy)


@dataclass
class Statistics:
    score: int
    length: int
    best: int
