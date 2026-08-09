"""Pure Binairo data types. No pygame here: data and rules, not rendering.

Colors live in the view (panels.py); the model only knows WHITE/BLACK/NONE.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class BoxType(Enum):
    NONE = "none"
    WHITE = "white"
    BLACK = "black"

    def next(self) -> "BoxType":
        order = (BoxType.NONE, BoxType.WHITE, BoxType.BLACK)
        return order[(order.index(self) + 1) % len(order)]

    def triplet_value(self) -> int:
        # WHITE=0, BLACK=1: three-in-a-row sums to 0 or 3. NONE=4 never forms a triplet.
        return {BoxType.WHITE: 0, BoxType.BLACK: 1, BoxType.NONE: 4}[self]


@dataclass
class Coord:
    x: int  # column
    y: int  # row


@dataclass(eq=False)
class Box:
    # eq=False + custom __eq__: boxes compare by type only (generation/verify need this).
    x: int
    y: int
    type: BoxType = BoxType.NONE
    is_blocked: bool = False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Box) and self.type == other.type

    def toggle(self) -> None:
        self.type = self.type.next()


class HintType(Enum):
    EQUAL = "="
    INVERSE = "x"


class HintDirection(Enum):
    TOP = (0, 1)
    BOTTOM = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @staticmethod
    def choose_random() -> "HintDirection":
        return random.choice(list(HintDirection))

    def reversed(self) -> "HintDirection":
        dx, dy = self.value
        return HintDirection((-dx, -dy))

    def is_horizontal(self) -> bool:
        return self in (HintDirection.LEFT, HintDirection.RIGHT)


@dataclass
class Hint:
    coord1: Coord
    coord2: Coord
    type: HintType
    direction: HintDirection


@dataclass
class Statistics:
    # per_col[i] / per_row[j] = [white, black, none] counts.
    number_white: int
    number_black: int
    number_none: int
    per_col: list[list[int]]
    per_row: list[list[int]]
