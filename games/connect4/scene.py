"""Connect4Scene: the controller wiring model, views and AI. Only it mutates the model."""
from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor

import pygame

from engine import constants as sc
from engine.scene import Scene
from engine.sidebar import Action, Sidebar, Stat
from games.icons import render_icon

from . import constants as k
from .ai import MinimaxAgent
from .game import COLS, Gameplay
from .models import Level, Mode, Piece, Score
from .panels import BoardPanel, Falling

log = logging.getLogger(__name__)

_COLUMN_KEYS = {getattr(pygame, f"K_{i + 1}"): i for i in range(COLS)}
_COLUMN_KEYS.update({getattr(pygame, f"K_KP{i + 1}"): i for i in range(COLS)})


class Connect4Scene(Scene):
    def __init__(self) -> None:
        self.mode = Mode.VS_AI
        self.level = Level.MEDIUM
        self.human = Piece.RED          # in vs-AI mode the human is always red
        self.starter = Piece.RED        # alternates every game
        self.game = Gameplay(self.starter)
        self.score = Score()
        self.falling: Falling | None = None
        self.time = 0.0
        # The AI searches in a worker thread so the animation never freezes.
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future: Future[int] | None = None
        self.think_time = 0.0

        self.sidebar = Sidebar(
            sc.SCREEN_HEIGHT, "Puissance 4", k.ACCENT,
            [Action("Nouvelle partie", self._new_game, "new"),
             Action("Mode", self._next_mode, "ai", value=self.mode.value, value_on=True),
             Action("Niveau", self._next_level, "level", value=self.level.label),
             Action("Annuler", self._undo, "undo"),
             Action("Retour au menu", self._back, "back")],
            icon=render_icon("Puissance 4", 44, k.ACCENT),
            sections=(("Contrôles", (("Clic", "lâcher un jeton dans la colonne"),
                                     ("1 - 7", "jouer au clavier"))),),
        )
        self.board = BoardPanel(pygame.Rect(k.BOARD_X, 0, k.BOARD_WIDTH, sc.SCREEN_HEIGHT))
        self._refresh_message()

    # -- buttons -------------------------------------------------------------------------

    def _new_game(self) -> None:
        self.starter = self.starter.other()
        self._restart()

    def _restart(self) -> None:
        self.future = None  # a search still running is simply ignored
        self.falling = None
        self.game.reset(self.starter)
        self._refresh_message()

    def _next_mode(self) -> None:
        self.mode = self.mode.next()
        self.sidebar.set_value(1, self.mode.value, on=True)
        self.score = Score()
        self.starter = Piece.RED
        self._restart()

    def _next_level(self) -> None:
        self.level = self.level.next()
        self.sidebar.set_value(2, self.level.label)

    def _undo(self) -> None:
        if self.falling is not None or not self.game.history:
            return
        self.future = None
        if self.game.is_over():
            self._count_result(-1)
        self.game.undo()
        # Against the AI, rewind to the human's turn (undo the AI's reply too).
        while self.mode is Mode.VS_AI and self.game.history and self.game.turn is not self.human:
            self.game.undo()
        self._refresh_message()

    def _back(self) -> None:
        from games.menu.scene import MenuScene  # local import avoids circular import

        self.executor.shutdown(wait=False, cancel_futures=True)
        self.app.change_scene(MenuScene())

    # -- moves ---------------------------------------------------------------------------

    def _human_can_play(self) -> bool:
        if self.falling is not None or self.future is not None or self.game.is_over():
            return False
        return self.mode is Mode.TWO_PLAYERS or self.game.turn is self.human

    def _ai_to_move(self) -> bool:
        return self.mode is Mode.VS_AI and not self.game.is_over() and self.game.turn is not self.human

    def _play(self, col: int) -> None:
        row = self.game.play(col)
        self.falling = Falling(col, row, self.board.preview_y)

    def _after_drop(self) -> None:
        if self.game.is_over():
            self._count_result(+1)
            log.info("game over: winner=%s", self.game.winner.label or "draw")
        self._refresh_message()

    def _count_result(self, sign: int) -> None:
        if self.game.winner is Piece.RED:
            self.score.red += sign
        elif self.game.winner is Piece.YELLOW:
            self.score.yellow += sign
        else:
            self.score.draws += sign

    def _refresh_message(self) -> None:
        g = self.game
        vs_ai = self.mode is Mode.VS_AI
        if g.winner is not Piece.NONE:
            if vs_ai:
                won = g.winner is self.human
                self.message, self.kind = ("Tu as gagné !", "success") if won else ("L'IA a gagné...", "error")
            else:
                self.message, self.kind = f"{g.winner.label} gagne !", "success"
        elif g.is_draw:
            self.message, self.kind = "Match nul", "info"
        elif vs_ai:
            self.message, self.kind = ("À toi de jouer", "info") if g.turn is self.human else ("L'IA réfléchit", "info")
        else:
            self.message, self.kind = f"Au tour de {g.turn.label}", "info"

    # -- game loop -----------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        self.sidebar.handle_event(event)
        col = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            col = self.board.column_at(event.pos)
        elif event.type == pygame.KEYDOWN:
            col = _COLUMN_KEYS.get(event.key)
        if col is not None and self._human_can_play() and self.game.can_play(col):
            self._play(col)

    def update(self, dt: float) -> None:
        self.time += dt
        if self.falling is not None:
            self._animate_drop(dt)
        elif self.future is not None:
            self.think_time += dt
            if self.future.done() and self.think_time >= k.AI_MIN_THINK:
                col = self.future.result()
                self.future = None
                self._play(col)
        elif self._ai_to_move():
            agent = MinimaxAgent(self.level.depth)
            self.future = self.executor.submit(agent.choose, self.game.copy())
            self.think_time = 0.0
            self._refresh_message()

    def _animate_drop(self, dt: float) -> None:
        f = self.falling
        f.vy += k.GRAVITY * dt
        f.y += f.vy * dt
        _, target = self.board.slot_center(f.col, f.row)
        if f.y >= target:
            f.y = target
            if not f.bounced and f.vy > 300:   # one small bounce, then rest
                f.vy = -f.vy * k.BOUNCE
                f.bounced = True
            else:
                self.falling = None
                self._after_drop()

    def draw(self, screen: pygame.Surface) -> None:
        vs_ai = self.mode is Mode.VS_AI
        labels = ("Toi", "IA") if vs_ai else ("Rouge", "Jaune")
        message = self.message
        if self.future is not None:  # animated "..." while the AI searches
            message += "." * (1 + int(self.time * 3) % 3)
        self.sidebar.draw(
            screen, "Aligne 4 jetons",
            [Stat(labels[0], str(self.score.red)), Stat(labels[1], str(self.score.yellow)),
             Stat("Nuls", str(self.score.draws))],
            message, self.kind,
        )
        preview = None
        if self._human_can_play():
            col = self.board.column_at(pygame.mouse.get_pos())
            if col is not None and self.game.can_play(col):
                preview = (col, self.game.turn)
        self.board.draw(screen, self.game, self.falling, preview, self.falling is None, self.time)
