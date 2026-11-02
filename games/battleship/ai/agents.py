"""Battleship AIs, from dumb to smart. They only see a TargetView (what a human
would know) and return the cell to shoot; the Scene fires it like a human tap."""
from __future__ import annotations

import random
from abc import ABC, abstractmethod

from ..models import SIZE, Cell, CellState, Level, TargetView
from .probability import heat_map

_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class BattleshipAgent(ABC):
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()

    @abstractmethod
    def choose(self, view: TargetView) -> Cell:
        ...


class RandomAgent(BattleshipAgent):
    """Easy: shoots anywhere it hasn't shot yet."""

    def choose(self, view: TargetView) -> Cell:
        return self.rng.choice(view.unknown_cells())


class HuntTargetAgent(BattleshipAgent):
    """Medium: hunts on a checkerboard (every ship covers at least one black cell),
    and once it hits, targets the neighbours, following the line if two hits align."""

    def choose(self, view: TargetView) -> Cell:
        states = view.states
        hits = {(x, y) for x in range(SIZE) for y in range(SIZE) if states[x][y] is CellState.HIT}
        scores: dict[Cell, int] = {}
        for hx, hy in hits:
            for dx, dy in _DIRECTIONS:
                cx, cy = hx + dx, hy + dy
                if 0 <= cx < SIZE and 0 <= cy < SIZE and states[cx][cy] is CellState.UNKNOWN:
                    in_line = (hx - dx, hy - dy) in hits   # continues a line of hits
                    scores[(cx, cy)] = max(scores.get((cx, cy), 0), 2 if in_line else 1)
        if scores:
            best = max(scores.values())
            return self.rng.choice([c for c, s in scores.items() if s == best])
        unknown = view.unknown_cells()
        checker = [(x, y) for x, y in unknown if (x + y) % 2 == 0]
        return self.rng.choice(checker or unknown)


class ProbabilityAgent(BattleshipAgent):
    """Hard: shoots the cell most likely to hold a ship (see probability.heat_map)."""

    def choose(self, view: TargetView) -> Cell:
        heat = heat_map(view)
        unknown = view.unknown_cells()
        best = max(heat[x][y] for x, y in unknown)
        return self.rng.choice([(x, y) for x, y in unknown if heat[x][y] >= best - 1e-9])


def agent_for(level: Level, rng: random.Random | None = None) -> BattleshipAgent:
    return {Level.EASY: RandomAgent, Level.MEDIUM: HuntTargetAgent,
            Level.HARD: ProbabilityAgent}[level](rng)
