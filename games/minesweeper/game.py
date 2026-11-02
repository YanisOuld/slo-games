"""Minesweeper rules. No pygame. Convention: Coord(x=col, y=row), y grows downward."""
from __future__ import annotations

import logging
import random

from .models import Cell, Coord, Difficulty, Statistics, Status

log = logging.getLogger(__name__)


class Gameplay:
    def __init__(self, difficulty: Difficulty = Difficulty.EASY) -> None:
        self.difficulty = difficulty
        self.reset()

    def reset(self, difficulty: Difficulty | None = None) -> None:
        if difficulty is not None:
            self.difficulty = difficulty
        d = self.difficulty
        self.width, self.height, self.mines = d.cols, d.rows, d.mines
        self.cells: dict[Coord, Cell] = {
            Coord(x, y): Cell() for y in range(self.height) for x in range(self.width)
        }
        self.status = Status.READY
        self.exploded: Coord | None = None
        self.flags = 0
        self.revealed = 0
        log.info("new game: %s %dx%d, %d mines", d.label, self.width, self.height, self.mines)

    # -- public API used by the Scene -----------------------------------------

    def is_over(self) -> bool:
        return self.status in (Status.WON, Status.LOST)

    def reveal(self, coord: Coord) -> None:
        if self.is_over() or coord not in self.cells:
            return
        cell = self.cells[coord]
        if cell.flagged or cell.revealed:
            return
        if self.status is Status.READY:
            self._place_mines(coord)
            self.status = Status.PLAYING
        if cell.mine:
            self._lose(coord)
            return
        self._flood(coord)
        self._check_win()

    def chord(self, coord: Coord) -> None:
        """On a revealed number whose mines are all flagged, reveal the other neighbours."""
        if self.is_over() or coord not in self.cells:
            return
        cell = self.cells[coord]
        if not cell.revealed or cell.adjacent == 0:
            return
        around = self.neighbors(coord)
        if sum(self.cells[n].flagged for n in around) != cell.adjacent:
            return
        for n in around:
            ncell = self.cells[n]
            if ncell.flagged or ncell.revealed:
                continue
            if ncell.mine:  # a wrong flag elsewhere: chording punishes it
                self._lose(n)
                return
            self._flood(n)
        self._check_win()

    def toggle_flag(self, coord: Coord) -> None:
        if self.is_over() or coord not in self.cells:
            return
        cell = self.cells[coord]
        if cell.revealed:
            return
        cell.flagged = not cell.flagged
        self.flags += 1 if cell.flagged else -1

    def neighbors(self, coord: Coord) -> list[Coord]:
        return [
            Coord(coord.x + dx, coord.y + dy)
            for dy in (-1, 0, 1)
            for dx in (-1, 0, 1)
            if (dx or dy)
            and 0 <= coord.x + dx < self.width
            and 0 <= coord.y + dy < self.height
        ]

    def statistics(self) -> Statistics:
        return Statistics(self.mines - self.flags, self.revealed, len(self.cells) - self.mines)

    # -- helpers ---------------------------------------------------------------

    def _place_mines(self, first: Coord) -> None:
        # The first click and its neighbours are kept clear, so the game always
        # opens on a 0 and the player gets a real starting area.
        forbidden = {first, *self.neighbors(first)}
        candidates = [c for c in self.cells if c not in forbidden]
        for c in random.sample(candidates, min(self.mines, len(candidates))):
            self.cells[c].mine = True
        for c, cell in self.cells.items():
            cell.adjacent = sum(self.cells[n].mine for n in self.neighbors(c))

    def _flood(self, start: Coord) -> None:
        """Reveal start; spread through zeros to open whole empty areas at once."""
        stack = [start]
        while stack:
            c = stack.pop()
            cell = self.cells[c]
            if cell.revealed or cell.flagged:
                continue
            cell.revealed = True
            self.revealed += 1
            if cell.adjacent == 0:
                stack.extend(n for n in self.neighbors(c) if not self.cells[n].revealed)

    def _check_win(self) -> None:
        if self.revealed == len(self.cells) - self.mines:
            self.status = Status.WON
            for cell in self.cells.values():  # flag the remaining mines for the player
                cell.flagged = cell.mine
            self.flags = self.mines
            log.info("won")

    def _lose(self, coord: Coord) -> None:
        self.status = Status.LOST
        self.exploded = coord
        log.info("lost on %s", coord)
