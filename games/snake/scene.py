"""SnakeScene: the controller wiring model and views. Only it mutates the model."""
from __future__ import annotations

import logging

import pygame

from engine import constants as sc
from engine.scene import Scene

from . import constants as k
from .ai import HamiltonianAgent
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
        self.agent = HamiltonianAgent(cols, rows)
        self.ai_enabled = False
        self.restart_timer = 0.0  # counts down the AI's game-over pause
        self.elapsed = 0.0
        self.move_timer = 0.0  # seconds accumulated toward the next step
        self.message = "Flèches ou ZQSD pour jouer"

        nav_rect = pygame.Rect(0, 0, k.NAV_WIDTH, sc.SCREEN_HEIGHT)
        board_rect = pygame.Rect(k.BOARD_X, 0, k.BOARD_WIDTH, sc.SCREEN_HEIGHT)
        self.board = BoardPanel(board_rect, cols, rows)
        self.nav = NavigatorPanel(nav_rect, self._new_game, self._toggle_ai, self._back)

    def _new_game(self) -> None:
        self.game.reset()
        self.elapsed = 0.0
        self.move_timer = 0.0
        self.restart_timer = 0.0
        self.message = "IA aux commandes" if self.ai_enabled else "Flèches ou ZQSD pour jouer"

    def _toggle_ai(self) -> None:
        self.ai_enabled = not self.ai_enabled
        self.nav.set_ai_label(self.ai_enabled)
        self.restart_timer = 0.0
        self.message = "IA aux commandes" if self.ai_enabled else "À toi de jouer"

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
            if self.ai_enabled:  # a keypress means the human takes control back
                self.ai_enabled = False
                self.nav.set_ai_label(False)
                self.message = "À toi de jouer"
            self.game.set_direction(_KEY_DIRECTIONS[event.key])

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.move_timer += dt
        # Catch up in case a frame was slow: step as many times as time allows.
        while self.move_timer >= self._move_interval():
            self.move_timer -= self._move_interval()
            if self.ai_enabled:  # the AI decides fresh before each step
                self.game.set_direction(self.agent.next_direction(self.game))
            self.game.step()
            if self.game.game_over:
                self.message = f"Perdu ! Score : {self.game.score}"
                break

    def draw(self, screen: pygame.Surface) -> None:
        self.nav.draw(screen, self.game.statistics(), self.elapsed, self.message)
        self.board.draw(screen, self.game.snake, self.game.food)
