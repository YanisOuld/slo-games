"""BinairoScene: the controller wiring model and views. Only it mutates the model."""
from __future__ import annotations

import logging

import pygame

from engine import constants as sc
from engine.scene import Scene
from engine.sidebar import Action, Sidebar, Stat
from games.icons import render_icon

from . import constants as k
from .game import Gameplay
from .panels import BoardPanel, BoardState

log = logging.getLogger(__name__)


class BinairoScene(Scene):
    def __init__(self, size: int = k.GRID_SIZE) -> None:
        self.size = size
        self.sidebar = Sidebar(
            sc.SCREEN_HEIGHT, "Binairo+", k.ACCENT,
            [Action("Nouvelle partie", self._new_game, "new"),
             Action("Vérifier", self._verify, "check", primary=True),
             Action("Retour au menu", self._back, "back")],
            icon=render_icon("Binairo", 44, k.ACCENT),
            sections=(
                ("Règles", ((None, "Jamais 3 identiques à la suite"),
                            (None, "Autant de chaque couleur par ligne"),
                            ("= x", "même couleur / opposées"))),
                ("Contrôles", (("Clic", "changer  ·  clic droit : inverse"),)),
            ),
        )
        self.board = BoardPanel(pygame.Rect(k.BOARD_X, 0, k.BOARD_WIDTH, sc.SCREEN_HEIGHT),
                                size, on_cell_click=self._on_cell)
        self._new_game()

    def _say(self, message: str, kind: str = "info") -> None:
        self.message, self.message_kind = message, kind

    def _on_cell(self, col: int, row: int, reverse: bool) -> None:
        if self.solved or self.game.is_cell_blocked(col, row):
            return
        self.game.toggle_cell(col, row, reverse)
        self._say("")
        # A full grid is checked automatically: no need to press "Vérifier".
        if self.game.is_full():
            self._verify()

    def _new_game(self) -> None:
        self.game = Gameplay(self.size)
        self.elapsed = 0.0
        self.solved = False
        self._say("")

    def _verify(self) -> None:
        if self.solved:
            return
        self.solved = self.game.verify()
        if self.solved:
            self._say("Grille résolue !", "success")
        elif self.game.triplet_cells() or self.game.broken_hints():
            self._say("Des erreurs en rouge", "error")
        elif not self.game.is_full():
            self._say("Pas encore complet...", "info")
        else:
            self._say("Pas encore...", "error")

    def _back(self) -> None:
        from games.menu.scene import MenuScene  # local import avoids circular import

        self.app.change_scene(MenuScene())

    # -- game loop ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        self.sidebar.handle_event(event)
        self.board.handle_event(event)

    def update(self, dt: float) -> None:
        if not self.solved:
            self.elapsed += dt

    def draw(self, screen: pygame.Surface) -> None:
        stats = self.game.statistics()
        progress = 1 - stats.number_none / (self.size * self.size)
        minutes, seconds = divmod(int(self.elapsed), 60)
        self.sidebar.draw(
            screen, f"Puzzle logique · {self.size}×{self.size}",
            [Stat("Temps", f"{minutes:02d}:{seconds:02d}"), Stat("Rempli", f"{progress:.0%}", progress)],
            self.message, self.message_kind,
        )
        state = BoardState(self.game, self.game.triplet_cells(), self.game.broken_hints(),
                           self.solved, self.elapsed)
        self.board.draw(screen, state)
