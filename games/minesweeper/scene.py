"""MinesweeperScene: the controller wiring model and views. Only it mutates the model."""
from __future__ import annotations

import logging

import pygame

from engine import constants as sc
from engine.scene import Scene
from engine.sidebar import Action, Sidebar, Stat
from games.icons import render_icon

from . import constants as k
from .ai import MinesweeperSolver
from .game import Gameplay
from .models import Difficulty, Move, Status
from .panels import BoardPanel

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
        self._say(_START_MESSAGE)

        self.sidebar = Sidebar(
            sc.SCREEN_HEIGHT, "Démineur", k.ACCENT,
            [Action("Nouvelle partie", self._new_game, "new"),
             Action("Niveau", self._next_difficulty, "level", value=difficulty.label),
             Action("Indice", self._show_hint, "hint", primary=True),
             Action("Pilote IA", self._toggle_ai, "ai", value="OFF"),
             Action("Retour au menu", self._back, "back")],
            icon=render_icon("Démineur", 44, k.ACCENT),
            sections=(("Contrôles", (("Clic G", "révéler (sur un chiffre : autour)"),
                                     ("Clic D", "poser un drapeau"))),),
        )
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
        self._say("IA aux commandes" if self.ai_enabled else _START_MESSAGE)

    def _say(self, message: str, kind: str = "info") -> None:
        self.message, self.message_kind = message, kind

    def _set_ai(self, enabled: bool) -> None:
        self.ai_enabled = enabled
        self.sidebar.set_value(3, "ON" if enabled else "OFF", on=enabled)

    def _next_difficulty(self) -> None:
        difficulty = self.game.difficulty.next()
        self.game.reset(difficulty)
        self.sidebar.set_value(1, difficulty.label)
        self._build_board()
        self._new_game()

    def _show_hint(self) -> None:
        self.hint = self.solver.next_move(self.game)
        if self.hint is None:
            return
        if not self.hint.certain:
            self._say(f"Pas de coup sûr : {self.hint.risk:.0%} de risque")
        elif self.hint.flag:
            self._say("Cette case est une mine", "error")
        else:
            self._say("Cette case est sûre", "success")

    def _toggle_ai(self) -> None:
        self._set_ai(not self.ai_enabled)
        self.ai_timer = 0.0
        self.hint = None
        if not self.game.is_over():
            self._say("IA aux commandes" if self.ai_enabled else "À toi de jouer")

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
            self._say(f"Gagné en {minutes:02d}:{seconds:02d} !", "success")
        elif self.game.status is Status.LOST:
            self._say("Boum ! Perdu...", "error")

    # -- game loop -------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        self.sidebar.handle_event(event)
        if event.type != pygame.MOUSEBUTTONDOWN or event.button not in (1, 3):
            return
        coord = self.board.cell_at(event.pos)
        if coord is None or self.game.is_over():
            return
        if self.ai_enabled:  # a click on the board means the human takes control back
            self._set_ai(False)
        if self.game.status is not Status.READY:
            self._say("À toi de jouer")
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
        stats = self.game.statistics()
        minutes, seconds = divmod(int(self.elapsed), 60)
        d = self.game.difficulty
        self.sidebar.draw(
            screen, f"Logique · {d.cols}×{d.rows}",
            [Stat("Mines", str(stats.mines_left)), Stat("Temps", f"{minutes:02d}:{seconds:02d}"),
             Stat("Dégagé", f"{stats.revealed / stats.safe_total:.0%}", stats.revealed / stats.safe_total)],
            self.message, self.message_kind,
        )
        self.board.draw(screen, self.game, self.hint)
