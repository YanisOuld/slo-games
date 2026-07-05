from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List
from enum import Enum

from .constants import WHITE_RGB, BLACK_RGB, GREY_RGB

@dataclass
class Statistics:
    number_white: int
    number_black: int
    number_none: int
    x: List[List[int]]
    y: List[List[int]]


class PyGameAbstract(ABC):
    @abstractmethod
    def draw():
        pass

@dataclass
class Coord:
    x: int
    y: int


class BoxType(Enum):
    WHITE = WHITE_RGB
    BLACK = BLACK_RGB
    NONE = GREY_RGB

    def next(actual_type):
        types = list(BoxType)
        index = types.index(actual_type)
        next_index = (index + 1) % len(types)
        return types[next_index]

    def convert_to_int(t):
        if t == BoxType.WHITE:
            return 0
        if t == BoxType.BLACK:
            return 1
        else:
            return 4

class HintType(Enum):
    EQUAL = 1
    INVERSE = -1