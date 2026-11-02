"""Base class for Connect Four brains: read the game, pick a column."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..game import Gameplay


class Connect4Agent(ABC):
    """Agents never mutate the game they're given; the Scene plays the chosen
    column exactly like a human click. Any agent can face any other (or a human)."""

    @abstractmethod
    def choose(self, game: Gameplay) -> int:
        ...
