"""Base class for Snake brains. An agent reads the game and picks the next move."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..game import Gameplay
from ..models import Direction


class SnakeAgent(ABC):
    """A brain for the snake: given the current state, choose the next Direction.

    Agents never mutate the game; the Scene applies the chosen direction, exactly
    like it applies a human keypress. That symmetry is what lets control pass
    between human and AI at any moment.
    """

    @abstractmethod
    def next_direction(self, game: Gameplay) -> Direction:
        ...
