"""Snake rules. No pygame. Convention: Coord(x=col, y=row), y grows downward."""
from __future__ import annotations

import logging
import random

from .models import Coord, Direction, Statistics

log = logging.getLogger(__name__)


class Gameplay:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.best = 0  # survives across restarts within a scene
        self.reset()

    def reset(self) -> None:
        cx, cy = self.width // 2, self.height // 2
        # Head first: a 3-cell snake heading right, laid out to the left of the head.
        self.snake: list[Coord] = [Coord(cx - i, cy) for i in range(2)]
        self.direction = Direction.RIGHT
        self._next_direction = Direction.RIGHT
        self.food = self._spawn_food()
        self.score = 0
        self.game_over = False
        log.info("new game: %dx%d", self.width, self.height)

    # -- public API used by the Scene --

    def set_direction(self, direction: Direction) -> None:
        # Ignore a 180° turn: the snake can't reverse into its own neck.
        if direction != self.direction.opposite():
            self._next_direction = direction

    def step(self) -> None:
        """Advance the snake one cell. Sets game_over on wall/self collision."""
        if self.game_over:
            return
        self.direction = self._next_direction
        head = self.snake[0].moved(self.direction)
        # The tail vacates its cell this step (unless we eat), so it's safe to move onto it.
        if not self._inside(head) or head in self.snake[:-1]:
            self.game_over = True
            self.best = max(self.best, self.score)
            log.info("game over: score=%d", self.score)
            return
        self.snake.insert(0, head)
        if head == self.food:
            self.score += 1
            if self.score == self.width * self.height - 2:
                self.game_over = True
                self.best = max(self.best, self.score)
                log.info("game over: score=%d", self.score)
                return 
            self.food = self._spawn_food()
        else:
            self.snake.pop()

    def statistics(self) -> Statistics:
        return Statistics(self.score, len(self.snake), self.best)

    # -- helpers --

    def _spawn_food(self) -> Coord:
        occupied = set(self.snake)
        free = [
            Coord(x, y)
            for x in range(self.width)
            for y in range(self.height)
            if Coord(x, y) not in occupied
        ]
        return random.choice(free) if free else self.snake[0]

    def _inside(self, coord: Coord) -> bool:
        return 0 <= coord.x < self.width and 0 <= coord.y < self.height
