"""Probability heat map: where are the remaining ships most likely to be?

For every ship still afloat, try every position it could occupy (horizontal and
vertical) given what is known: it can't cover a miss or a sunk ship. Each cell
counts how many possible positions cover it. Positions that explain hits we
already have are far more likely, so they weigh much more.

This is the brain of the hard AI, and it's what the "Chaleur" view shows.
"""
from __future__ import annotations

from ..models import SIZE, CellState, TargetView, cells_of

# How much more likely a position is for each unexplained hit it covers.
_HIT_WEIGHT = 40.0


def heat_map(view: TargetView) -> list[list[float]]:
    """[x][y] -> likelihood in 0..1 (1 = most likely cell). Known cells are 0."""
    heat = [[0.0] * SIZE for _ in range(SIZE)]
    states = view.states
    for size in view.remaining:
        for horizontal in (True, False):
            for x in range(SIZE - size + 1 if horizontal else SIZE):
                for y in range(SIZE if horizontal else SIZE - size + 1):
                    cells = cells_of(x, y, size, horizontal)
                    blocked = False
                    hits = 0
                    for cx, cy in cells:
                        state = states[cx][cy]
                        if state is CellState.MISS or state is CellState.SUNK:
                            blocked = True
                            break
                        if state is CellState.HIT:
                            hits += 1
                    if blocked:
                        continue
                    weight = _HIT_WEIGHT ** hits
                    for cx, cy in cells:
                        if states[cx][cy] is CellState.UNKNOWN:
                            heat[cx][cy] += weight
    top = max(max(col) for col in heat) or 1.0
    return [[v / top for v in col] for col in heat]
