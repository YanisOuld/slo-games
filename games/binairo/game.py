"""Binairo rules. No pygame. Convention: grid[col][row] (col = x, row = y)."""
from __future__ import annotations

import logging
import math
import random

from .models import Box, BoxType, Coord, Hint, HintDirection, HintType, Statistics

log = logging.getLogger(__name__)

Grid = list[list[Box]]

ACTION_CHANCE = 0.30  # chance a start cell is already revealed
HINT_CHANCE = 0.70    # chance to place a hint on a hidden cell


class Gameplay:
    def __init__(self, size: int = 10) -> None:
        if size % 2 != 0:
            raise ValueError("size must be even")
        self.size = size
        self.answer = self._generate_solution()
        self.player_game = self._generate_start_map(self.answer)
        self.hints: list[Hint] = []
        self._seed_hints()
        log.info("new game: size=%d hints=%d", size, len(self.hints))

    # -- public API used by the Scene --

    def is_cell_blocked(self, col: int, row: int) -> bool:
        return self.player_game[col][row].is_blocked

    def toggle_cell(self, col: int, row: int) -> None:
        if self._inside(col, row):
            self.player_game[col][row].toggle()

    def verify(self) -> bool:
        solved = all(
            self.player_game[c][r] == self.answer[c][r]
            for c in range(self.size)
            for r in range(self.size)
        )
        log.info("verify -> %s", solved)
        return solved

    def statistics(self) -> Statistics:
        white = black = none = 0
        per_col = [[0, 0, 0] for _ in range(self.size)]
        per_row = [[0, 0, 0] for _ in range(self.size)]
        slot = {BoxType.WHITE: 0, BoxType.BLACK: 1, BoxType.NONE: 2}
        for c in range(self.size):
            for r in range(self.size):
                s = slot[self.player_game[c][r].type]
                per_col[c][s] += 1
                per_row[r][s] += 1
        for col in per_col:
            white, black, none = white + col[0], black + col[1], none + col[2]
        return Statistics(white, black, none, per_col, per_row)

    # -- generation --

    def _generate_solution(self) -> Grid:
        # Start from a valid checkerboard, permute 2x2 squares while avoiding triplets.
        grid = self._checkerboard()
        done = 0
        while done < self.size ** 2:
            x, y = self._random_pos()
            if not self._is_square_checker(grid, x, y):
                continue
            self._swap(grid, x, y, x, y - 1)
            self._swap(grid, x - 1, y, x - 1, y - 1)
            if self._has_triplets(grid):
                self._swap(grid, x, y, x, y - 1)
                self._swap(grid, x - 1, y, x - 1, y - 1)
            else:
                done += 1
        return grid

    def _generate_start_map(self, solution: Grid) -> Grid:
        start = self._empty_grid()
        for c in range(self.size):
            for r in range(self.size):
                if random.random() < ACTION_CHANCE:
                    start[c][r].type = solution[c][r].type
                    start[c][r].is_blocked = True
        return start

    def _seed_hints(self) -> None:
        for c in range(self.size):
            for r in range(self.size):
                if self.player_game[c][r].type is BoxType.NONE and random.random() < HINT_CHANCE:
                    self._add_hint(Coord(c, r), HintDirection.choose_random())

    def _add_hint(self, c1: Coord, direction: HintDirection) -> None:
        dx, dy = direction.value
        c2 = Coord(c1.x + dx, c1.y + dy)
        if not self._inside(c2.x, c2.y):
            direction = direction.reversed()
            dx, dy = direction.value
            c2 = Coord(c1.x + dx, c1.y + dy)
        same = self.answer[c1.x][c1.y] == self.answer[c2.x][c2.y]
        self.hints.append(Hint(c1, c2, HintType.EQUAL if same else HintType.INVERSE, direction))

    # -- helpers --

    def _empty_grid(self, t: BoxType = BoxType.NONE) -> Grid:
        return [[Box(c, r, t) for r in range(self.size)] for c in range(self.size)]

    def _checkerboard(self) -> Grid:
        grid = self._empty_grid()
        for c in range(self.size):
            for r in range(self.size):
                grid[c][r].type = BoxType.WHITE if (c + r) % 2 == 0 else BoxType.BLACK
        return grid

    def _has_triplets(self, grid: Grid) -> bool:
        for c in range(self.size):
            for r in range(self.size):
                center = grid[c][r].type.triplet_value()
                r1 = grid[c + 1][r].type.triplet_value() if self._inside(c + 1, r) else 4
                r2 = grid[c + 2][r].type.triplet_value() if self._inside(c + 2, r) else 4
                t1 = grid[c][r + 1].type.triplet_value() if self._inside(c, r + 1) else 4
                t2 = grid[c][r + 2].type.triplet_value() if self._inside(c, r + 2) else 4
                if center + r1 + r2 in (0, 3) or center + t1 + t2 in (0, 3):
                    return True
        return False

    def _is_square_checker(self, grid: Grid, x: int, y: int) -> bool:
        return (
            grid[x][y] == grid[x - 1][y - 1]
            and grid[x - 1][y] == grid[x][y - 1]
            and grid[x][y] != grid[x][y - 1]
        )

    def _inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def _random_pos(self) -> tuple[int, int]:
        upper = self.size - 1
        return math.ceil(random.random() * upper), math.ceil(random.random() * upper)

    def _swap(self, grid: Grid, x: int, y: int, w: int, z: int) -> None:
        grid[x][y].type, grid[w][z].type = grid[w][z].type, grid[x][y].type
