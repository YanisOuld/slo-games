"""BinairoScene: the controller wiring model and views. Only it mutates the model."""
from __future__ import annotations

import logging

import pygame

from engine import constants as sc
from engine.scene import Scene

from . import constants as k
from .game import Gameplay
from .panels import BoardPanel, NavigatorPanel

log = logging.getLogger(__name__)


class BinairoScene(Scene):
    def __init__(self, size: int = k.GRID_SIZE) -> None:
        self.size = size
        self.game = Gameplay(size)
        self.elapsed = 0.0
        self.message = ""
        self.solved = False

        nav_rect = pygame.Rect(0, 0, k.NAV_WIDTH, sc.SCREEN_HEIGHT)
        board_rect = pygame.Rect(k.BOARD_X, 0, k.BOARD_WIDTH, sc.SCREEN_HEIGHT)
        self.board = BoardPanel(board_rect, size, on_cell_click=self._on_cell)
        self.nav = NavigatorPanel(nav_rect, self._new_game, self._verify, self._back)

    def _on_cell(self, col: int, row: int) -> None:
        if not self.solved and not self.game.is_cell_blocked(col, row):
            self.game.toggle_cell(col, row)
            self.message = ""

    def _new_game(self) -> None:
        self.game = Gameplay(self.size)
        self.elapsed = 0.0
        self.solved = False
        self.message = ""

    def _verify(self) -> None:
        self.solved = self.game.verify()
        self.message = "Gagné !" if self.solved else "Pas encore..."

    def _back(self) -> None:
        from games.menu.scene import MenuScene  # local import avoids circular import

        self.app.change_scene(MenuScene())

    # -- game loop ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        self.nav.handle_event(event)
        self.board.handle_event(event)

    def update(self, dt: float) -> None:
        if not self.solved:
            self.elapsed += dt

    def draw(self, screen: pygame.Surface) -> None:
        self.nav.draw(screen, self.elapsed, self.message)
        self.board.draw(screen, self.game.player_game, self.game.hints, self.game.statistics())
