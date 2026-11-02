"""SnakeScene: the controller wiring model and views. Only it mutates the model."""
from __future__ import annotations

import logging

import pygame

from engine import constants as sc
from engine.scene import Scene
from engine.sidebar import Action, Sidebar, Stat
from games.icons import render_icon

from . import constants as k
from .ai import HamiltonianAgent
from .game import Gameplay
from .models import Direction
from .panels import BoardPanel

log = logging.getLogger(__name__)

# Keyboard -> Direction. Arrows, WASD and ZQSD (AZERTY) all work.
_KEY_DIRECTIONS = {
    pygame.K_UP: Direction.UP,
    pygame.K_DOWN: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT,
    pygame.K_w: Direction.UP,
    pygame.K_s: Direction.DOWN,
    pygame.K_a: Direction.LEFT,
    pygame.K_d: Direction.RIGHT,
    pygame.K_z: Direction.UP,
    pygame.K_q: Direction.LEFT,
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
        self._say("Flèches ou ZQSD pour jouer")

        self.sidebar = Sidebar(
            sc.SCREEN_HEIGHT, "Snake", k.ACCENT,
            [Action("Nouvelle partie", self._new_game, "new"),
             Action("Pilote IA", self._toggle_ai, "ai", value="OFF"),
             Action("Retour au menu", self._back, "back")],
            icon=render_icon("Snake", 44, k.ACCENT),
            sections=(
                ("Contrôles", (("Flèches", "ou ZQSD : diriger"),
                               (None, "Mange, grandis, évite les murs"))),
                ("IA", ((None, "Suit un cycle qui passe partout"),
                        (None, "Ne prend un raccourci que s'il est sûr"))),
            ),
        )
        board_rect = pygame.Rect(k.BOARD_X, 0, k.BOARD_WIDTH, sc.SCREEN_HEIGHT)
        self.board = BoardPanel(board_rect, cols, rows)

    def _new_game(self) -> None:
        self.game.reset()
        self.elapsed = 0.0
        self.move_timer = 0.0
        self.restart_timer = 0.0
        self._say("IA aux commandes" if self.ai_enabled else "Flèches ou ZQSD pour jouer")

    def _say(self, message: str, kind: str = "info") -> None:
        self.message, self.message_kind = message, kind

    def _set_ai(self, enabled: bool) -> None:
        self.ai_enabled = enabled
        self.sidebar.set_value(1, "ON" if enabled else "OFF", on=enabled)

    def _toggle_ai(self) -> None:
        self._set_ai(not self.ai_enabled)
        self.restart_timer = 0.0
        self._say("IA aux commandes" if self.ai_enabled else "À toi de jouer")

    def _back(self) -> None:
        from games.menu.scene import MenuScene  # local import avoids circular import

        self.app.change_scene(MenuScene())

    def _move_interval(self) -> float:
        # Speeds up as the score grows, clamped so it never gets impossibly fast.
        return max(k.MIN_INTERVAL, k.MOVE_INTERVAL - self.game.score * k.SPEEDUP_PER_POINT)

    # -- game loop ------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        self.sidebar.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key in _KEY_DIRECTIONS:
            if self.ai_enabled:  # a keypress means the human takes control back
                self._set_ai(False)
                self._say("À toi de jouer")
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
                self._say(f"Perdu ! Score : {self.game.score}", "error")
                break

    def draw(self, screen: pygame.Surface) -> None:
        stats = self.game.statistics()
        minutes, seconds = divmod(int(self.elapsed), 60)
        self.sidebar.draw(
            screen, f"Arcade · {self.cols}×{self.rows}",
            [Stat("Score", str(stats.score)), Stat("Record", str(stats.best)),
             Stat("Temps", f"{minutes:02d}:{seconds:02d}")],
            self.message, self.message_kind,
        )
        self.board.draw(screen, self.game.snake, self.game.food)
