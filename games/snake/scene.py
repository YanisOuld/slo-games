"""SnakeScene: the controller wiring model and views. Only it mutates the model."""
from __future__ import annotations

import logging

import pygame

from engine import constants as sc
from engine.scene import Scene

from . import constants as k
from .game import Gameplay
from .models import Direction
from .panels import BoardPanel, NavigatorPanel

log = logging.getLogger(__name__)

# Keyboard -> Direction. Arrows and WASD both work.
_KEY_DIRECTIONS = {
    pygame.K_UP: Direction.UP,
    pygame.K_DOWN: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT,
    pygame.K_w: Direction.UP,
    pygame.K_s: Direction.DOWN,
    pygame.K_a: Direction.LEFT,
    pygame.K_d: Direction.RIGHT,
}


class SnakeScene(Scene):
    def __init__(self, cols: int = k.GRID_COLS, rows: int = k.GRID_ROWS) -> None:
        self.cols = cols
        self.rows = rows
        self.game = Gameplay(cols, rows)
        self.elapsed = 0.0
        self.move_timer = 0.0  # seconds accumulated toward the next step
        self.message = "Flèches ou ZQSD pour jouer"

        nav_rect = pygame.Rect(0, 0, k.NAV_WIDTH, sc.SCREEN_HEIGHT)
        board_rect = pygame.Rect(k.BOARD_X, 0, k.BOARD_WIDTH, sc.SCREEN_HEIGHT)
        self.board = BoardPanel(board_rect, cols, rows)
        self.nav = NavigatorPanel(nav_rect, self._new_game, self._back)

    def _new_game(self) -> None:
        self.game.reset()
        self.elapsed = 0.0
        self.move_timer = 0.0
        self.message = "Flèches ou ZQSD pour jouer"

    def _back(self) -> None:
        from games.menu.scene import MenuScene  # local import avoids circular import

        self.app.change_scene(MenuScene())

    def _move_interval(self) -> float:
        # Speeds up as the score grows, clamped so it never gets impossibly fast.
        return max(k.MIN_INTERVAL, k.MOVE_INTERVAL - self.game.score * k.SPEEDUP_PER_POINT)

    # -- game loop ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        self.nav.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key in _KEY_DIRECTIONS:
            self.game.set_direction(_KEY_DIRECTIONS[event.key])
            self.message = ""

    def update(self, dt: float) -> None:
        if self.game.game_over:
            return
        self.elapsed += dt
        self.move_timer += dt
        # Catch up in case a frame was slow: step as many times as time allows.
        while self.move_timer >= self._move_interval():
            self.move_timer -= self._move_interval()
            self.game.step()
            if self.game.game_over:
                self.message = f"Perdu ! Score : {self.game.score}"
                break

    def draw(self, screen: pygame.Surface) -> None:
        self.nav.draw(screen, self.game.statistics(), self.elapsed, self.message)
        self.board.draw(screen, self.game.snake, self.game.food)
