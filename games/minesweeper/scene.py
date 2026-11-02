"""MinesweeperScene: the controller wiring model and views. Only it mutates the model."""
from __future__ import annotations

import logging

import pygame

from engine import constants as sc
from engine.scene import Scene

from . import constants as k
from .ai import MinesweeperSolver
from .game import Gameplay
from .models import Difficulty, Move, Status
from .panels import BoardPanel, NavigatorPanel

log = logging.getLogger(__name__)

_START_MESSAGE = "Clique une case pour commencer"


class MinesweeperScene(Scene):
    def __init__(self, difficulty: Difficulty = Difficulty.EASY) -> None:
        self.game = Gameplay(difficulty)
        self.solver = MinesweeperSolver()
        self.ai_enabled = False
        self.ai_timer = 0.0  # seconds accumulated toward the AI's next move
        self.hint: Move | None = None
        self.elapsed = 0.0
        self.message = _START_MESSAGE

        nav_rect = pygame.Rect(0, 0, k.NAV_WIDTH, sc.SCREEN_HEIGHT)
        self.nav = NavigatorPanel(nav_rect, self._new_game, self._next_difficulty,
                                  self._show_hint, self._toggle_ai, self._back)
        self.nav.set_difficulty_label(difficulty.label)
        self._build_board()

    def _build_board(self) -> None:
        # The board's cell size depends on the grid, so it's rebuilt on difficulty change.
        board_rect = pygame.Rect(k.BOARD_X, 0, k.BOARD_WIDTH, sc.SCREEN_HEIGHT)
        self.board = BoardPanel(board_rect, self.game.width, self.game.height)

    # -- button callbacks ------------------------------------------------------

    def _new_game(self) -> None:
        self.game.reset()
        self.elapsed = 0.0
        self.ai_timer = 0.0
        self.hint = None
        self.message = "IA aux commandes" if self.ai_enabled else _START_MESSAGE

    def _next_difficulty(self) -> None:
        difficulty = self.game.difficulty.next()
        self.game.reset(difficulty)
        self.nav.set_difficulty_label(difficulty.label)
        self._build_board()
        self._new_game()

    def _show_hint(self) -> None:
        self.hint = self.solver.next_move(self.game)
        if self.hint is None:
            return
        if not self.hint.certain:
            self.message = f"Aucun coup sûr ({self.hint.risk:.0%} de risque)"
        elif self.hint.flag:
            self.message = "Cette case est une mine"
        else:
            self.message = "Cette case est sûre"

    def _toggle_ai(self) -> None:
        self.ai_enabled = not self.ai_enabled
        self.nav.set_ai_label(self.ai_enabled)
        self.ai_timer = 0.0
        self.hint = None
        if not self.game.is_over():
            self.message = "IA aux commandes" if self.ai_enabled else "À toi de jouer"

    def _back(self) -> None:
        from games.menu.scene import MenuScene  # local import avoids circular import

        self.app.change_scene(MenuScene())

    # -- moves -----------------------------------------------------------------

    def _play(self, move: Move) -> None:
        """Apply a move, whoever made it (human click or AI)."""
        if move.flag:
            self.game.toggle_flag(move.coord)
        elif self.game.cells[move.coord].revealed:
            self.game.chord(move.coord)
        else:
            self.game.reveal(move.coord)
        self.hint = None
        if self.game.status is Status.WON:
            minutes, seconds = divmod(int(self.elapsed), 60)
            self.message = f"Gagné en {minutes:02d}:{seconds:02d} !"
        elif self.game.status is Status.LOST:
            self.message = "Boum ! Perdu..."

    # -- game loop -------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        self.nav.handle_event(event)
        if event.type != pygame.MOUSEBUTTONDOWN or event.button not in (1, 3):
            return
        coord = self.board.cell_at(event.pos)
        if coord is None or self.game.is_over():
            return
        if self.ai_enabled:  # a click on the board means the human takes control back
            self.ai_enabled = False
            self.nav.set_ai_label(False)
        if self.game.status is not Status.READY:
            self.message = "À toi de jouer"
        # Right click flags; left click reveals (or chords, on a revealed number).
        self._play(Move(coord, flag=event.button == 3, certain=False))

    def update(self, dt: float) -> None:
        if self.game.status is Status.PLAYING:
            self.elapsed += dt
        if not self.ai_enabled or self.game.is_over():
            return
        self.ai_timer += dt
        if self.ai_timer >= k.AI_INTERVAL:
            self.ai_timer = 0.0
            move = self.solver.next_move(self.game)
            if move is not None:
                self._play(move)

    def draw(self, screen: pygame.Surface) -> None:
        self.nav.draw(screen, self.game.statistics(), self.elapsed, self.message)
        self.board.draw(screen, self.game, self.hint)
